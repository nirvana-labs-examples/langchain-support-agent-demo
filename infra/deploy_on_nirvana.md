# Deploying on Nirvana Cloud

This guide walks through deploying the support agent on a Nirvana Cloud VM
with Qdrant backed by Nirvana ABS (Attached Block Storage).

## Why This Architecture Matters

Qdrant stores its HNSW vector index on disk. The speed of that disk directly affects:

- **Ingest throughput**: index construction requires high-IOPS random writes
- **Query latency**: index traversal requires random reads (partially cached in RAM)
- **Recovery time**: after a restart, Qdrant loads the full index from disk

Nirvana ABS NVMe volumes provide **10,000–100,000 IOPS** and sub-millisecond
latency — purpose-built for stateful AI workloads like vector databases.

## Step 1: Create a VM

From the Nirvana Cloud dashboard or CLI:

```
Instance type: standard-4 (4 vCPUs, 16 GB RAM) — minimum recommended
OS: Ubuntu 22.04 LTS
Region: choose closest to your users
```

For production or high-traffic deployments, use `standard-8` or `gpu-small`.

## Step 2: Create and Attach a Volume

In the dashboard: **Storage → Volumes → Create Volume**

```
Size: 50 GB (sufficient for up to ~8M vectors)
Type: NVMe
IOPS: 10,000 baseline
```

After creation, attach the volume to your VM.

SSH into the VM and mount the volume:

```bash
sudo mkfs.ext4 /dev/vdb
sudo mkdir -p /data/qdrant
sudo mount /dev/vdb /data/qdrant

# Make persistent across reboots
echo '/dev/vdb /data/qdrant ext4 defaults 0 2' | sudo tee -a /etc/fstab
```

## Step 3: Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

## Step 4: Install uv and Clone the Repository

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Clone the repo
git clone https://github.com/nirvana-labs-examples/langchain-support-agent-demo.git
cd langchain-support-agent-demo
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY
```

## Step 5: Bind Qdrant Storage to the ABS Volume

Edit `docker-compose.yml` to replace the named volume with a bind mount:

```yaml
volumes:
  qdrant_storage:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/qdrant
```

This directs Qdrant to write its HNSW index directly to the NVMe volume.

## Step 6: Start Services

```bash
# Start Qdrant
docker compose up -d qdrant

# Install Python dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Ingest the knowledge base
python -m app.ingest --recreate

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Step 7: Open Firewall Rules

In the Nirvana Cloud dashboard, navigate to your VM's **Firewall** settings and add:

| Port | Protocol | Description        |
|------|----------|--------------------|
| 8000 | TCP      | Support Agent API  |
| 6333 | TCP      | Qdrant REST/Web UI (optional, restrict to your IP) |

## Step 8: Run Benchmarks

```bash
python -m benchmarks.ingest_benchmark
python -m benchmarks.retrieval_latency_benchmark
```

Compare results to `benchmarks/sample_results.md` to validate your setup.

## Running as a Service

To keep the API running after SSH disconnect, use `systemd` or `screen`:

```bash
# Simple approach with screen
screen -S support-agent
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Ctrl+A, D to detach
```
