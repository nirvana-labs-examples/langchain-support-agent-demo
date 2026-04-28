from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")

    # Qdrant
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_collection_name: str = Field(default="support_docs")
    qdrant_api_key: str | None = Field(default=None)
    qdrant_url: str | None = Field(default=None)  # For Qdrant Cloud

    # LLM / Embedding
    agent_model: str = Field(default="gpt-4o-mini")
    embedding_model: str = Field(default="text-embedding-3-small")

    # Chunking
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=64)

    # Retrieval
    retriever_top_k: int = Field(default=5)


# Module-level singleton — all modules import from here
settings = Settings()
