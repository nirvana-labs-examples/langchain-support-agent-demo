"""
Vector retriever: connects to self-hosted Qdrant and returns relevant chunks.

The embedding model is loaded once into memory and reused across requests.
At query time:
  1. Embed the user's question on local CPU (~30ms)
  2. Run a cosine-similarity search against Qdrant's HNSW index (~3ms on NVMe)

No external APIs. No network round-trips. The full retrieval path runs on
the Nirvana VM and is bound by CPU + storage I/O.
"""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.schema import BaseRetriever

from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    """
    Return a cached QdrantVectorStore. The embedding model and the Qdrant
    connection are both reused across requests via lru_cache.
    """
    url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"
    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        collection_name=settings.qdrant_collection_name,
        url=url,
    )


def get_retriever() -> BaseRetriever:
    return get_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_top_k},
    )
