# Migrating from GCP to Nirvana Cloud

## Service Mapping

| GCP | Nirvana Cloud |
|-----|--------------|
| Compute Engine | VM |
| Persistent Disk SSD | Performance SSD Volume |
| GCS | Object Storage |
| Cloud SQL | Self-hosted PostgreSQL/MySQL on VM |
| Cloud Load Balancing | Layer 4/7 Load Balancer |
| VPC | VPC |
| Cloud DNS | DNS Management |
| IAM | IAM & Access Control |
| Cloud Monitoring | Monitoring & Alerts |
| GKE | Nirvana Kubernetes Service |
| Artifact Registry | Nirvana Container Registry |

## Migrating Compute Engine VMs

1. Create a machine image from the running instance in GCP Console.
2. Export the image to a GCS bucket in VMDK or raw format.
3. Download the image from GCS.
4. Upload to Nirvana: **Storage → Import Image → Upload VMDK**.
5. Create a VM from the imported image.

## Migrating GCS Buckets

Use `gcloud storage` and `rclone`:
```bash
rclone copy gcs:my-bucket nirvana:my-bucket   --transfers 16 --checkers 32 --progress
```

## Migrating Cloud SQL (PostgreSQL)

1. Use `pg_dump` to export the database.
2. Transfer the dump to a Nirvana VM.
3. Restore with `pg_restore`.
4. For near-zero downtime, set up logical replication before cutover.

## Network Migration

GCP's global VPC differs from Nirvana's regional VPC model. Plan accordingly:
- Nirvana VPCs are regional; create one per region.
- Use VPC Peering for cross-region communication.

## Timeline

A typical migration of 50 VMs and 10 TB data takes 2–4 weeks:
- Week 1: Planning and tooling setup
- Week 2: Test migration of non-production workloads
- Week 3: Production migration in waves
- Week 4: Cutover, validation, and decommission

## Support

Nirvana's migration team provides free assistance for migrations from major clouds.
Contact sales@nirvanacloud.io to schedule a migration call.
