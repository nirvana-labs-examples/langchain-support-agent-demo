"""
Pre-compute embeddings for a dataset and cache them to disk.

Run this once before benchmarks.ingest to eliminate the CPU-bound embedding
phase from the write benchmark, so it measures only Qdrant I/O.

Cache files are split into ≤48 MB parts so they can be committed to git.

Run:
  python -m benchmarks.precompute           # medium (default)
  python -m benchmarks.precompute small
  python -m benchmarks.precompute large
"""

import sys

import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from rich.console import Console

from app.config import settings
from app.embedding_cache import save_cache
from app.ingest import load_csv_tickets, load_markdown_files

console = Console()


def run_precompute(dataset: str) -> None:
    console.rule(f"[bold magenta]Precompute Embeddings — dataset: {dataset}[/bold magenta]")

    console.print("\n[bold]Loading documents...[/bold]")
    docs = load_markdown_files(dataset) + load_csv_tickets(dataset)
    console.print(f"  Total: [cyan]{len(docs)}[/cyan] documents")

    console.print("\n[dim]Chunking...[/dim]")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(docs)
    console.print(f"  -> [cyan]{len(chunks)}[/cyan] chunks")

    console.print("\n[dim]Loading embedding model...[/dim]")
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    console.print(f"  Loaded [cyan]{settings.embedding_model}[/cyan]")

    console.print(f"\nEmbedding [cyan]{len(chunks)}[/cyan] chunks (this is the slow part)...")
    raw_vectors = embeddings.embed_documents([c.page_content for c in chunks])
    console.print(f"  Done — {len(raw_vectors)} vectors ({settings.embedding_dimensions} dims each)")

    payloads: list[dict[str, object]] = [
        {"text": chunk.page_content, **chunk.metadata}
        for chunk in chunks
    ]

    console.print("\nSaving cache...")
    save_cache(dataset, np.array(raw_vectors, dtype=np.float32), payloads)

    console.print(f"\n[bold green]Done![/bold green] Run [bold]python -m benchmarks.ingest {dataset}[/bold] to benchmark.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in ("small", "medium", "large")]
    if args:
        settings.dataset = args[0]  # pyright: ignore[reportAttributeAccessIssue]
    run_precompute(settings.dataset)
