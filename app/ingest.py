"""
Ingest pipeline: load documents → chunk → embed (locally) → store in Qdrant.

Everything runs on-box: the embedding model (BGE-small) loads into CPU memory,
chunks are encoded locally, and vectors are written directly to a self-hosted
Qdrant instance. No external API calls, no API keys.
"""

import sys
import zipfile
from pathlib import Path
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, HnswConfigDiff, PointStruct, VectorParams
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from app.config import settings
from app.embedding_cache import is_cached, load_cache

console = Console()

_REPO_ROOT = Path(__file__).parent.parent


def _data_dir(dataset: str) -> Path:
    return _REPO_ROOT / "data" / dataset


def ensure_extracted(dataset: str) -> None:
    """Extract data/{dataset}.zip into data/ if the directory doesn't exist yet."""
    data_dir = _data_dir(dataset)
    if data_dir.exists():
        return
    zip_path = _REPO_ROOT / "data" / f"{dataset}.zip"
    if not zip_path.exists():
        raise FileNotFoundError(
            f"Dataset '{dataset}' not found. Expected {data_dir} or {zip_path}. Run 'python -m scripts.generate_dataset {dataset}' to generate it."
        )
    console.print(f"  [dim]Extracting {zip_path.name}...[/dim]")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(_REPO_ROOT / "data")
    console.print(f"  [green]Extracted[/green] {dataset} dataset to {data_dir}")


def _collection_name(dataset: str) -> str:
    return f"{settings.qdrant_collection_name}_{dataset}"


def load_markdown_files(dataset: str) -> list[Document]:
    ensure_extracted(dataset)
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
    ensure_extracted(dataset)
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
                on_disk=settings.qdrant_on_disk,
            ),
            hnsw_config=HnswConfigDiff(on_disk=settings.qdrant_on_disk),
        )
        mode = "on-disk" if settings.qdrant_on_disk else "in-memory"
        console.print(f"  [yellow]Created collection[/yellow] '{collection_name}' ([cyan]{mode}[/cyan])")
    else:
        console.print(f"  [blue]Collection[/blue] '{collection_name}' already exists")


def ingest(dataset: str, recreate: bool = False, nocache: bool = False) -> int:
    """
    Full ingest pipeline for the given dataset. Returns the number of chunks stored.

    If pre-computed embeddings are cached (data/.cache/), load them directly and
    skip extraction, loading, chunking, and embedding entirely. Pass nocache=True
    to force the full pipeline regardless.
    """
    collection_name = _collection_name(dataset)
    console.rule(f"[bold magenta]Nirvana Support Agent — Ingest Pipeline ({dataset})[/bold magenta]")

    console.print("\n[bold]Step 1: Connecting to Qdrant[/bold]")
    client = get_qdrant_client()
    console.print(f"  Connected to Qdrant at [cyan]{settings.qdrant_host}:{settings.qdrant_port}[/cyan]")

    if recreate:
        existing = [c.name for c in client.get_collections().collections]
        if collection_name in existing:
            _ = client.delete_collection(collection_name)
            console.print(f"  [red]Deleted[/red] existing collection '{collection_name}'")

    ensure_collection(client, collection_name)

    if not nocache and is_cached(dataset):
        console.print("\n[bold]Step 2: Loading pre-computed embeddings from cache[/bold]")
        vectors, payloads = load_cache(dataset)
        num_chunks = len(vectors)
        console.print(f"  Loaded [cyan]{num_chunks}[/cyan] vectors from cache")

        console.print("\n[bold]Step 3: Storing vectors[/bold]")
        points = [
            PointStruct(id=i, vector=vec, payload=payload)
            for i, (vec, payload) in enumerate(zip(vectors, payloads))
        ]
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Upserting {num_chunks} vectors...", total=None)
            for batch_start in range(0, len(points), 512):
                _ = client.upsert(
                    collection_name=collection_name,
                    points=points[batch_start : batch_start + 512],
                    wait=True,
                )
            progress.update(task, description=f"Upserted {num_chunks} vectors")
    else:
        if nocache:
            console.print("\n[dim]--nocache: skipping cache, running full pipeline[/dim]")

        console.print("\n[bold]Step 2: Loading documents[/bold]")
        docs = load_markdown_files(dataset) + load_csv_tickets(dataset)
        console.print(f"  Total documents loaded: [bold]{len(docs)}[/bold]")

        console.print("\n[bold]Step 3: Chunking[/bold]")
        chunks = chunk_documents(docs)
        num_chunks = len(chunks)

        console.print("\n[bold]Step 4: Loading embedding model[/bold]")
        embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        console.print(f"  Loaded [cyan]{settings.embedding_model}[/cyan] ({settings.embedding_dimensions} dims)")

        console.print("\n[bold]Step 5: Embedding and storing vectors[/bold]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Embedding {num_chunks} chunks...", total=None)
            raw_vectors = embeddings.embed_documents([c.page_content for c in chunks])
            progress.update(task, description=f"Upserting {num_chunks} vectors...")
            payloads: list[dict[str, object]] = [
                {"text": chunk.page_content, **chunk.metadata}
                for chunk in chunks
            ]
            points = [
                PointStruct(id=i, vector=vec, payload=payload)
                for i, (vec, payload) in enumerate(zip(raw_vectors, payloads))
            ]
            for batch_start in range(0, len(points), 512):
                _ = client.upsert(
                    collection_name=collection_name,
                    points=points[batch_start : batch_start + 512],
                    wait=True,
                )
            progress.update(task, description=f"Upserted {num_chunks} vectors")

    console.print(f"\n[bold green]Ingest complete![/bold green] {num_chunks} chunks stored in '{collection_name}'.")
    console.rule()
    return num_chunks


def _parse_args() -> tuple[str, bool, bool]:
    args = sys.argv[1:]
    dataset: str = settings.dataset
    recreate = False
    nocache = False
    for arg in args:
        if arg in ("small", "medium", "large"):
            dataset = arg
        elif arg == "--recreate":
            recreate = True
        elif arg == "--nocache":
            nocache = True
    return dataset, recreate, nocache


if __name__ == "__main__":
    _dataset, _recreate, _nocache = _parse_args()
    _ = ingest(dataset=_dataset, recreate=_recreate, nocache=_nocache)
