"""
Benchmark: document ingest throughput with local embeddings.

Measures end-to-end ingest time against real dataset content, broken into:
  - Embedding (CPU-bound, local sentence-transformers model)
  - Qdrant write (disk I/O bound, HNSW index construction)

Both steps run on the Nirvana VM. No external API calls.

Run:
  python -m benchmarks.ingest_benchmark           # uses medium dataset
  python -m benchmarks.ingest_benchmark small
  python -m benchmarks.ingest_benchmark large
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
from app.ingest import load_csv_tickets, load_markdown_files

console = Console()

BENCH_COLLECTION = "benchmark_ingest"


def _percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p / 100
    lo = int(idx)
    hi = min(lo + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


def run_ingest_benchmark() -> None:
    console.rule(f"[bold magenta]Ingest Throughput Benchmark — dataset: {settings.dataset}[/bold magenta]")

    console.print("\n[bold]Loading dataset documents...[/bold]")
    docs = load_markdown_files(settings.dataset) + load_csv_tickets(settings.dataset)
    console.print(f"  Total: [cyan]{len(docs)}[/cyan] documents")

    console.print("\n[dim]Chunking documents...[/dim]")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(docs)
    console.print(f"  -> [cyan]{len(chunks)}[/cyan] chunks")

    console.print("\n[dim]Loading embedding model...[/dim]")
    t0 = time.perf_counter()
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    load_time = time.perf_counter() - t0
    console.print(f"  Loaded [cyan]{settings.embedding_model}[/cyan] in {load_time:.1f}s")

    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    existing = [c.name for c in client.get_collections().collections]
    if BENCH_COLLECTION in existing:
        _ = client.delete_collection(BENCH_COLLECTION)
    _ = client.create_collection(
        collection_name=BENCH_COLLECTION,
        vectors_config=VectorParams(size=settings.embedding_dimensions, distance=Distance.COSINE),
    )

    # --- Embedding phase (CPU-bound) ---
    console.print(f"\nEmbedding [cyan]{len(chunks)}[/cyan] chunks (CPU)...")
    t_embed_start = time.perf_counter()
    vectors = embeddings.embed_documents([c.page_content for c in chunks])
    embed_time = time.perf_counter() - t_embed_start
    embed_throughput = len(chunks) / embed_time
    console.print(f"  Done in [green]{embed_time:.2f}s[/green] ([cyan]{embed_throughput:.1f}[/cyan] chunks/sec)")

    # --- Write phase (disk I/O bound) ---
    BATCH_SIZE = 512
    console.print(f"\nWriting [cyan]{len(chunks)}[/cyan] vectors to Qdrant (batch_size={BATCH_SIZE})...")
    points = [
        PointStruct(
            id=i,
            vector=vec,
            payload={"text": chunk.page_content, **chunk.metadata},
        )
        for i, (vec, chunk) in enumerate(zip(vectors, chunks))
    ]
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
    write_throughput = len(chunks) / write_time
    console.print(f"  Done in [green]{write_time:.2f}s[/green] ([cyan]{write_throughput:.0f}[/cyan] vectors/sec)")

    total_time = embed_time + write_time
    _ = client.delete_collection(BENCH_COLLECTION)

    table = Table(title="Ingest Benchmark Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Dataset", settings.dataset)
    table.add_row("Documents", str(len(docs)))
    table.add_row("Chunks", str(len(chunks)))
    table.add_row("Embedding time", f"{embed_time:.2f}s")
    table.add_row("Embedding throughput", f"{embed_throughput:.1f} chunks/sec")
    table.add_row("Qdrant write time", f"{write_time:.2f}s")
    table.add_row("Qdrant write throughput", f"{write_throughput:.0f} vectors/sec")
    table.add_row("Write batches", str(len(batch_latencies_ms)))
    table.add_row("Batch latency p50", f"{statistics.median(batch_latencies_ms):.0f} ms")
    table.add_row("Batch latency p95", f"{_percentile(batch_latencies_ms, 95):.0f} ms")
    table.add_row("Batch latency p99", f"{_percentile(batch_latencies_ms, 99):.0f} ms")
    table.add_row("Total time", f"{total_time:.2f}s")
    table.add_row("Embedding model", settings.embedding_model)
    table.add_row("Vector dimensions", str(settings.embedding_dimensions))

    console.print()
    console.print(table)
    console.print("\n[dim]Embedding is CPU-bound — scales with vCPU count and clock speed.\nQdrant write is disk-I/O-bound — scales with ABS IOPS. Both run entirely on the Nirvana VM.[/dim]")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in ("small", "medium", "large")]
    if args:
        settings.dataset = args[0]  # pyright: ignore[reportAttributeAccessIssue]
    run_ingest_benchmark()
