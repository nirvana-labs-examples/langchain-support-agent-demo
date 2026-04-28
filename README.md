# LangChain Customer Support Agent on Nirvana Cloud

> **AI agents are infrastructure-heavy workloads.**
> This demo shows why — and what happens when you run them on
> purpose-built cloud infrastructure.

A production-style AI customer support agent built with LangChain, Qdrant,
and OpenAI — designed to run on [Nirvana Cloud](https://nirvanalabs.io).

---

## Why Infrastructure Matters for AI Agents

Most AI agent demos skip the infrastructure. They run on a laptop, hit a
cloud LLM API, and call it done. That works for a proof of concept.

In production, your agent is constantly reading and writing:

| Component          | Infrastructure dependency                        |
|--------------------|--------------------------------------------------|
| Vector DB (Qdrant) | Disk IOPS for HNSW index reads/writes            |
| Ingest pipeline    | CPU for chunking + network for embedding API     |
| Retrieval          | RAM for index cache + disk for cold reads        |
| Agent memory       | Storage for conversation logs and checkpoints    |

When the storage layer is slow or inconsistent, the agent feels slow.
**Nirvana Cloud gives LangChain apps a faster, more predictable infrastructure
layer for RAG, vector search, and stateful AI agents.**

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│               Customer / Support Rep                │
└─────────────────────┬───────────────────────────────┘
                      │  HTTP POST /ask
┌─────────────────────▼───────────────────────────────┐
│              FastAPI Application                    │
│              app/main.py                            │
└─────────────────────┬───────────────────────────────┘
                      │  invoke()
┌─────────────────────▼───────────────────────────────┐
│              LangChain Agent                        │
│              app/agent.py                           │
│   (OpenAI Functions agent, gpt-4o-mini)             │
└─────────────────────┬───────────────────────────────┘
                      │  tool call: search_support_docs
┌─────────────────────▼───────────────────────────────┐
│              Vector Retriever                       │
│              app/retriever.py                       │
│   (text-embedding-3-small → cosine similarity)      │
└─────────────────────┬───────────────────────────────┘
                      │  similarity search
┌─────────────────────▼───────────────────────────────┐
│         Qdrant (Docker / Self-hosted)               │
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
- OpenAI API key

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
# Edit .env and add your OPENAI_API_KEY
```

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

### 4. Ingest the knowledge base

```bash
python -m app.ingest
```

You'll see a progress bar as documents are chunked, embedded, and stored in Qdrant.

```
─── Nirvana Support Agent — Ingest Pipeline ───
Step 1: Loading documents
  Loaded refund_policy.md
  Loaded onboarding_guide.md
  Loaded help_center_articles/billing_faq.md
  ...
  Loaded 20 tickets from sample_tickets.csv
  Total documents loaded: 26

Step 2: Chunking
  Split into 84 chunks (size=512, overlap=64)

Step 3: Connecting to Qdrant
  Connected to Qdrant at localhost:6333
  Created collection 'support_docs'

Step 4: Embedding and storing vectors
  Embedding and indexing chunks... 100% 0:00:22

Ingest complete! 84 chunks stored.
```

### 5. Start the API

```bash
uvicorn app.main:app --reload
```

API docs available at **http://localhost:8000/docs**

---

## Demo: Ask the Agent

### Via curl

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our refund policy for annual enterprise customers?"}'
```

### Sample Questions

| Question | What it demonstrates |
|----------|----------------------|
| "What is our refund policy for annual enterprise customers?" | Policy retrieval + citation |
| "Draft a support reply for a customer who cannot log in." | Document-grounded reply drafting |
| "Summarize recurring complaints from the latest support tickets." | Multi-doc synthesis from CSV data |
| "Which help article should this ticket link to?" | Semantic routing across knowledge base |
| "Is this customer eligible for escalation?" | Policy reasoning + criteria matching |
| "Create a step-by-step troubleshooting guide from our docs." | Cross-document synthesis |

### Example Response

```json
{
  "question": "What is our refund policy for annual enterprise customers?",
  "answer": "Enterprise customers on annual contracts are eligible for a full refund within 14 days of contract signing. Between 14 and 90 days, a prorated refund is available subject to a 10% early-termination fee. Beyond 90 days, refunds are handled on a case-by-case basis by the Enterprise Success team. To request a refund, email billing@nirvanacloud.io with your account ID and reason.",
  "sources": ["refund_policy.md"],
  "latency_ms": 1842.5,
  "model": "gpt-4o-mini"
}
```

---

## Benchmarks

Run the benchmarks yourself:

```bash
# Ingest throughput (chunks/sec)
python -m benchmarks.ingest_benchmark

# Retrieval latency (p50/p95/p99)
python -m benchmarks.retrieval_latency_benchmark
```

See `benchmarks/sample_results.md` for results collected on Nirvana Cloud.

**Headline result**: Qdrant on Nirvana ABS NVMe delivers **~60% lower p99 retrieval
latency** vs. NFS-backed storage (203ms vs. 487ms). At 1M+ vectors, the gap widens
further as the HNSW index no longer fits in RAM and storage latency dominates.

---

## Deploy on Nirvana Cloud

See [`infra/deploy_on_nirvana.md`](infra/deploy_on_nirvana.md) for a complete deployment guide.

The short version:
1. Create a VM (`standard-4` or higher)
2. Create an ABS NVMe volume and mount it at `/data/qdrant`
3. Run Qdrant with the volume bound to `/data/qdrant`
4. Run the ingest pipeline and start the API server

---

## Project Structure

```
langchain-support-agent-demo/
  README.md                        ← you are here
  docker-compose.yml               ← Qdrant container
  .env.example                     ← environment variables template
  requirements.txt                 ← Python dependencies

  app/
    config.py                      ← Pydantic settings (reads from .env)
    ingest.py                      ← document → chunk → embed → Qdrant
    retriever.py                   ← cached Qdrant vector retriever
    agent.py                       ← LangChain OpenAI Functions agent
    main.py                        ← FastAPI: GET /health, POST /ask

  data/
    refund_policy.md
    onboarding_guide.md
    help_center_articles/
      billing_faq.md
      vm_management.md
      escalation_policy.md
    sample_tickets.csv

  benchmarks/
    ingest_benchmark.py            ← throughput benchmark
    retrieval_latency_benchmark.py ← p50/p95/p99 latency benchmark
    sample_results.md              ← results from Nirvana Cloud

  infra/
    deploy_on_nirvana.md           ← step-by-step deployment guide
    volume_setup.md                ← ABS volume sizing and backup
```

---

## Tech Stack

| Component       | Choice                 | Why                                          |
|-----------------|------------------------|----------------------------------------------|
| API framework   | FastAPI                | Fast, auto-docs via Swagger, Pydantic-native |
| Agent framework | LangChain              | Best-in-class tooling for RAG agents         |
| LLM             | gpt-4o-mini            | Fast, cost-effective, deterministic at temp=0|
| Embeddings      | text-embedding-3-small | Great quality/cost ratio, 1536 dims          |
| Vector DB       | Qdrant                 | Self-hostable, Docker-native, HNSW-on-disk   |
| Config          | Pydantic Settings v2   | Type-safe, .env support out of the box       |
| Infra           | Nirvana Cloud VM + ABS | Purpose-built for stateful AI workloads      |

---

LangChain gives developers the agent framework. Nirvana Cloud gives those agents the fast, predictable infrastructure layer they need in production.
