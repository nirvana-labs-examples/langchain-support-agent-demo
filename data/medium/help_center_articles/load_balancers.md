# Load Balancer Configuration

Nirvana Cloud offers Layer 4 (TCP/UDP) and Layer 7 (HTTP/HTTPS) load balancers.

## Creating a Load Balancer

1. Navigate to **Networking → Load Balancers → + Create**.
2. Choose **Layer 4** (for raw TCP throughput) or **Layer 7** (for HTTP routing and SSL termination).
3. Select the region and VPC.
4. Configure the frontend listener (port and protocol).
5. Add backend VMs to the target group.
6. Set health check parameters.

## Health Checks

- **HTTP health check**: The load balancer sends a GET request to a configurable path
  (default `/health`). A 2xx response marks the VM healthy.
- **TCP health check**: A successful TCP connection marks the VM healthy.
- Unhealthy VMs are automatically removed from rotation and re-added once they recover.

## SSL Termination (Layer 7)

Upload your TLS certificate under **Settings → Certificates** or use Nirvana's
managed certificates (auto-renewed via Let's Encrypt):

1. Add your domain under **Settings → Domains**.
2. When creating the load balancer, select **Managed TLS certificate**.
3. Point your DNS A record to the load balancer's public IP.

## Sticky Sessions

Enable sticky sessions so a client always hits the same backend VM:
- **Layer 7**: Cookie-based stickiness; configure the cookie name and TTL.
- **Layer 4**: IP hash-based; no cookie required.

## Pricing

Load balancers are billed at $0.015/hour plus $0.008/GB of data processed.

## Common Issues

- **502 Bad Gateway**: Backend VMs are unhealthy or not listening on the target port.
- **High latency**: Check that backend VMs are in the same region as the load balancer.
- **SSL errors**: Verify the certificate covers the domain and is not expired.
