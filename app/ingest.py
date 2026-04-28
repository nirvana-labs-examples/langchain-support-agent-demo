"""
Ingest pipeline: load documents → chunk → embed → store in Qdrant.

This is where infrastructure matters most: embedding thousands of documents
and storing vectors requires fast CPUs, ample RAM, and low-latency attached
block storage (where Qdrant keeps its HNSW index on disk).
"""

import sys
from pathlib import Path
from typing import List

import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from app.config import settings

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"


def load_markdown_files() -> List[Document]:
    docs = []
    for path in sorted(DATA_DIR.glob("**/*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(
            page_content=text,
            metadata={
                "source": str(path.relative_to(DATA_DIR)),
                "file_type": "markdown",
                "filename": path.name,
            },
        ))
        console.print(f"  [green]Loaded[/green] {path.relative_to(DATA_DIR)}")
    return docs


def load_csv_tickets() -> List[Document]:
    csv_path = DATA_DIR / "sample_tickets.csv"
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        content = (
            f"Support Ticket {row['ticket_id']}\n"
            f"Date: {row['date']}\n"
            f"Customer Tier: {row['customer_tier']}\n"
            f"Subject: {row['subject']}\n"
            f"Description: {row['description']}\n"
            f"Status: {row['status']}\n"
            f"Resolution: {row['resolution']}\n"
        )
        docs.append(Document(
            page_content=content,
            metadata={
                "source": "sample_tickets.csv",
                "file_type": "csv",
                "ticket_id": row["ticket_id"],
                "customer_tier": row["customer_tier"],
                "status": row["status"],
            },
        ))
    console.print(f"  [green]Loaded[/green] {len(docs)} tickets from sample_tickets.csv")
    return docs


def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    console.print(
        f"  [cyan]Split into[/cyan] {len(chunks)} chunks "
        f"(size={settings.chunk_size}, overlap={settings.chunk_overlap})"
    )
    return chunks


def get_qdrant_client() -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(client: QdrantClient, vector_size: int = 1536) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection_name not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        console.print(f"  [yellow]Created collection[/yellow] '{settings.qdrant_collection_name}'")
    else:
        console.print(f"  [blue]Collection[/blue] '{settings.qdrant_collection_name}' already exists")


def ingest(recreate: bool = False) -> int:
    """
    Full ingest pipeline. Returns the number of chunks stored.

    Args:
        recreate: If True, deletes and recreates the collection before ingesting.
    """
    console.rule("[bold magenta]Nirvana Support Agent — Ingest Pipeline[/bold magenta]")

    console.print("\n[bold]Step 1: Loading documents[/bold]")
    docs = load_markdown_files() + load_csv_tickets()
    console.print(f"  Total documents loaded: [bold]{len(docs)}[/bold]")

    console.print("\n[bold]Step 2: Chunking[/bold]")
    chunks = chunk_documents(docs)

    console.print("\n[bold]Step 3: Connecting to Qdrant[/bold]")
    client = get_qdrant_client()
    console.print(f"  Connected to Qdrant at [cyan]{settings.qdrant_host}:{settings.qdrant_port}[/cyan]")

    if recreate:
        existing = [c.name for c in client.get_collections().collections]
        if settings.qdrant_collection_name in existing:
            client.delete_collection(settings.qdrant_collection_name)
            console.print(f"  [red]Deleted[/red] existing collection '{settings.qdrant_collection_name}'")

    # text-embedding-3-small produces 1536-dimensional vectors
    ensure_collection(client, vector_size=1536)

    console.print("\n[bold]Step 4: Embedding and storing vectors[/bold]")
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )

    qdrant_url = settings.qdrant_url or f"http://{settings.qdrant_host}:{settings.qdrant_port}"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding and indexing chunks...", total=len(chunks))
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=settings.qdrant_collection_name,
            url=qdrant_url,
            api_key=settings.qdrant_api_key,
            force_recreate=False,
        )
        progress.update(task, completed=len(chunks))

    console.print(f"\n[bold green]Ingest complete![/bold green] {len(chunks)} chunks stored.")
    console.rule()
    return len(chunks)


if __name__ == "__main__":
    recreate = "--recreate" in sys.argv
    ingest(recreate=recreate)
