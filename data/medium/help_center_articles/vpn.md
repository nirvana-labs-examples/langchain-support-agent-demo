# Private Networking & VPN

## Site-to-Site VPN

Connect your on-premises network to a Nirvana VPC:

1. **Networking → VPN → + Create VPN Gateway**.
2. Configure the customer gateway (your on-premises router's public IP and ASN).
3. Download the configuration file for your router (supports Cisco, Juniper, pfSense, strongSwan).
4. Apply the config on your router. The tunnel establishes automatically.

**Supported protocols**: IKEv1 and IKEv2 with AES-256 / SHA-256.

## Client VPN (WireGuard)

Allow individual developers to access VPC resources without exposing a public IP:

1. **Networking → Client VPN → + Create Endpoint**.
2. Select the VPC and subnet.
3. Invite users — they receive a WireGuard configuration file.
4. Users install the WireGuard app and import the config. Connection is one click.

## Private Link

Expose a service (e.g., a database or internal API) to another Nirvana account
without VPC peering or public internet:

1. Provider creates a **Private Link Service** attached to a load balancer.
2. Consumer creates a **Private Link Endpoint** pointing to the service.
3. Traffic stays on the Nirvana backbone — never touches the public internet.

## Bastion Host Alternative

Instead of a bastion, use the Nirvana SSH proxy:
```bash
nirvana ssh <vm-name>
```
This opens an SSH tunnel via the Nirvana control plane. No public IP required on
the target VM.

## Troubleshooting

- **VPN tunnel down**: Check Phase 1/Phase 2 IKE settings match on both sides.
- **Cannot ping across tunnel**: Verify route table entries and firewall rules on both ends.
- **High latency**: Consider VPC peering if both sides are in Nirvana (lower overhead).
