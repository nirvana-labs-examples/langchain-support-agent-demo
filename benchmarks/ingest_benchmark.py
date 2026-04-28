"""
Benchmark: document ingest throughput.

Measures how many chunks/second can be embedded and stored in Qdrant.
This metric is directly affected by:
  - CPU speed (embedding batch preparation)
  - Storage IOPS (Qdrant writes HNSW index nodes to disk on every upsert)
  - Network latency to the OpenAI embedding API

Run:
  python -m benchmarks.ingest_benchmark
"""

import time
from typing import List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from rich.console import Console
from rich.table import Table

from app.config import settings

console = Console()

BENCH_COLLECTION = "benchmark_ingest"
DOC_COUNT = 100
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


def generate_synthetic_docs(n: int) -> List[Document]:
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

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    existing = [c.name for c in client.get_collections().collections]
    if BENCH_COLLECTION in existing:
        client.delete_collection(BENCH_COLLECTION)
    client.create_collection(
        collection_name=BENCH_COLLECTION,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

    console.print(f"\nGenerating [cyan]{DOC_COUNT}[/cyan] synthetic documents...")
    docs = generate_synthetic_docs(DOC_COUNT)

    console.print("Chunking documents...")
    chunks = splitter.split_documents(docs)
    console.print(f"  -> [cyan]{len(chunks)}[/cyan] chunks")

    console.print(f"\nRunning ingest (embedding + storing {len(chunks)} chunks)...\n")

    t_start = time.perf_counter()
    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=BENCH_COLLECTION,
        url=f"http://{settings.qdrant_host}:{settings.qdrant_port}",
        force_recreate=False,
    )
    elapsed = time.perf_counter() - t_start
    throughput = len(chunks) / elapsed

    client.delete_collection(BENCH_COLLECTION)

    table = Table(title="Ingest Benchmark Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Documents", str(DOC_COUNT))
    table.add_row("Chunks", str(len(chunks)))
    table.add_row("Total time", f"{elapsed:.2f}s")
    table.add_row("Throughput", f"{throughput:.1f} chunks/sec")
    table.add_row("Embedding model", settings.embedding_model)
    table.add_row("Qdrant host", f"{settings.qdrant_host}:{settings.qdrant_port}")

    console.print(table)
    console.print(
        "\n[dim]Note: throughput is bottlenecked by OpenAI API rate limits and "
        "Qdrant HNSW index writes. On Nirvana Cloud ABS (NVMe), Qdrant write "
        "IOPS are 3–5× faster than on NFS-backed storage.[/dim]"
    )


if __name__ == "__main__":
    run_ingest_benchmark()
