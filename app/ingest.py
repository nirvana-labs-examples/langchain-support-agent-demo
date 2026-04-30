"""
Ingest pipeline: load documents → chunk → embed (locally) → store in Qdrant.

Everything runs on-box: the embedding model (BGE-small) loads into CPU memory,
chunks are encoded locally, and vectors are written directly to a self-hosted
Qdrant instance. No external API calls, no API keys.
"""

import sys
from pathlib import Path
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from app.config import settings

console = Console()

_REPO_ROOT = Path(__file__).parent.parent


def _data_dir(dataset: str) -> Path:
    return _REPO_ROOT / "data" / dataset


def _collection_name(dataset: str) -> str:
    return f"{settings.qdrant_collection_name}_{dataset}"


def load_markdown_files(dataset: str) -> list[Document]:
    data_dir = _data_dir(dataset)
    docs = []
    for path in sorted(data_dir.glob("**/*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(
            page_content=text,
            metadata={
                "source": str(path.relative_to(data_dir)),
                "file_type": "markdown",
                "filename": path.name,
            },
        ))
    console.print(f"  [green]Loaded[/green] {len(docs)} markdown files")
    return docs


def load_csv_tickets(dataset: str) -> list[Document]:
    data_dir = _data_dir(dataset)
    csv_path = data_dir / "sample_tickets.csv"
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


def chunk_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    console.print(f"  [cyan]Split into[/cyan] {len(chunks)} chunks (size={settings.chunk_size}, overlap={settings.chunk_overlap})")
    return chunks


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(client: QdrantClient, collection_name: str) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        _ = client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        console.print(f"  [yellow]Created collection[/yellow] '{collection_name}'")
    else:
        console.print(f"  [blue]Collection[/blue] '{collection_name}' already exists")


def ingest(dataset: str, recreate: bool = False) -> int:
    """
    Full ingest pipeline for the given dataset. Returns the number of chunks stored.

    Args:
        dataset:  "small" or "medium"
        recreate: If True, drops and recreates the collection before ingesting.
    """
    collection_name = _collection_name(dataset)
    console.rule(f"[bold magenta]Nirvana Support Agent — Ingest Pipeline ({dataset})[/bold magenta]")

    console.print("\n[bold]Step 1: Loading documents[/bold]")
    docs = load_markdown_files(dataset) + load_csv_tickets(dataset)
    console.print(f"  Total documents loaded: [bold]{len(docs)}[/bold]")

    console.print("\n[bold]Step 2: Chunking[/bold]")
    chunks = chunk_documents(docs)

    console.print("\n[bold]Step 3: Loading embedding model[/bold]")
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    console.print(f"  Loaded [cyan]{settings.embedding_model}[/cyan] ({settings.embedding_dimensions} dims)")

    console.print("\n[bold]Step 4: Connecting to Qdrant[/bold]")
    client = get_qdrant_client()
    console.print(f"  Connected to Qdrant at [cyan]{settings.qdrant_host}:{settings.qdrant_port}[/cyan]")

    if recreate:
        existing = [c.name for c in client.get_collections().collections]
        if collection_name in existing:
            _ = client.delete_collection(collection_name)
            console.print(f"  [red]Deleted[/red] existing collection '{collection_name}'")

    ensure_collection(client, collection_name)

    console.print("\n[bold]Step 5: Embedding and storing vectors[/bold]")
    qdrant_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        _ = progress.add_task(f"Embedding and indexing {len(chunks)} chunks...", total=None)
        _ = QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=collection_name,
            url=qdrant_url,
            force_recreate=False,
        )

    console.print(f"\n[bold green]Ingest complete![/bold green] {len(chunks)} chunks stored in '{collection_name}'.")
    console.rule()
    return len(chunks)


def _parse_args() -> tuple[str, bool]:
    args = sys.argv[1:]
    dataset: str = settings.dataset
    recreate = False
    for arg in args:
        if arg in ("small", "medium", "large"):
            dataset = arg
        elif arg == "--recreate":
            recreate = True
    return dataset, recreate


if __name__ == "__main__":
    _dataset, _recreate = _parse_args()
    _ = ingest(dataset=_dataset, recreate=_recreate)
