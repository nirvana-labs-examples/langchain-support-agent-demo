# Nirvana ABS Volume Setup for Qdrant

## Overview

Qdrant persists its HNSW vector index in the directory pointed to by
`storage.storage_path` (default: `./storage`). This is mapped to the Docker
volume `qdrant_storage` in `docker-compose.yml`.

By binding that volume to a Nirvana ABS NVMe volume, Qdrant gets direct access
to high-IOPS, low-latency block storage — the same storage layer that makes
Nirvana Cloud well-suited for production AI agent workloads.

## Volume Sizing Guide

| Collection size  | Vectors    | Recommended size |
|------------------|------------|------------------|
| Small demo       | < 10K      | 10 GB            |
| Medium           | 10K–500K   | 50 GB            |
| Large production | 500K–5M    | 200 GB           |
| Enterprise       | 5M+        | 1 TB+, striped   |

**Rule of thumb**: each vector (1536 dims, float32) takes ~6 KB including HNSW
graph edges. 1 million vectors ≈ 6 GB on disk.

## IOPS Requirements

| Workload         | Recommended IOPS |
|------------------|------------------|
| Ingest-heavy     | 10,000+          |
| Query-heavy      | 3,000+           |
| Mixed            | 6,000+           |

## Creating the Volume (Nirvana Cloud Dashboard)

1. Navigate to **Storage → Volumes → Create Volume**
2. Set name: `qdrant-data`
3. Set size: 50 GB (adjust per sizing guide above)
4. Set type: NVMe
5. Click **Create**
6. Navigate to your VM → **Attached Volumes → Attach** → select `qdrant-data`

## Binding the Docker Volume

Edit `docker-compose.yml` to use a bind mount instead of a named volume:

```yaml
volumes:
  qdrant_storage:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/qdrant  # must be the mount point of your ABS volume
```

## Backup and Snapshots

### Qdrant Snapshot API

Create a snapshot of the collection (stored inside the Qdrant container):

```bash
curl -X POST "http://localhost:6333/collections/support_docs/snapshots"
```

List snapshots:

```bash
curl "http://localhost:6333/collections/support_docs/snapshots"
```

### Volume Snapshots via Nirvana Cloud

For full disaster recovery, snapshot the entire ABS volume from the dashboard:

**Storage → Volumes → [your volume] → Take Snapshot**

Snapshots are stored redundantly and can be used to create a new volume if
the original is lost. Billed at $0.05/GB/month.

### Offsite Backup to Nirvana Object Storage

```bash
# Install the AWS CLI (Nirvana Object Storage is S3-compatible)
pip install awscli

# Configure with your Nirvana Object Storage credentials
aws configure --profile nirvana

# Upload the latest Qdrant snapshot
aws s3 cp /data/qdrant/snapshots/ s3://your-bucket/qdrant-backups/ \
  --recursive --profile nirvana \
  --endpoint-url https://storage.nirvanacloud.io
```
