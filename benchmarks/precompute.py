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

import json
import sys
from pathlib import Path

import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from rich.console import Console

from app.config import settings
from app.ingest import load_csv_tickets, load_markdown_files

console = Console()

_CACHE_DIR = Path(__file__).parent / ".cache"
_MAX_PART_BYTES = 48 * 1024 * 1024  # 48 MB — safely under GitHub's 50 MB limit


def cache_key(dataset: str) -> dict[str, object]:
    return {
        "dataset": dataset,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }


def _key_path(dataset: str) -> Path:
    return _CACHE_DIR / f"{dataset}_key.json"


def _vector_parts(dataset: str) -> list[Path]:
    return sorted(_CACHE_DIR.glob(f"{dataset}_vectors.part*.npy"))


def _payload_parts(dataset: str) -> list[Path]:
    return sorted(_CACHE_DIR.glob(f"{dataset}_payloads.part*.json"))


def is_cached(dataset: str) -> bool:
    key_path = _key_path(dataset)
    if not key_path.exists() or not _vector_parts(dataset):
        return False
    stored_key: object = json.loads(key_path.read_text())  # pyright: ignore[reportAny]
    return stored_key == cache_key(dataset)


def load_cache(dataset: str) -> tuple[list[list[float]], list[dict[str, object]]]:
    vector_parts = _vector_parts(dataset)
    payload_parts = _payload_parts(dataset)
    vectors: list[list[float]] = np.concatenate(  # pyright: ignore[reportAny]
        [np.load(p) for p in vector_parts]
    ).tolist()
    payloads: list[dict[str, object]] = []
    for p in payload_parts:
        chunk: list[dict[str, object]] = json.loads(p.read_text())  # pyright: ignore[reportAny]
        payloads.extend(chunk)
    return vectors, payloads


def save_cache(dataset: str, vectors: np.ndarray, payloads: list[dict[str, object]]) -> None:  # pyright: ignore[reportMissingTypeArgument,reportUnknownParameterType]
    _CACHE_DIR.mkdir(exist_ok=True)

    # Remove any existing parts for this dataset
    for old in list(_CACHE_DIR.glob(f"{dataset}_vectors.part*.npy")) + \
               list(_CACHE_DIR.glob(f"{dataset}_payloads.part*.json")):
        old.unlink()

    dims = vectors.shape[1]
    rows_per_part = max(1, _MAX_PART_BYTES // (dims * 4))
    num_parts = (len(vectors) + rows_per_part - 1) // rows_per_part

    for i, start in enumerate(range(0, len(vectors), rows_per_part)):
        end = min(start + rows_per_part, len(vectors))
        np.save(_CACHE_DIR / f"{dataset}_vectors.part{i:02d}.npy", vectors[start:end])
        _ = (_CACHE_DIR / f"{dataset}_payloads.part{i:02d}.json").write_text(
            json.dumps(payloads[start:end])
        )

    _ = _key_path(dataset).write_text(json.dumps(cache_key(dataset)))

    total_mb = vectors.nbytes / 1_000_000
    console.print(f"  Saved in [cyan]{num_parts}[/cyan] part(s) ({total_mb:.1f} MB total)")


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
