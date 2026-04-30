"""
Benchmark: retrieval latency (p50 / p95 / p99).

Fires N retrieval queries against the live Qdrant collection and measures
end-to-end latency including:
  - Query embedding (local sentence-transformers on CPU, ~25-50ms)
  - Qdrant HNSW similarity search + disk reads (~2-5ms on ABS)

Both steps run on the Nirvana VM. Every millisecond reflects local
compute and storage — no external API variance.

Queries are sampled from real ticket subjects in the dataset (plus a small
set of knowledge-base questions), so the mix scales with dataset size.

Run:
  python -m benchmarks.retrieval_latency_benchmark           # uses medium
  python -m benchmarks.retrieval_latency_benchmark small
  python -m benchmarks.retrieval_latency_benchmark large
  python -m benchmarks.retrieval_latency_benchmark medium --queries 200
"""

import csv
import random
import statistics
import sys
from pathlib import Path
import time

from rich.console import Console
from rich.table import Table

from app.config import settings
from app.retriever import get_retriever

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


def measure_latencies(queries: list[str]) -> list[float]:
    retriever = get_retriever()
    latencies: list[float] = []

    console.print(f"\nRunning [cyan]{len(queries)}[/cyan] retrieval queries...")
    for query in queries:
        t0 = time.perf_counter()
        _ = retriever.invoke(query)
        latencies.append((time.perf_counter() - t0) * 1000)
    console.print("  Done.")

    return latencies


def run_retrieval_benchmark(num_queries: int) -> None:
    console.rule(f"[bold magenta]Retrieval Latency Benchmark — dataset: {settings.dataset}[/bold magenta]")

    console.print(f"\nBuilding query list ({num_queries} queries from KB articles + ticket subjects)...")
    queries = _build_query_list(num_queries)

    latencies = measure_latencies(queries)

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
    console.print("\n[dim]Latency breakdown: ~25-50ms local CPU embedding + ~2-5ms Qdrant HNSW search. Both run on the Nirvana VM. At 1M+ vectors the HNSW index no longer fits fully in RAM and storage latency becomes the dominant factor — where Nirvana ABS (Accelerated Block Storage) is most pronounced.[/dim]")


_DEFAULT_QUERIES = {"small": 20, "medium": 200, "large": 500}

if __name__ == "__main__":
    argv = sys.argv[1:]
    dataset_args = [a for a in argv if a in ("small", "medium", "large")]
    if dataset_args:
        settings.dataset = dataset_args[0]  # pyright: ignore[reportAttributeAccessIssue]

    num_queries = _DEFAULT_QUERIES[settings.dataset]
    for arg in argv:
        if arg.startswith("--queries="):
            num_queries = int(arg.split("=", 1)[1])
        elif arg.isdigit():
            num_queries = int(arg)

    run_retrieval_benchmark(num_queries)
