# VPC & Networking Setup

## What is a VPC?

A Virtual Private Cloud (VPC) is an isolated network environment within Nirvana Cloud.
All VMs you create are launched inside a VPC and communicate via private IP addresses.

## Creating a VPC

1. Navigate to **Networking → VPCs**.
2. Click **+ Create VPC**.
3. Enter a CIDR block (e.g., `10.0.0.0/16`). This determines the private IP range
   available to VMs in this VPC.
4. Choose a region.
5. Click **Create**.

## Subnets

Divide your VPC into subnets to segment workloads:

- Navigate to **Networking → Subnets → + Create Subnet**.
- Select the parent VPC and specify a sub-CIDR (e.g., `10.0.1.0/24`).
- Assign VMs to subnets at creation time.

## VPC Peering

Connect two VPCs so resources in each can communicate privately:

1. **Networking → VPC Peering → + Create Peering**.
2. Select the two VPCs (can be in different regions).
3. Accept the peering request on the other side if it belongs to a different account.
4. Update route tables in both VPCs to point traffic at the peering connection.

## DNS Resolution

Each VPC includes a private DNS resolver. VM hostnames follow the pattern
`<vm-name>.<vpc-name>.internal`. You can also configure custom DNS zones via
**Networking → Private DNS**.

## Troubleshooting

- **VMs cannot reach each other**: Verify firewall rules allow traffic on the required ports.
- **Cross-VPC traffic fails**: Check that peering is active and route tables are updated.
- **DNS resolution fails**: Confirm the VM is in the correct VPC and DNS is enabled on the subnet.
