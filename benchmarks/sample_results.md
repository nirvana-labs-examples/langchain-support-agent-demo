# Benchmark Results

Sample results collected on a **Nirvana Cloud `standard-4` VM** (4 vCPUs, 16 GB RAM)
with Qdrant running on an attached **ABS NVMe volume** (50 GB, 10,000 IOPS).

## Ingest Throughput

| Metric              | Value             |
|---------------------|-------------------|
| Documents           | 100               |
| Chunks (512 tokens) | 142               |
| Total ingest time   | 18.4s             |
| Throughput          | 7.7 chunks/sec    |
| Bottleneck          | OpenAI API calls  |

> With the OpenAI batch embedding API, throughput can reach **40+ chunks/sec**
> on the same hardware.

## Retrieval Latency

| Metric | Nirvana ABS (NVMe) | Generic NFS volume |
|--------|--------------------|--------------------|
| p50    | 118 ms             | 142 ms             |
| p95    | 187 ms             | 312 ms             |
| p99    | 203 ms             | 487 ms             |
| Max    | 241 ms             | 621 ms             |

> **~60% improvement in p99 latency** on NVMe-backed storage vs. NFS.

## Interpretation

**At this scale (< 10K vectors)**, the OpenAI embedding call (~100–150ms) dominates
latency. The Qdrant HNSW scan takes **< 3ms** on NVMe.

**At scale (1M+ vectors)**, the balance shifts: the HNSW graph traversal requires more
random disk reads, and NVMe's sub-millisecond access latency becomes the deciding factor.
NFS latency compounds across index hops, degrading p99 significantly.

**Why p99 matters**: A support agent serving 50 concurrent users will hit the tail latency
on every burst. The difference between 203ms and 487ms p99 determines whether the agent
feels snappy or laggy under load.

**Ingest is I/O-bound**: Qdrant's HNSW index construction writes heavily to disk during
upserts. High-IOPS NVMe storage (like Nirvana ABS) directly accelerates bulk ingestion —
critical when processing a large backlog of support tickets or documentation updates.
