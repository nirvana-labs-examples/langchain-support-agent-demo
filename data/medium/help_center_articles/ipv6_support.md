# IPv6 Support

## Enabling IPv6 on a VPC

1. Navigate to **VPC Settings → IPv6 → Enable**.
2. Nirvana assigns a `/56` IPv6 prefix to the VPC.
3. Each subnet receives a `/64` from the VPC prefix.
4. VMs in IPv6-enabled subnets receive an IPv6 address automatically.

## Dual Stack

VMs with IPv6 enabled are dual-stack — they have both an IPv4 and an IPv6 address.
Services can listen on both:

```bash
# Python: bind to :: to listen on both IPv4 and IPv6
uvicorn app:main --host :: --port 8000
```

## Firewall Rules for IPv6

Add firewall rules separately for IPv6 traffic:
- IPv4 source: `0.0.0.0/0`
- IPv6 source: `::/0`

Both rules are required to allow traffic from all internet clients.

## Public IPv6 Addresses

IPv6 addresses on Nirvana are publicly routable by default (no NAT).
All addresses in the `/64` subnet are reachable from the internet.
Use firewall rules to restrict access.

## IPv6 in DNS

Add AAAA records for your services to DNS:
```
api.example.com.  300  IN  AAAA  2001:db8::1
```

## Common Issues

- **IPv6 not working on VM**: Ensure the OS has the IPv6 interface configured
  (`ip -6 addr show`). Most modern Linux distributions configure it automatically.
- **Services not listening on IPv6**: Check the bind address in your application config.
- **Firewall blocking IPv6**: Verify `::/0` rules are present alongside `0.0.0.0/0`.
