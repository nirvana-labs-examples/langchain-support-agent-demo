# Network Pricing

## Inbound Traffic

All inbound traffic to Nirvana Cloud is **free** — no ingress charges.

## Outbound Traffic (Egress)

| Destination | Price |
|-------------|-------|
| Same region (VM to VM in same VPC) | Free |
| Same region (VM to VM in different VPC) | Free |
| Different Nirvana region | $0.02/GB |
| Internet (first 100 GB/month) | Free |
| Internet (after 100 GB/month) | $0.09/GB |

## Load Balancer Data Processing

- $0.008/GB for all data processed (inbound + outbound)

## VPN Traffic

- Site-to-site VPN: $0.05/GB for data transferred over the tunnel
- Client VPN: $0.05/GB per active VPN connection-hour

## DNS Queries

- First 1 billion queries/month: $0.40 per million queries
- Over 1 billion: $0.20 per million queries

## Free Data Transfer Use Cases

These are never charged for egress:
- Traffic between VMs in the same VPC
- Traffic to Nirvana Object Storage in the same region
- Traffic to the Nirvana API (api.nirvanacloud.io)
- Traffic within a Kubernetes cluster

## Tips to Reduce Egress Costs

1. Keep compute and storage in the same region.
2. Use a CDN (Nirvana CDN) to serve static assets — CDN-to-user traffic is
   cheaper than VM-to-user.
3. Compress data before transferring across regions.
4. Use Nirvana Object Storage cross-region replication only for critical data.

## Estimating Your Bill

Use the pricing calculator at nirvanacloud.io/pricing to estimate costs
based on your expected resource usage and data transfer patterns.
