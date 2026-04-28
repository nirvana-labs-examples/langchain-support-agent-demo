"""
Vector retriever: connects to Qdrant and returns relevant document chunks.

Retrieval latency is directly tied to Qdrant's HNSW index performance,
which depends on the speed of the underlying block storage. On Nirvana Cloud
ABS (NVMe), the HNSW scan itself takes <3ms. The dominant latency factor at
this scale is the OpenAI embedding API call (~100-200ms).
"""

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.schema import BaseRetriever

from app.config import settings


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    """
    Return a cached QdrantVectorStore instance.

    lru_cache ensures we reuse the connection across requests,
    avoiding per-request connection overhead.
    """
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
    url = settings.qdrant_url or f"http://{settings.qdrant_host}:{settings.qdrant_port}"
    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=settings.qdrant_collection_name,
        url=url,
        api_key=settings.qdrant_api_key,
    )


def get_retriever() -> BaseRetriever:
    return get_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_top_k},
    )
