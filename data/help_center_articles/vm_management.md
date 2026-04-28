# VM Management Guide

## Stopping vs. Deleting a VM

- **Stop**: The VM is powered off. You are NOT charged for compute, but storage and
  reserved IPs continue to incur charges.
- **Delete**: All associated resources are released. This action is irreversible.
  Volumes must be detached before deletion unless you choose to delete them together.

## Resizing a VM

1. Stop the VM.
2. Navigate to **VM Settings → Resize**.
3. Select the new instance type.
4. Restart the VM.

Note: You can resize to a larger instance at any time. Downsizing is subject to
resource availability in the region.

## Snapshots

Snapshots capture the full disk state of a VM at a point in time.

- Creating a snapshot: **VM Actions → Take Snapshot**
- Restoring from a snapshot: **Storage → Snapshots → Restore**
- Snapshots are billed at $0.05/GB/month.

## GPU Instances

GPU instances are available in the following configurations:

- `gpu-small`: 1x NVIDIA A10G, 16 GB VRAM, 8 vCPUs, 32 GB RAM
- `gpu-medium`: 2x NVIDIA A10G, 32 GB VRAM, 16 vCPUs, 64 GB RAM
- `gpu-large`: 8x NVIDIA A100, 320 GB VRAM, 96 vCPUs, 768 GB RAM

GPU instances are ideal for model training, inference serving, and vector database hosting.

## Networking

- Each VM gets a private IP in your VPC and an optional public IP.
- Public IPs are static and persist across stop/start cycles.
- Inbound traffic is free. Outbound is charged at $0.09/GB after the first 100 GB/month.

## SSH Key Management

SSH keys must be associated with a VM at creation time. To change the SSH key on an
existing VM, you must stop the VM, take a snapshot, create a new VM from that snapshot,
and add the new key during creation.

## Firewall Rules

Each VM has its own firewall. Default rules block all inbound traffic except port 22 (SSH).
To open additional ports (e.g., 80 for HTTP, 8000 for an API), navigate to
**VM Settings → Firewall → Add Rule**.
