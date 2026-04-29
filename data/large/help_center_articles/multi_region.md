# Multi-Region Setup

## Available Regions

| Region | Location | Notes |
|--------|----------|-------|
| us-east-1 | Virginia, USA | Largest capacity, lowest latency to US East |
| us-west-1 | Oregon, USA | Low latency to US West and Asia-Pacific |
| eu-west-1 | Dublin, Ireland | EU data residency available |
| eu-central-1 | Frankfurt, Germany | German DSGVO compliance |
| ap-south-1 | Mumbai, India | Covers South and Southeast Asia |
| ap-east-1 | Singapore | Southeast Asia hub |

## Global Load Balancing

Route user traffic to the nearest healthy region using Nirvana Global Load Balancer:

1. **Networking → Global Load Balancer → + Create**.
2. Add regional endpoints (each backed by a regional load balancer).
3. Choose routing policy: **Latency-based** (default) or **Geo-based**.
4. Attach a Nirvana-managed domain or CNAME to the GLB endpoint.

## Data Replication

**Object storage**: Enable cross-region replication under **Bucket Settings →
Replication → + Add Rule**. Objects sync within 15 minutes.

**Databases**: Use streaming replication (PostgreSQL) or native replication to
maintain a read replica in a second region.

## Failover Architecture

Example: primary in us-east-1, standby in eu-west-1.

1. Primary region handles all traffic.
2. Standby keeps a warm replica (DB replica + idle VMs).
3. On failure: update DNS TTL to 60s before an incident, then point to eu-west-1.

RTO with DNS failover: 60–120 seconds.

## Latency Benchmarks

Typical inter-region latency (round trip):
- us-east-1 ↔ eu-west-1: ~80 ms
- us-east-1 ↔ ap-south-1: ~160 ms
- eu-west-1 ↔ ap-east-1: ~170 ms

## Cost Considerations

Data transferred between regions is billed at $0.02/GB. Design your architecture
to minimise cross-region traffic — keep data and compute co-located where possible.
