"""
Benchmark: document ingest throughput with local embeddings.

Measures end-to-end ingest time, broken into:
  - Embedding (CPU-bound, local sentence-transformers model)
  - Qdrant write (disk I/O bound, HNSW index construction)

Both steps run on the Nirvana VM. No external API calls.

Run:
  python -m benchmarks.ingest_benchmark
"""

import time

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from rich.console import Console
from rich.table import Table

from app.config import settings

console = Console()

BENCH_COLLECTION = "benchmark_ingest"
DOC_COUNT = 100
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


def generate_synthetic_docs(n: int) -> list[Document]:
    template = (
        "Support Article #{i}\n\n"
        "This article covers common issues related to topic #{i} on Nirvana Cloud. "
        "Customers experiencing this issue should follow these steps:\n\n"
        "1. Check the current status at status.nirvanacloud.io.\n"
        "2. Restart the affected service.\n"
        "3. If the problem persists, open a support ticket with logs attached.\n\n"
        "Common symptoms include slow response times, failed API calls, and "
        "unexpected billing charges. The Nirvana Cloud team monitors all services "
        "24/7 and will respond to P1 issues within 15 minutes.\n"
    )
    return [
        Document(
            page_content=template.format(i=i),
            metadata={"source": f"synthetic_{i}.md", "benchmark": True},
        )
        for i in range(n)
    ]


def run_ingest_benchmark():
    console.rule("[bold magenta]Ingest Throughput Benchmark[/bold magenta]")

    console.print("\n[dim]Loading embedding model...[/dim]")
    t0 = time.perf_counter()
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    load_time = time.perf_counter() - t0
    console.print(f"  Loaded [cyan]{settings.embedding_model}[/cyan] in {load_time:.1f}s")

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    existing = [c.name for c in client.get_collections().collections]
    if BENCH_COLLECTION in existing:
        _ = client.delete_collection(BENCH_COLLECTION)
    _ = client.create_collection(
        collection_name=BENCH_COLLECTION,
        vectors_config=VectorParams(
            size=settings.embedding_dimensions,
            distance=Distance.COSINE,
        ),
    )

    console.print(f"\nGenerating [cyan]{DOC_COUNT}[/cyan] synthetic documents...")
    docs = generate_synthetic_docs(DOC_COUNT)

    console.print("Chunking documents...")
    chunks = splitter.split_documents(docs)
    console.print(f"  -> [cyan]{len(chunks)}[/cyan] chunks")

    # --- Embedding phase (CPU-bound) ---
    console.print(f"\nEmbedding {len(chunks)} chunks (CPU)...")
    t_embed_start = time.perf_counter()
    vectors = embeddings.embed_documents([c.page_content for c in chunks])
    embed_time = time.perf_counter() - t_embed_start
    embed_throughput = len(chunks) / embed_time
    console.print(f"  Done in [green]{embed_time:.2f}s[/green] ([cyan]{embed_throughput:.1f}[/cyan] chunks/sec)")

    # --- Write phase (disk I/O bound) ---
    console.print(f"\nWriting {len(chunks)} vectors to Qdrant...")
    points = [
        PointStruct(
            id=i,
            vector=vec,
            payload={"text": chunk.page_content, **chunk.metadata},
        )
        for i, (vec, chunk) in enumerate(zip(vectors, chunks))
    ]
    t_write_start = time.perf_counter()
    _ = client.upsert(collection_name=BENCH_COLLECTION, points=points, wait=True)
    write_time = time.perf_counter() - t_write_start
    write_throughput = len(chunks) / write_time
    console.print(f"  Done in [green]{write_time:.2f}s[/green] ([cyan]{write_throughput:.0f}[/cyan] vectors/sec)")

    total_time = embed_time + write_time
    _ = client.delete_collection(BENCH_COLLECTION)

    table = Table(title="Ingest Benchmark Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Documents", str(DOC_COUNT))
    table.add_row("Chunks", str(len(chunks)))
    table.add_row("Embedding time", f"{embed_time:.2f}s")
    table.add_row("Embedding throughput", f"{embed_throughput:.1f} chunks/sec")
    table.add_row("Qdrant write time", f"{write_time:.2f}s")
    table.add_row("Qdrant write throughput", f"{write_throughput:.0f} vectors/sec")
    table.add_row("Total time", f"{total_time:.2f}s")
    table.add_row("Embedding model", settings.embedding_model)
    table.add_row("Vector dimensions", str(settings.embedding_dimensions))

    console.print()
    console.print(table)
    console.print("\n[dim]Embedding is CPU-bound — scales with vCPU count and clock speed.\nQdrant write is disk-I/O-bound — scales with NVMe IOPS. Both run entirely on the Nirvana VM.[/dim]")


if __name__ == "__main__":
    run_ingest_benchmark()
