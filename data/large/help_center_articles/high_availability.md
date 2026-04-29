# High Availability Patterns

## What "High Availability" Means on Nirvana

Nirvana provides building blocks for HA; you design the pattern that fits your
availability target. Common SLA targets:

| Pattern | Achievable Uptime | Complexity |
|---------|------------------|------------|
| Single VM + daily backup | ~99.5% | Low |
| Active-passive failover | ~99.9% | Medium |
| Active-active multi-zone | ~99.95% | High |
| Active-active multi-region | ~99.99% | Very high |

## Active-Passive Failover

1. Run two identical VMs in different availability zones.
2. Assign a floating IP to the primary.
3. Monitor the primary with an external health check.
4. On failure, reassign the floating IP to the standby (API call, ~10 seconds).

## Active-Active with Load Balancer

1. Create a load balancer with both VMs as backends.
2. Enable health checks — traffic routes only to healthy VMs.
3. On VM failure, the load balancer removes it from rotation automatically.
4. Scale out by adding more VMs to the target group.

## Stateful Services

For databases and caches:
- Use primary-replica replication.
- Promote a replica automatically via a health-check script or a tool like Patroni (PostgreSQL).

## Qdrant High Availability

Qdrant supports distributed mode:
```yaml
# docker-compose.yml (3-node cluster)
services:
  qdrant_node1:
    image: qdrant/qdrant
    command: ./qdrant --cluster-enabled true --cluster-p2p-host qdrant_node1
  qdrant_node2: ...
  qdrant_node3: ...
```

Shards are replicated across nodes. A node failure does not interrupt search.

## Health Check Endpoints

Add a `/health` endpoint to every service:
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

The load balancer polls this endpoint every 10 seconds and removes unhealthy instances.
