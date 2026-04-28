"""
Benchmark: retrieval latency (p50 / p95 / p99).

Fires N retrieval queries against the live Qdrant collection and measures
end-to-end latency including:
  - Query embedding (OpenAI API call, ~100-200ms at this scale)
  - Qdrant HNSW similarity search + disk reads (<3ms on NVMe)

This is the hot path for every agent invocation. p99 here directly
determines worst-case agent response time under concurrent load.

Run:
  python -m benchmarks.retrieval_latency_benchmark
"""

import statistics
import time

from rich.console import Console
from rich.table import Table

from app.config import settings
from app.retriever import get_retriever

console = Console()

QUERIES = [
    "What is the refund policy for enterprise annual customers?",
    "How do I reset my password?",
    "VM is stuck in pending state",
    "How do I mount a volume after reboot?",
    "What are the escalation criteria for P1 tickets?",
    "How do I resize a VM instance?",
    "What happens when my payment fails?",
    "How do I add a GPU instance?",
    "What is the free tier inactivity policy?",
    "How do I contact enterprise support?",
]

ITERATIONS = 3  # Each query is run this many times; aggregate stats are reported


def percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p / 100
    lo = int(idx)
    hi = min(lo + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


def measure_latencies() -> list[float]:
    retriever = get_retriever()
    latencies = []

    total = len(QUERIES) * ITERATIONS
    console.print(
        f"\nRunning [cyan]{total}[/cyan] retrieval queries "
        f"({len(QUERIES)} unique × {ITERATIONS} iterations)...\n"
    )

    for i in range(ITERATIONS):
        for query in QUERIES:
            t0 = time.perf_counter()
            retriever.invoke(query)
            latency_ms = (time.perf_counter() - t0) * 1000
            latencies.append(latency_ms)
            console.print(f"  [{i+1}/{ITERATIONS}] {query[:55]:<55} {latency_ms:6.1f} ms")

    return latencies


def run_retrieval_benchmark():
    console.rule("[bold magenta]Retrieval Latency Benchmark[/bold magenta]")

    latencies = measure_latencies()

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
    table.add_row("Embedding model", settings.embedding_model)
    table.add_row("Top-K", str(settings.retriever_top_k))

    console.print()
    console.print(table)
    console.print(
        "\n[dim]Most latency here is the OpenAI embedding API call (~100–200ms). "
        "The Qdrant HNSW scan itself typically takes <3ms on NVMe-backed storage "
        "like Nirvana Cloud ABS. At 1M+ vectors, storage latency becomes the "
        "dominant factor — where the NVMe advantage is most pronounced.[/dim]"
    )


if __name__ == "__main__":
    run_retrieval_benchmark()
