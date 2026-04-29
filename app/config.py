from typing import ClassVar, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Qdrant (self-hosted via docker-compose.yml)
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_collection_name: str = Field(default="support_docs")

    # Embedding model (HuggingFace, runs locally)
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_dimensions: int = Field(default=384)

    # Chunking
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=64)

    # Retrieval
    retriever_top_k: int = Field(default=5)

    # LLM (used by app.ask / POST /ask)
    llm_provider: Literal["ollama", "openai"] = Field(default="ollama")
    ollama_model: str = Field(default="llama3.2:3b")
    ollama_base_url: str = Field(default="http://localhost:11434")
    openai_model: str = Field(default="gpt-4o-mini")
    openai_api_key: str | None = Field(default=None)


# Module-level singleton — all modules import from here
settings = Settings()
