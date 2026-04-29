# Redis on Nirvana Cloud

## Why Redis on Nirvana?

Self-hosting Redis on a Nirvana VM gives you:
- Full control over configuration and memory limits
- Persistent storage on ABS NVMe (sub-millisecond disk writes for AOF)
- No data leaving your VPC

## Installation

```bash
sudo apt update && sudo apt install -y redis-server
sudo systemctl enable --now redis-server
```

Configure to listen on the private IP only:
```ini
# /etc/redis/redis.conf
bind 0.0.0.0        # or bind to specific private IP
requirepass your_strong_password
maxmemory 8gb
maxmemory-policy allkeys-lru
```

## Persistence Options

| Mode | Description | Recommended For |
|------|-------------|-----------------|
| No persistence | In-memory only | Pure cache, ephemeral data |
| RDB snapshots | Periodic dump to disk | Cache with acceptable data loss |
| AOF | Append-only log | Session store, queues |
| RDB + AOF | Both | Mission-critical data |

For AOF on ABS NVMe, set `appendfsync everysec` — the NVMe latency makes this
nearly as fast as `no` with much better durability.

## Replication

```ini
# On replica:
replicaof primary_ip 6379
masterauth your_strong_password
```

## Sentinel (High Availability)

Run 3 Sentinel processes (one per VM) to monitor the primary and promote a replica
automatically on failure:

```bash
redis-sentinel /etc/redis/sentinel.conf
```

## Firewall

Redis listens on port 6379. Restrict access to your application VMs only.
Never expose Redis publicly without auth and TLS.

## Monitoring

Redis exports metrics via INFO command. Use the Prometheus `redis_exporter`
sidecar and push to Nirvana Monitoring for CPU, memory, and hit-rate dashboards.
