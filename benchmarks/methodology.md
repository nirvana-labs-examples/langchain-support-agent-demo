# Benchmark methodology

These benchmarks exist to measure **storage performance under a realistic RAG
serving workload** — not embedding speed, not LLM throughput, not network
latency to a hosted API. Every design decision below is in service of that
goal: produce a number where the *only* meaningful variable is the underlying
block device.

The shape of the numbers should be defensible regardless of where the demo is
running (local, Nirvana Cloud, AWS EC2 with various EBS variants). When the
ranking changes between platforms, that change should reflect storage and
storage alone.

## What's measured, and what's excluded

| Step | Included in timer? | Why |
|---|---|---|
| Loading documents from disk | No | One-time, dominated by tar/zip extraction, not the path we're benchmarking |
| Chunking | No | CPU-bound text splitting, no I/O of interest |
| Embedding (BGE-small) | **No** — pre-computed and cached | This is the biggest leak in most "vector DB benchmarks". Embedding 470K chunks on CPU takes minutes; if you let it inside the timer you're benchmarking your CPU, not your storage. We pre-compute once and ship `.npy` blobs in `data/.cache/`. |
| Qdrant `upsert` (write phase) | **Yes** | The headline number for ingest. Disk-bound at scale (HNSW writes + WAL fsync). |
| Query embedding | **No** — done in a single batch *before* the timer starts | Same reason. Each query is ~30ms of CPU on BGE; if you measure it per-query, p50/p95/p99 reflect the embedding model, not the database. |
| Qdrant `search` (HNSW traversal + payload load) | **Yes** | The headline number for retrieval. |

## On-disk Qdrant collections

`QDRANT_ON_DISK=true` is the default. Vectors and the HNSW graph are
memory-mapped (`mmap`) from disk rather than fully loaded into RAM. Linux
serves reads through the page cache — **so cold reads hit the block device,
warm reads don't**.

This matches the realistic deployment regime: at 10M+ vectors the index
doesn't fit in RAM and you're paging from storage anyway. Forcing this mode
on a small dataset gives the same I/O pattern at any scale, which is why the
cross-cloud comparison is meaningful even on `medium` (46K vectors).

The legacy in-RAM mode (`QDRANT_ON_DISK=false`) loads everything into
process memory at startup. Search never touches disk after that. **It's a
CPU/RAM benchmark wearing a storage-benchmark t-shirt** — useful for
debugging Qdrant, useless for comparing block devices.

## Page cache drop before each retrieval run

Even with `on_disk=true`, Linux happily serves recently-read pages from RAM.
After `app.ingest` writes the collection, the entire vector file is sitting
in page cache and the first batch of queries reads from RAM regardless of
the underlying storage.

The infra playbook (`infra/ansible/roles/benchmark-runner/`) runs
`echo 3 > /proc/sys/vm/drop_caches` between ingest and retrieval, and again
between every concurrency level in the sweep. **Each run starts cold.** That's
not how production caches behave, but it's the only way to compare storage
fairly across platforms within a short benchmark window.

A real production p50 will be lower than ours. The *gap between platforms*
should still be informative.

## Concurrency sweep (1, 4, 16, 64)

Single-stream retrieval (`--concurrency=1`) issues one HNSW traversal at a
time. That generates only a handful of outstanding I/O requests — far below
what high-IOPS storage like ABS or io2 is designed to serve. The platform
ranking from `c=1` understates the storage advantage; you're measuring
single-thread CPU + memory bandwidth as much as disk.

At `c=16` and `c=64`, multiple traversals overlap. The kernel's I/O
scheduler dispatches reads in parallel, and the page-fault stream finally
saturates the block device. That's where the `fio` numbers (105k vs 40k
IOPS) translate into application-level latency differences.

The benchmark reports both:
- **Per-query latency under load** (p50/p95/p99) — what a user sees when the
  system is busy
- **Throughput (qps)** — total queries / wall time — how many users you can
  serve concurrently

Both come from the same run. The crossover point where one storage variant
pulls ahead of another is itself an interesting datapoint.

## What these benchmarks intentionally don't do

- **No embedding throughput numbers.** Use a different benchmark for that.
- **No LLM latency.** `app.ask` exists for the demo; it's not part of the
  reported numbers.
- **No network latency to a hosted vector DB.** Qdrant runs on the same
  host as the bench client. The TCP loopback plus Docker bridge adds ~50µs
  per query — measurable but constant across platforms.
- **No multi-tenant noise.** A single Qdrant collection, a single benchmark
  process. Real workloads share I/O bandwidth across tenants and the
  ranking can change.
- **No warm-cache steady state.** The cache-drop-before-each-run is the
  opposite assumption. Reasonable middle-ground would be a long-running
  bench that lets cache warm naturally — not what we do here.

## Hardware parity in the cross-cloud comparison

All five platforms use **4 vCPU / 16 GB RAM / 256 GB root volume**:

| Platform | Instance | Storage |
|---|---|---|
| `gp3-3k` | AWS m6i.xlarge | gp3, 3,000 IOPS |
| `gp3-16k` | AWS m6i.xlarge | gp3, 16,000 IOPS |
| `io2-32k` | AWS m6i.xlarge | io2, 32,000 IOPS |
| `io2-64k` | AWS m6i.xlarge | io2, 64,000 IOPS |
| `nirvana-abs` | Nirvana n1-standard-4 | ABS |

The CPUs are not identical (Intel Ice Lake on AWS, vendor-dependent on
Nirvana), so a fraction of any latency gap is CPU-attributable rather than
storage. The `c=1` row is the most CPU-sensitive; `c=16+` and the raw `fio`
numbers are the cleanest storage signal.

## Reading the results

`results/comparison_medium.md` has five tables:

1. **Raw disk (fio)** — pure block-device characterization, application-free
2. **Ingest** — Qdrant write throughput
3. **Retrieval p50 under load** — typical-user latency at each concurrency level
4. **Retrieval p99 under load** — tail latency at each concurrency level
5. **Throughput (qps) under load** — sustained query rate at each concurrency level

The story you're looking for: **does the platform ranking from `fio`
translate into the application-level tables?** When it does, storage matters
for the workload. When it doesn't, the bottleneck is somewhere else and
spending more on IOPS is wasted.
