# Hosting a Vector Database on Nirvana Cloud

Vector databases are I/O-intensive: they maintain large HNSW or IVF indexes that
must be read from disk during similarity search. Nirvana ABS NVMe volumes are
purpose-built for this workload.

## Qdrant

The recommended self-hosted vector database for Nirvana deployments.

### Quick Setup (Docker)

```bash
docker run -d --name qdrant   -p 6333:6333   -v /data/qdrant:/qdrant/storage   qdrant/qdrant:latest
```

Mount Qdrant storage on an ABS NVMe volume (`/data/qdrant`) for 10,000+ IOPS.

### Sizing Guide

| Vectors | Dimensions | Index Size | Recommended Volume |
|---------|-----------|------------|-------------------|
| 100K | 384 | ~150 MB | 10 GB SSD |
| 1M | 384 | ~1.5 GB | 50 GB SSD |
| 10M | 384 | ~15 GB | 200 GB NVMe |
| 100M | 1536 | ~600 GB | 1 TB NVMe |

### Taking Snapshots

```bash
curl -X POST "http://localhost:6333/collections/my_collection/snapshots"
```

Store the resulting `.tar` file in Nirvana Object Storage for backup.

## Weaviate

```bash
docker run -d --name weaviate   -p 8080:8080   -v /data/weaviate:/var/lib/weaviate   semitechnologies/weaviate:latest
```

## Milvus

```bash
docker compose up -d  # using Milvus's official docker-compose.yml
```

## Performance Tuning

- **NVMe mount**: `sudo mount -o noatime,nodiratime /dev/nvme0n1 /data`
- **Readahead**: `sudo blockdev --setra 256 /dev/nvme0n1`
- **Huge pages**: `echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages`

## Recommended Instance for Qdrant

For 10M vectors at 384 dims: `standard-8` with a 200 GB ABS NVMe volume.
