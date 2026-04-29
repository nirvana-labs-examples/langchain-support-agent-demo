# Advanced Firewall Configuration

## Default Rules

Every VM starts with these default firewall rules:
- **Inbound**: Allow TCP 22 (SSH) from anywhere
- **Outbound**: Allow all traffic

## Adding Rules

**Dashboard**: VM Settings → Firewall → + Add Rule.

**API**:
```bash
curl -X POST https://api.nirvanacloud.io/v1/vms/<vm-id>/firewall-rules   -H "Authorization: Bearer <api-key>"   -d '{"direction":"inbound","protocol":"tcp","port":443,"source":"0.0.0.0/0"}'
```

## Source Filtering

Restrict access by IP range:
- Single IP: `203.0.113.42/32`
- CIDR range: `10.0.0.0/24`
- Anywhere: `0.0.0.0/0` (IPv4) or `::/0` (IPv6)
- Another VPC: use its CIDR block

## Security Groups (Enterprise)

A security group is a reusable set of firewall rules that can be applied to
multiple VMs:

1. **Networking → Security Groups → + Create**.
2. Define inbound and outbound rules.
3. Attach to VMs at creation time or via **VM Settings → Security Groups**.

Changes to a security group apply instantly to all attached VMs.

## Network ACLs

Applied at the subnet level, before security groups:
- Stateless (must explicitly allow return traffic)
- Support allow and deny rules
- Applied in order (lowest rule number first)

**Networking → Subnets → [Subnet] → Network ACL → Edit**.

## Logging Dropped Packets

Enable firewall logging to debug connectivity issues:
**VM Settings → Firewall → Enable Logging**.
Logs appear in **Monitoring → Log Explorer** under the `firewall` source.

## Common Configurations

| Use Case | Inbound Rules |
|----------|--------------|
| Web server | TCP 80, TCP 443 from 0.0.0.0/0 |
| API server (internal only) | TCP 8000 from VPC CIDR |
| Database | TCP 5432 from app subnet only |
| Redis | TCP 6379 from app subnet only |
