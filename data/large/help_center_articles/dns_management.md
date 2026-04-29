# DNS Management

Nirvana Cloud provides a managed DNS service supporting both public and private zones.

## Public DNS Zones

1. Navigate to **Networking → DNS → + Create Zone**.
2. Enter your domain (e.g., `example.com`).
3. Nirvana provides four authoritative nameservers — update your registrar's NS records.
4. Add records (A, AAAA, CNAME, MX, TXT, SRV) from the zone editor.

## Record Types

| Type  | Use case |
|-------|----------|
| A     | Map hostname to IPv4 address |
| AAAA  | Map hostname to IPv6 address |
| CNAME | Alias one hostname to another |
| MX    | Mail exchange records |
| TXT   | Domain ownership verification, SPF, DKIM |
| SRV   | Service discovery |

## Private DNS Zones

For internal hostnames resolvable only within a VPC:

1. Navigate to **Networking → Private DNS → + Create Zone**.
2. Specify the zone name (e.g., `internal.example.com`).
3. Associate it with one or more VPCs.
4. Add records pointing to private IPs.

VMs in the associated VPCs can resolve these hostnames without any additional configuration.

## TTL Recommendations

- Public records: 300 seconds (5 min) for frequently changing IPs; 3600 for stable ones.
- Private records: 60 seconds for service-discovery use cases.

## Propagation

DNS changes propagate globally within 30–120 seconds on the Nirvana network.
External resolvers may cache the old TTL value until it expires.

## Troubleshooting

- **Records not resolving**: Check nameserver delegation at your registrar.
- **Internal DNS not working**: Confirm the VPC is associated with the private zone.
- **DNSSEC errors**: Enable DNSSEC under zone settings and add the DS record at your registrar.
