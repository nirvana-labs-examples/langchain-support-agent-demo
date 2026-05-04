# Benchmark Results

Sample results collected on a **Nirvana Cloud `standard-4` VM** (4 vCPUs, 16 GB RAM)
with Qdrant running on an attached **ABS volume** (50 GB, 10,000 IOPS).

## Ingest Throughput

Measures Qdrant write throughput only. Pre-computed embeddings are loaded from
`benchmarks/.cache/` — the CPU embedding step is excluded so numbers reflect
only HNSW index construction and disk I/O.

| Metric                  | small   | medium      | large       |
|-------------------------|---------|-------------|-------------|
| Chunks ingested         | ~200    | ~46,000     | ~470,000    |
| Qdrant write time       | < 1s    | ~35s        | ~360s       |
| Write throughput        | —       | ~1,300 vec/sec | ~1,300 vec/sec |
| Batch latency p50       | —       | ~380 ms     | ~380 ms     |
| Batch latency p95       | —       | ~420 ms     | ~430 ms     |
| Batch latency p99       | —       | ~450 ms     | ~460 ms     |

> Throughput is HNSW-construction-bound and scales with ABS IOPS.
> Run `python -m benchmarks.ingest` to see results on your hardware.

## Retrieval Latency

Measures Qdrant HNSW search only. Queries are pre-embedded in a batch before
the timer starts — CPU embedding time is excluded so numbers reflect pure
storage I/O.

| Metric | Nirvana ABS       | Generic NFS volume |
|--------|--------------------|--------------------|
| p50    | 2 ms               | 5 ms               |
| p95    | 5 ms               | 14 ms              |
| p99    | 8 ms               | 28 ms              |
| Max    | 15 ms              | 52 ms              |

> **~3× improvement in p99 latency** on ABS-backed storage vs. NFS.

## Interpretation

**At this scale (< 500K vectors)**, the Qdrant HNSW scan dominates — typically
**2–5ms on ABS**. The HNSW graph fits mostly in RAM and storage access is
sequential during ingestion.

**At scale (1M+ vectors)**, the HNSW graph traversal requires more random disk
reads, and ABS's sub-millisecond access latency becomes the deciding factor.
NFS latency compounds across index hops, degrading p99 significantly.

**Why p99 matters**: A support agent serving 50 concurrent users will hit the
tail latency on every burst. The difference between 8ms and 28ms p99
determines whether the agent feels snappy or laggy under load.

**Ingest is I/O-bound**: Qdrant's HNSW index construction writes heavily to
disk during upserts. High-IOPS ABS storage directly accelerates bulk ingestion —
critical when processing a large backlog of support tickets or documentation
updates.
