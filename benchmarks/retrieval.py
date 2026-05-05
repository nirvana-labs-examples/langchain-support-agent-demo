"""
Benchmark: retrieval latency (p50 / p95 / p99).

Embeds all query texts upfront in a single batch (outside the timer), then
fires raw Qdrant vector searches and measures only the HNSW disk-read phase:
  - Qdrant HNSW similarity search + disk reads (~2-5ms on ABS)

This isolates storage I/O from CPU embedding time so the numbers reflect
Nirvana ABS performance directly.

Run:
  python -m benchmarks.retrieval           # uses medium
  python -m benchmarks.retrieval small
  python -m benchmarks.retrieval large
  python -m benchmarks.retrieval medium --queries=200
"""

import csv
import json
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
import time

from qdrant_client import QdrantClient
from rich.console import Console
from rich.table import Table

from app.config import settings
from app.ingest import ensure_extracted
from app.retriever import get_embeddings

console = Console()

_ROOT = Path(__file__).parent.parent

# Baseline knowledge-base queries that cover the article topics.
# These are always included regardless of dataset.
_KB_QUERIES: list[str] = [
    "What is the refund policy for enterprise annual customers?",
    "How do I reset my password?",
    "VM is stuck in pending state",
    "How do I mount a block volume after reboot?",
    "What are the escalation criteria for P1 tickets?",
    "How do I resize a VM instance?",
    "What happens when my payment fails?",
    "How do I add a GPU instance?",
    "What is the free tier inactivity policy?",
    "How do I contact enterprise support?",
    "How do I set up a VPC with custom subnets?",
    "What is the difference between Layer 4 and Layer 7 load balancers?",
    "How do I configure DNS for my domain on Nirvana Cloud?",
    "What object storage classes are available?",
    "How do I set up IAM roles and policies?",
    "How do I enable two-factor authentication?",
    "How do I view the audit log for my account?",
    "How do I deploy a Kubernetes cluster?",
    "How do I push images to the container registry?",
    "How do I manage infrastructure with Terraform?",
    "How do I set up monitoring and alerting?",
    "How can I reduce my monthly cloud spend?",
    "What are spot instances and how do they work?",
    "How do I configure auto-scaling for my VMs?",
    "How do I set up a VPN connection?",
    "How do I enable cross-region replication for block storage?",
    "How do I restore from a snapshot backup?",
    "How do I deploy across multiple regions for high availability?",
    "How do I configure SSO with my identity provider?",
    "How do I connect to a managed PostgreSQL database?",
    "How do I use Redis for session caching?",
    "How do I ship logs to a central aggregator?",
    "How do I migrate VMs from AWS to Nirvana Cloud?",
    "What are reserved instances and how do I purchase them?",
    "How do I mount an NFS file share?",
    "What are the GDPR compliance controls available?",
    "What are the SLAs for P1 and P2 support tickets?",
    "How do I integrate my CI/CD pipeline with Nirvana Cloud?",
    "How do I host a static website?",
    "What GPU instance types are available for AI workloads?",
    "How do I host a Qdrant vector database on Nirvana Cloud?",
    "How do I manage team members and permissions?",
    "How do I configure IPv6 on my VPC?",
    "How do I get a managed TLS certificate?",
    "How do I use webhooks to receive event notifications?",
    "How do I manage infrastructure with Pulumi?",
    "How do I understand my billing cycle and invoices?",
    "How do I run a Windows Server VM?",
    "What network egress pricing applies to my region?",
    "How do I create a custom VM image?",
]


def _load_ticket_subjects(dataset: str, n: int) -> list[str]:
    ensure_extracted(dataset)
    csv_path = _ROOT / "data" / dataset / "sample_tickets.csv"
    subjects: list[str] = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append(row["subject"])
    rng = random.Random(42)
    rng.shuffle(subjects)
    return subjects[:n]


def _build_query_list(num_queries: int) -> list[str]:
    kb = _KB_QUERIES[:]
    remaining = max(0, num_queries - len(kb))
    ticket_subjects = _load_ticket_subjects(settings.dataset, remaining) if remaining > 0 else []
    queries = kb + ticket_subjects
    random.Random(42).shuffle(queries)
    return queries[:num_queries]


def percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p / 100
    lo = int(idx)
    hi = min(lo + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


def embed_queries(queries: list[str]) -> list[list[float]]:
    console.print(f"\n[dim]Embedding {len(queries)} queries (excluded from latency timer)...[/dim]")
    embeddings = get_embeddings()
    vectors = embeddings.embed_documents(queries)
    console.print(f"  [dim]Done.[/dim]")
    return vectors


def measure_latencies(query_vectors: list[list[float]]) -> list[float]:
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    collection = f"{settings.qdrant_collection_name}_{settings.dataset}"
    latencies: list[float] = []

    console.print(f"\nRunning [cyan]{len(query_vectors)}[/cyan] vector searches (Qdrant only, embedding excluded)...")
    for vec in query_vectors:
        t0 = time.perf_counter()
        _ = client.search(collection_name=collection, query_vector=vec, limit=settings.retriever_top_k)
        latencies.append((time.perf_counter() - t0) * 1000)
    console.print("  Done.")

    return latencies


def _check_collection_exists() -> None:
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    collection = f"{settings.qdrant_collection_name}_{settings.dataset}"
    existing = [c.name for c in client.get_collections().collections]
    if collection not in existing:
        console.print(f"\n[red]Collection '{collection}' does not exist.[/red]\nRun [bold]python -m app.ingest {settings.dataset}[/bold] first to populate it.")
        sys.exit(1)


def run_retrieval_benchmark(
    num_queries: int,
    json_path: str | None = None,
    platform: str | None = None,
) -> None:
    console.rule(f"[bold magenta]Retrieval Latency Benchmark — dataset: {settings.dataset}[/bold magenta]")

    _check_collection_exists()

    console.print(f"\nBuilding query list ({num_queries} queries from KB articles + ticket subjects)...")
    queries = _build_query_list(num_queries)

    query_vectors = embed_queries(queries)
    latencies = measure_latencies(query_vectors)

    p50 = statistics.median(latencies)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    mean = statistics.mean(latencies)

    table = Table(title="Retrieval Latency Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Queries run", str(len(latencies)))
    table.add_row("Mean", f"{mean:.1f} ms")
    table.add_row("p50", f"{p50:.1f} ms")
    table.add_row("p95", f"{p95:.1f} ms")
    table.add_row("p99", f"{p99:.1f} ms")
    table.add_row("Min", f"{min(latencies):.1f} ms")
    table.add_row("Max", f"{max(latencies):.1f} ms")
    table.add_row("Dataset", settings.dataset)
    table.add_row("Embedding model", settings.embedding_model)
    table.add_row("Top-K", str(settings.retriever_top_k))

    console.print()
    console.print(table)
    console.print("\n[dim]Latency is Qdrant HNSW search only — query embedding is done upfront and excluded from the timer. At 1M+ vectors the HNSW index no longer fits fully in RAM and storage latency becomes the dominant factor — where Nirvana ABS (Accelerated Block Storage) is most pronounced.[/dim]")

    if json_path:
        result = {
            "platform": platform or "local",
            "benchmark": "retrieval",
            "dataset": settings.dataset,
            "queries": len(latencies),
            "search_latency_mean_ms": round(mean, 3),
            "search_latency_p50_ms": round(p50, 3),
            "search_latency_p95_ms": round(p95, 3),
            "search_latency_p99_ms": round(p99, 3),
            "search_latency_min_ms": round(min(latencies), 3),
            "search_latency_max_ms": round(max(latencies), 3),
            "embedding_model": settings.embedding_model,
            "top_k": settings.retriever_top_k,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        out = Path(json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        _ = out.write_text(json.dumps(result, indent=2))
        console.print(f"[dim]Wrote JSON results to {json_path}[/dim]")


_DEFAULT_QUERIES = {"small": 20, "medium": 200, "large": 500}

if __name__ == "__main__":
    argv = sys.argv[1:]
    dataset_args = [a for a in argv if a in ("small", "medium", "large")]
    if dataset_args:
        settings.dataset = dataset_args[0]  # pyright: ignore[reportAttributeAccessIssue]

    num_queries = _DEFAULT_QUERIES[settings.dataset]
    json_path: str | None = None
    platform: str | None = None
    for arg in argv:
        if arg.startswith("--queries="):
            num_queries = int(arg.split("=", 1)[1])
        elif arg.startswith("--json="):
            json_path = arg.split("=", 1)[1]
        elif arg.startswith("--platform="):
            platform = arg.split("=", 1)[1]
        elif arg.isdigit():
            num_queries = int(arg)

    run_retrieval_benchmark(num_queries, json_path=json_path, platform=platform)
