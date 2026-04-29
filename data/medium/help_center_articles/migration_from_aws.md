# Migrating from AWS to Nirvana Cloud

## Planning Your Migration

1. **Inventory**: List all AWS resources (EC2, EBS, S3, RDS, ELB, Route 53).
2. **Map equivalents**: Each AWS service has a direct Nirvana equivalent.
3. **Choose a strategy**: Lift-and-shift (fastest), re-platform, or refactor.

## Service Mapping

| AWS | Nirvana Cloud |
|-----|--------------|
| EC2 | VM |
| EBS (gp3) | Performance SSD Volume |
| EBS (io2) | ABS NVMe Volume |
| S3 | Object Storage |
| RDS | Self-hosted on VM (or bring your own) |
| ALB | Layer 7 Load Balancer |
| NLB | Layer 4 Load Balancer |
| VPC | VPC |
| Route 53 | DNS Management |
| IAM | IAM & Access Control |
| CloudWatch | Monitoring & Alerts |
| EKS | Nirvana Kubernetes Service |
| ECR | Nirvana Container Registry |

## Migrating EC2 Instances

1. Install the Nirvana migration agent on the source EC2 instance.
2. The agent creates a snapshot of the root volume.
3. Import the snapshot into Nirvana: **Storage → Import Snapshot**.
4. Launch a VM from the imported snapshot.

## Migrating S3 Buckets

Use `aws s3 sync` with the Nirvana Object Storage endpoint:
```bash
aws s3 sync s3://my-aws-bucket s3://my-nirvana-bucket   --source-region us-east-1   --endpoint-url https://storage.nirvanacloud.io
```

## Migrating RDS

1. Take an RDS snapshot and export to S3 as Parquet.
2. Restore using `pg_restore` on a Nirvana PostgreSQL VM.
3. For minimal downtime, use logical replication during the cutover window.

## DNS Cutover

1. Lower TTLs to 60s one day before cutover.
2. After verifying Nirvana setup, update A/CNAME records.
3. Monitor for errors; rollback by reverting DNS.
4. After 24 hours, restore normal TTLs.

## Cost Comparison

Most customers see 20–40% cost reduction versus equivalent AWS resources,
primarily from lower VM and storage pricing and no data-egress fees within
the same region.
