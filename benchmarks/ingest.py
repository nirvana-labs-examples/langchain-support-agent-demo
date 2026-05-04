"""
Benchmark: document ingest throughput.

Measures the Qdrant write phase only (disk I/O bound — HNSW index construction).
Pre-computed embeddings are loaded from data/.cache/ so CPU embedding time is
excluded and numbers reflect pure storage performance.

Run:
  python -m benchmarks.ingest              # medium (default)
  python -m benchmarks.ingest small
  python -m benchmarks.ingest large
"""

import statistics
import sys
import time

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from rich.console import Console
from rich.table import Table

from app.config import settings
from app.embedding_cache import cache_key, is_cached, load_cache
from app.ingest import load_csv_tickets, load_markdown_files

console = Console()

BENCH_COLLECTION = "benchmark_ingest"
BATCH_SIZE = 512


def _percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p / 100
    lo = int(idx)
    hi = min(lo + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


def run_ingest_benchmark() -> None:
    dataset = settings.dataset
    console.rule(f"[bold magenta]Ingest Throughput Benchmark — dataset: {dataset}[/bold magenta]")

    embed_time: float | None = None
    embed_throughput: float | None = None

    if is_cached(dataset):
        console.print(f"\n[green]Using pre-computed embeddings[/green] (cache key: {cache_key(dataset)})")
        vectors, payloads = load_cache(dataset)
        num_chunks = len(vectors)
        console.print(f"  Loaded [cyan]{num_chunks}[/cyan] vectors from cache")
        points = [
            PointStruct(id=i, vector=vec, payload=payload)
            for i, (vec, payload) in enumerate(zip(vectors, payloads))
        ]
    else:
        console.print("\n[yellow]No cache found — embedding on the fly.[/yellow] Run [bold]python -m benchmarks.precompute[/bold] to skip this step.")

        console.print("\n[bold]Loading documents...[/bold]")
        docs = load_markdown_files(dataset) + load_csv_tickets(dataset)
        console.print(f"  Total: [cyan]{len(docs)}[/cyan] documents")

        console.print("\n[dim]Chunking...[/dim]")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)
        num_chunks = len(chunks)
        console.print(f"  -> [cyan]{num_chunks}[/cyan] chunks")

        console.print("\n[dim]Loading embedding model...[/dim]")
        embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)

        console.print(f"\nEmbedding [cyan]{num_chunks}[/cyan] chunks (CPU)...")
        t_embed_start = time.perf_counter()
        vectors = embeddings.embed_documents([c.page_content for c in chunks])
        embed_time = time.perf_counter() - t_embed_start
        embed_throughput = num_chunks / embed_time
        console.print(f"  Done in [green]{embed_time:.2f}s[/green] ([cyan]{embed_throughput:.1f}[/cyan] chunks/sec)")

        points = [
            PointStruct(
                id=i,
                vector=vec,
                payload={"text": chunk.page_content, **chunk.metadata},
            )
            for i, (vec, chunk) in enumerate(zip(vectors, chunks))
        ]

    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    existing = [c.name for c in client.get_collections().collections]
    if BENCH_COLLECTION in existing:
        _ = client.delete_collection(BENCH_COLLECTION)
    _ = client.create_collection(
        collection_name=BENCH_COLLECTION,
        vectors_config=VectorParams(size=settings.embedding_dimensions, distance=Distance.COSINE),
    )

    # --- Write phase (disk I/O bound) ---
    console.print(f"\nWriting [cyan]{num_chunks}[/cyan] vectors to Qdrant (batch_size={BATCH_SIZE})...")
    batch_latencies_ms: list[float] = []
    t_write_start = time.perf_counter()
    for batch_start in range(0, len(points), BATCH_SIZE):
        t_batch = time.perf_counter()
        _ = client.upsert(
            collection_name=BENCH_COLLECTION,
            points=points[batch_start : batch_start + BATCH_SIZE],
            wait=True,
        )
        batch_latencies_ms.append((time.perf_counter() - t_batch) * 1000)
    write_time = time.perf_counter() - t_write_start
    write_throughput = num_chunks / write_time
    console.print(f"  Done in [green]{write_time:.2f}s[/green] ([cyan]{write_throughput:.0f}[/cyan] vectors/sec)")

    _ = client.delete_collection(BENCH_COLLECTION)

    table = Table(title="Ingest Benchmark Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Dataset", dataset)
    table.add_row("Chunks", str(num_chunks))
    table.add_row("Embeddings", "pre-cached" if embed_time is None else f"{embed_time:.2f}s ({embed_throughput:.0f} chunks/sec)")
    table.add_row("Qdrant write time", f"{write_time:.2f}s")
    table.add_row("Qdrant write throughput", f"{write_throughput:.0f} vectors/sec")
    table.add_row("Write batches", str(len(batch_latencies_ms)))
    table.add_row("Batch latency p50", f"{statistics.median(batch_latencies_ms):.0f} ms")
    table.add_row("Batch latency p95", f"{_percentile(batch_latencies_ms, 95):.0f} ms")
    table.add_row("Batch latency p99", f"{_percentile(batch_latencies_ms, 99):.0f} ms")
    table.add_row("Embedding model", settings.embedding_model)
    table.add_row("Vector dimensions", str(settings.embedding_dimensions))

    console.print()
    console.print(table)
    console.print("\n[dim]Qdrant write is disk-I/O-bound — scales with ABS IOPS.[/dim]")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in ("small", "medium", "large")]
    if args:
        settings.dataset = args[0]  # pyright: ignore[reportAttributeAccessIssue]
    run_ingest_benchmark()
