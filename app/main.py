"""
FastAPI application exposing semantic search over the support knowledge base.

Endpoints:
  GET  /         — welcome
  GET  /health   — Qdrant connectivity check
  POST /search   — semantic search; returns top-K matching chunks with scores
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from app.config import settings
from app.retriever import get_vector_store


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        examples=["What is the refund policy for enterprise customers?"],
    )
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    text: str
    source: str
    score: float
    metadata: dict[str, object]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    latency_ms: float
    embedding_model: str


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    embedding_model: str
    collection: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        _ = get_vector_store()
        print("Embedding model and Qdrant connection warmed up.")
    except Exception as e:
        print(f"Warning: could not warm up retriever: {e}")
    yield


app = FastAPI(
    title="Nirvana Cloud Support Search",
    description=(
        "Semantic search over a customer-support knowledge base. "
        "Local embedding model + self-hosted Qdrant. No external APIs."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Meta"])
def root():
    return {
        "name": "Nirvana Cloud Support Search",
        "docs": "/docs",
        "search": "POST /search",
        "health": "GET /health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Meta"])
def health():
    """Check that Qdrant is reachable and the collection exists."""
    try:
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        collections = [c.name for c in client.get_collections().collections]
        qdrant_status = (
            "ok" if settings.qdrant_collection_name in collections else "collection_missing"
        )
    except Exception as e:
        qdrant_status = f"error: {e}"

    return HealthResponse(
        status="ok" if qdrant_status == "ok" else "degraded",
        qdrant=qdrant_status,
        embedding_model=settings.embedding_model,
        collection=settings.qdrant_collection_name,
    )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
def search(request: SearchRequest):
    """
    Semantic search over the support knowledge base.

    Returns the top-K most relevant chunks with similarity scores and source
    metadata. Latency includes local query embedding + Qdrant HNSW search.
    """
    start = time.perf_counter()
    try:
        vector_store = get_vector_store()
        hits = vector_store.similarity_search_with_score(
            query=request.query,
            k=request.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    latency_ms = (time.perf_counter() - start) * 1000

    results = [
        SearchResult(
            text=doc.page_content,
            source=doc.metadata.get("source", "unknown"),
            score=round(float(score), 4),
            metadata={k: v for k, v in doc.metadata.items() if k != "source"},
        )
        for doc, score in hits
    ]

    return SearchResponse(
        query=request.query,
        results=results,
        latency_ms=round(latency_ms, 2),
        embedding_model=settings.embedding_model,
    )
