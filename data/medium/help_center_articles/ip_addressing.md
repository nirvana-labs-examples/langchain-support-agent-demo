# IP Addressing & Public IPs

## Private IPs

Every VM receives a private IP from its subnet's CIDR block. Private IPs:
- Are stable across stop/start cycles
- Are not reachable from the public internet
- Are used for VM-to-VM communication within the VPC

## Public IPs

A public IP makes your VM reachable from the internet.

### Assigning a Public IP

When creating a VM, enable **Assign Public IP** in the network settings.
Alternatively, attach a floating IP to an existing VM.

### Floating IPs

A floating IP is a static public IP that can be moved between VMs:

1. **Networking → Floating IPs → + Create**.
2. Associate with a VM: **Floating IP → Assign → Select VM**.
3. Reassign instantly during failover.

Useful for blue/green deployments — point the floating IP at the new VM before
decommissioning the old one.

### IPv6

Enable IPv6 at the VPC level: **VPC Settings → Enable IPv6**.
Each VM in the VPC receives a `/128` IPv6 address automatically.

## Reverse DNS (PTR Records)

Set custom reverse DNS on public IPs:
**Networking → Floating IPs → [IP] → Set Reverse DNS**.

Required for mail servers (SMTP rejection is common without a valid PTR record).

## IP Allocation

Nirvana allocates IPs from its own CIDR blocks. If you need to bring your own
IP addresses (BYOIP), contact sales@nirvanacloud.io.

## Pricing

- Private IPs: included
- Public IP (attached to a running VM): $0.005/hour
- Floating IP (unattached): $0.005/hour
- Floating IP (attached): included in VM's public IP cost
