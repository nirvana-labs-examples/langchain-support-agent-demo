# Running PostgreSQL on Nirvana Cloud

## Recommended Setup

For production workloads, run PostgreSQL on a **Performance SSD** or **ABS NVMe** volume
to handle high write IOPS.

### Instance Recommendation

| Use case | Instance type | Volume |
|----------|--------------|--------|
| Dev/staging | standard-2 | 50 GB SSD |
| Small production | standard-4 | 200 GB Performance SSD |
| High-traffic production | standard-8 | 500 GB ABS NVMe |
| Very high write load | standard-16 | 1 TB ABS NVMe |

## Installation

```bash
sudo apt update && sudo apt install -y postgresql-15
sudo systemctl enable --now postgresql
```

## Data Directory on Attached Volume

Move PostgreSQL data to the attached NVMe volume for better I/O:

```bash
sudo systemctl stop postgresql
sudo rsync -av /var/lib/postgresql/ /data/postgresql/
# Edit /etc/postgresql/15/main/postgresql.conf:
# data_directory = '/data/postgresql/15/main'
sudo systemctl start postgresql
```

## Key Configuration Tuning

```ini
# postgresql.conf
shared_buffers = 4GB          # 25% of RAM
effective_cache_size = 12GB   # 75% of RAM
work_mem = 64MB
wal_buffers = 64MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1        # for SSD/NVMe (default 4.0 is for spinning disk)
```

## Streaming Replication

Set up a hot-standby replica in another region:

```bash
# On primary:
pg_basebackup -h primary_ip -U replicator -D /data/postgresql -P -Xs -R
```

## Backups

Use `pgdump` for logical backups, or Nirvana volume snapshots for physical backups.
Schedule daily snapshots under **VM Settings → Backups**.

## Firewall Rules

PostgreSQL listens on port 5432. Add a firewall rule to allow only your app VMs:
**VM Settings → Firewall → + Add Rule → TCP 5432 from app-vm-ip**.
