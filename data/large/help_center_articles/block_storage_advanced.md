# Block Storage — Advanced Topics

## Volume Types

| Type | Max IOPS | Max Throughput | Best For |
|------|----------|----------------|----------|
| Standard HDD | 500 | 100 MB/s | Archives, cold data |
| Standard SSD | 3,000 | 250 MB/s | General workloads |
| Performance SSD | 16,000 | 500 MB/s | Databases, high-IOPS |
| ABS NVMe | 100,000+ | 4 GB/s | Vector DBs, ML training |

## Multi-Attach

Attach a single volume to up to 4 VMs simultaneously (read-write on each).
Requires a cluster-aware filesystem (GFS2, OCFS2) — EXT4 is not safe with multi-attach.

Enable: **Volume Settings → Multi-Attach → Enable**.

## Volume Encryption

All volumes are encrypted at rest by default using AES-256.

For customer-managed encryption keys (CMEK):
1. Create a key in **Settings → Key Management**.
2. When creating a volume, select **Customer-managed key** and choose the key.
3. You control key rotation and revocation.

## IOPS Provisioning

For Performance SSD volumes, provision dedicated IOPS:
- Navigate to **Volume Settings → Provisioned IOPS**.
- Valid range: 3 IOPS/GB minimum, up to 16,000 IOPS per volume.
- Billed at $0.065 per provisioned IOPS/month in addition to storage.

## Expanding a Volume

Expand without downtime on Linux:
```bash
# After resizing in the dashboard:
sudo growpart /dev/vdb 1
sudo resize2fs /dev/vdb1   # for ext4
# or:
sudo xfs_growfs /data       # for xfs
```

## Snapshots & Cloning

- **Snapshot**: Point-in-time backup, stored in object storage. Billed at $0.05/GB/month.
- **Clone**: Creates a new independent volume from a snapshot instantly. Full volume price applies.

## Detaching Safely

Always unmount before detaching:
```bash
sudo umount /data
# Then detach in the dashboard
```
Force-detaching a mounted volume can cause data corruption.
