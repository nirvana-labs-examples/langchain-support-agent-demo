# Nirvana File Storage (NFS)

Nirvana File Storage provides a fully managed NFS share accessible by multiple VMs
simultaneously — useful for shared configuration, shared ML datasets, or collaborative
workloads.

## Creating a File System

1. Navigate to **Storage → File Systems → + Create**.
2. Enter a name and select a VPC.
3. Choose performance tier:
   - **Burst**: Up to 100 MB/s per TB stored. Good for sporadic access.
   - **Provisioned**: Fixed throughput up to 1 GB/s. Good for continuous workloads.
4. Set initial capacity (minimum 100 GB; expands automatically as needed).

## Mounting on Linux

```bash
sudo apt install -y nfs-common
sudo mkdir /shared
sudo mount -t nfs4 <file-system-dns>:/ /shared -o nfsvers=4.1,rsize=1048576,wsize=1048576
```

For persistent mounts, add to `/etc/fstab`:
```
<file-system-dns>:/ /shared nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576 0 0
```

## Permissions

File Storage uses POSIX permissions. All VMs in the VPC can mount the share.
Use standard `chmod` and `chown` to control access within the mounted directory.

## Performance Tips

- Mount with `rsize=1048576,wsize=1048576` for large sequential I/O.
- Avoid NFS for high-IOPS random workloads (databases) — use Block Storage instead.
- Co-locate File Storage and VMs in the same region.

## Use Cases

- Shared model weights for a cluster of inference VMs
- Shared training data for distributed ML jobs
- Configuration files for a multi-VM application

## Pricing

- Burst tier: $0.08/GB/month
- Provisioned tier: $0.16/GB/month + $0.01/MB-s provisioned throughput/month
