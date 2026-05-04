"""
FastAPI application exposing semantic search and grounded answers.

Endpoints:
  GET  /         — welcome
  GET  /health   — Qdrant connectivity check
  POST /search   — semantic search; returns top-K matching chunks with scores
  POST /ask      — grounded structured answer via the configured LLM
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from app.answer import SupportAnswer, answer
from app.config import settings
from app.llm import llm_label
from app.retriever import get_embeddings, get_vector_store, search_by_vector


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
    embed_ms: float
    search_ms: float
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


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        examples=["A customer wants a refund after 45 days. What should the support rep say?"],
    )


class AskResponse(BaseModel):
    question: str
    answer: SupportAnswer
    embed_ms: float
    search_ms: float
    generate_ms: float
    latency_ms: float
    llm: str


@app.get("/", tags=["Meta"])
def root():
    return {
        "name": "Nirvana Cloud Support Search",
        "docs": "/docs",
        "search": "POST /search",
        "ask": "POST /ask",
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
    try:
        t0 = time.perf_counter()
        vec = get_embeddings().embed_query(request.query)
        embed_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        hits = search_by_vector(vec, request.top_k)
        search_ms = (time.perf_counter() - t1) * 1000
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        embed_ms=round(embed_ms, 2),
        search_ms=round(search_ms, 2),
        latency_ms=round(embed_ms + search_ms, 2),
        embedding_model=settings.embedding_model,
    )


@app.post("/ask", response_model=AskResponse, tags=["Ask"])
def ask(request: AskRequest):
    """
    Grounded structured answer.

    Retrieves top-K chunks from Qdrant, sends them with the question to the
    configured LLM (ollama by default, OpenAI when LLM_PROVIDER=openai), and
    returns a SupportAnswer (summary, recommended response, citations,
    escalation flag).
    """
    try:
        result, latency = answer(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return AskResponse(
        question=request.question,
        answer=result,
        embed_ms=round(latency.embed_ms, 2),
        search_ms=round(latency.search_ms, 2),
        generate_ms=round(latency.generate_ms, 2),
        latency_ms=round(latency.total_ms, 2),
        llm=llm_label(),
    )
