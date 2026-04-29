# Backup & Restore

## Automated VM Backups

Enable daily backups on a VM:
1. **VM Settings → Backups → Enable Automatic Backups**.
2. Choose a retention period (7, 14, or 30 days).
3. Backups run daily at the scheduled time (default: 02:00 in the VM's region).

Backups capture the full disk state. Restore creates a new VM from the backup.

## Manual Snapshots

Create an on-demand snapshot at any time:
**VM Actions → Take Snapshot**.

Recommended before:
- Resizing a VM
- Major OS upgrades
- Deploying significant software changes

## Restoring a VM from Backup

1. Navigate to **Storage → Snapshots**.
2. Select the snapshot → **Restore as New VM**.
3. Choose instance type and region (can differ from the original).
4. The new VM boots from the snapshot's disk state.

## Volume-Level Backups

For granular backup of a single attached volume:
1. **Storage → Volumes → [Volume] → Snapshots → + Take Snapshot**.
2. Restore by creating a new volume from the snapshot.

## Qdrant Snapshot Backups (Vector DB)

Qdrant's snapshot API saves the index state:
```bash
curl -X POST "http://localhost:6333/collections/my_collection/snapshots"
```
Upload the resulting `.tar` file to Nirvana Object Storage for off-site storage.

## Cross-Region Disaster Recovery

1. Take a snapshot in region A.
2. Copy it to region B: **Snapshot → Copy to Region**.
3. In region B, restore from the copied snapshot.

RTO: 5–15 minutes. RPO: time since last backup.

## Backup Pricing

- Snapshots: $0.05/GB/month
- Automated backup storage: $0.04/GB/month (compressed)
