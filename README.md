# Nirvana Cloud — Semantic Support Search Demo

> **AI workloads are infrastructure-heavy.**
> This demo runs an entire semantic search stack — embedding model + vector
> database — on a single Nirvana Cloud VM. No external APIs, no API keys.

A self-contained semantic search service over a customer-support knowledge
base. Built to make the case that **Nirvana Cloud is the right place to host
stateful AI workloads**: retrieval, vector search, and the storage layer they
depend on.

---

## Why this demo doesn't use an LLM

Most AI agent demos call out to OpenAI for both embeddings and answer
generation. When you benchmark such a stack, **>95% of every measurement is
network latency to OpenAI** — the numbers don't reflect the host
infrastructure at all.

This demo strips back to the hot path that actually depends on local compute
and storage:

1. Embed the user's query with a local model (CPU)
2. Run a similarity search against Qdrant's HNSW index (CPU + disk)
3. Return the top-K matching document chunks with relevance scores

No LLM generation step, no external APIs. Every millisecond reflects
Nirvana's CPU and storage.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│               Customer / Support Rep                │
└─────────────────────┬───────────────────────────────┘
                      │  HTTP POST /search
┌─────────────────────▼───────────────────────────────┐
│              FastAPI Application                    │
│              app/main.py                            │
└─────────────────────┬───────────────────────────────┘
                      │  embed query (CPU)
┌─────────────────────▼───────────────────────────────┐
│         sentence-transformers (BGE-small)           │
│         Local model, 384 dims, ~30ms / query        │
└─────────────────────┬───────────────────────────────┘
                      │  similarity search
┌─────────────────────▼───────────────────────────────┐
│         Qdrant (Docker, self-hosted)                │
│         HNSW index, cosine distance                 │
└─────────────────────┬───────────────────────────────┘
                      │  index stored on
┌─────────────────────▼───────────────────────────────┐
│       Nirvana Cloud VM + ABS NVMe Volume            │
│       10,000+ IOPS, sub-millisecond latency         │
└─────────────────────────────────────────────────────┘
```

---

## Knowledge Base

The agent has access to:

| Document                                             | Content                       |
|------------------------------------------------------|-------------------------------|
| `data/refund_policy.md`                              | Refund rules by plan tier     |
| `data/onboarding_guide.md`                           | First-30-minutes guide        |
| `data/help_center_articles/billing_faq.md`           | Billing Q&A                   |
| `data/help_center_articles/vm_management.md`         | VM operations guide           |
| `data/help_center_articles/escalation_policy.md`     | Escalation criteria & SLAs    |
| `data/sample_tickets.csv`                            | 20 realistic support tickets  |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker + Docker Compose

#### Install uv

**macOS**
```bash
brew install uv
```

**Linux** (Nirvana Cloud VMs and other Linux environments)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env  # or restart your shell
```

### 1. Clone and configure

```bash
git clone https://github.com/nirvana-labs-examples/langchain-support-agent-demo.git
cd langchain-support-agent-demo
cp .env.example .env
```

The default `.env` works out of the box — no keys to fill in.

### 2. Start Qdrant

```bash
docker compose up -d qdrant
```

### 3. Install dependencies

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

The first run downloads the BGE-small embedding model (~130 MB) from
HuggingFace and caches it locally. Subsequent runs are fully offline.

### 4. Ingest the knowledge base

```bash
python -m app.ingest
```

You'll see the loading → chunking → embedding → indexing pipeline run with
progress output. Takes a few seconds on a modern CPU.

### 5. Search

#### Interactive CLI

```bash
python -m app.search
```

```
> what is the refund policy for enterprise customers?

  Results (5)                                          37ms

  1. refund_policy.md                              score 0.91
     Enterprise customers on annual contracts are eligible for a
     full refund within 14 days of contract signing...

  2. refund_policy.md                              score 0.84
     Beyond 90 days, refunds are handled on a case-by-case basis
     by the Enterprise Success team.
```

#### HTTP API

```bash
uvicorn app.main:app --reload
```

Then open **http://localhost:8000/docs** or:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "refund policy for enterprise customers", "top_k": 3}'
```

---

## Sample Queries

| Query | What it demonstrates |
|-------|----------------------|
| "refund policy for enterprise" | Policy retrieval with high precision |
| "how do I reset my password?" | Cross-document matching (guide + tickets) |
| "VM stuck pending" | Synonym handling via embeddings |
| "high outbound data transfer charges" | Long-tail technical queries |
| "P1 escalation criteria" | Acronym + policy lookup |
| "GPU instance VRAM" | Specific factual recall |

---

## Benchmarks

```bash
# Ingest throughput: chunks/sec (CPU embedding) + vectors/sec (disk write)
python -m benchmarks.ingest_benchmark

# Retrieval latency: p50/p95/p99 over a mix of realistic queries
python -m benchmarks.retrieval_latency_benchmark
```

See `benchmarks/sample_results.md` for results collected on Nirvana Cloud.

Both benchmarks run **entirely on the host** — no external API calls. The
numbers reflect Nirvana's CPU and storage performance directly.

---

## Deploy on Nirvana Cloud

See [`infra/deploy_on_nirvana.md`](infra/deploy_on_nirvana.md) for a complete deployment guide.

The short version:
1. Create a VM (`standard-4` or higher)
2. Attach an ABS NVMe volume and mount it at `/data/qdrant`
3. Bind the Docker `qdrant_storage` volume to `/data/qdrant`
4. `docker compose up -d qdrant && python -m app.ingest && uvicorn app.main:app --host 0.0.0.0`

---

## Project Structure

```
langchain-support-agent-demo/
  README.md                        ← you are here
  docker-compose.yml               ← self-hosted Qdrant
  .env.example                     ← environment variables (no keys needed)
  requirements.txt                 ← Python dependencies

  app/
    config.py                      ← Pydantic settings (reads from .env)
    ingest.py                      ← document → chunk → embed → Qdrant
    retriever.py                   ← cached embedding model + Qdrant connection
    search.py                      ← interactive CLI for semantic search
    main.py                        ← FastAPI: GET /health, POST /search

  data/
    refund_policy.md
    onboarding_guide.md
    help_center_articles/
      billing_faq.md
      vm_management.md
      escalation_policy.md
    sample_tickets.csv

  benchmarks/
    ingest_benchmark.py            ← embed throughput + Qdrant write throughput
    retrieval_latency_benchmark.py ← p50/p95/p99 retrieval latency
    sample_results.md              ← results from Nirvana Cloud

  infra/
    deploy_on_nirvana.md           ← step-by-step deployment guide
    volume_setup.md                ← ABS volume sizing and backup
```

---

## Tech Stack

| Component           | Choice                            | Why                                    |
|---------------------|-----------------------------------|----------------------------------------|
| API framework       | FastAPI                           | Auto-docs, Pydantic-native             |
| Embedding model     | `BAAI/bge-small-en-v1.5` (local)  | High retrieval quality on CPU, no API  |
| Vector DB           | Qdrant (self-hosted, Docker)      | HNSW-on-disk, single-binary deploy     |
| Config              | Pydantic Settings v2              | Type-safe `.env` parsing               |
| Infra               | Nirvana Cloud VM + ABS            | Purpose-built for stateful AI workloads|
