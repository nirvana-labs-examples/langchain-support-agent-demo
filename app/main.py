"""
FastAPI application exposing the support agent via a REST API.

Endpoints:
  GET  /        — welcome
  GET  /health  — Qdrant connectivity check
  POST /ask     — ask the agent a question
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from app.config import settings
from app.agent import run_agent


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        example="What is our refund policy for annual enterprise customers?",
    )


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    latency_ms: float
    model: str


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    model: str
    collection: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the cached vector store so the first request isn't slow
    from app.retriever import get_vector_store
    try:
        get_vector_store()
        print("Retriever warmed up successfully.")
    except Exception as e:
        print(f"Warning: could not warm up retriever: {e}")
    yield


app = FastAPI(
    title="Nirvana Cloud Support Agent",
    description=(
        "AI-powered customer support agent backed by LangChain, Qdrant, and OpenAI. "
        "Demonstrates infrastructure-heavy AI agent workloads on Nirvana Cloud."
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
        "name": "Nirvana Cloud Support Agent",
        "docs": "/docs",
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
        model=settings.agent_model,
        collection=settings.qdrant_collection_name,
    )


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
def ask(request: AskRequest):
    """
    Ask the support agent a question.

    The agent searches the knowledge base and returns a grounded answer with
    source citations. Response time includes: query embedding + vector retrieval
    + LLM generation.
    """
    start = time.perf_counter()
    try:
        result = run_agent(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    latency_ms = (time.perf_counter() - start) * 1000

    return AskResponse(
        question=request.question,
        answer=result["answer"],
        sources=result["sources"],
        latency_ms=round(latency_ms, 2),
        model=settings.agent_model,
    )
