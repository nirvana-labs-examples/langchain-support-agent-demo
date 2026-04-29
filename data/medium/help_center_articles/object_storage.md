# Object Storage

Nirvana Object Storage is an S3-compatible blob store for unstructured data: backups,
assets, model weights, logs, and more.

## Creating a Bucket

1. Navigate to **Storage → Object Storage → + Create Bucket**.
2. Choose a region and enter a globally unique bucket name.
3. Set the access policy: **Private** (default) or **Public** (suitable for static assets).

## Uploading Objects

**Via the dashboard**: Drag and drop files into the bucket browser.

**Via the CLI** (AWS CLI compatible):
```bash
aws s3 cp localfile.tar.gz s3://my-bucket/ --endpoint-url https://storage.nirvanacloud.io
```

**Via the API**: Use any S3-compatible SDK (boto3, @aws-sdk/client-s3, etc.) with the
endpoint `https://storage.nirvanacloud.io`.

## Access Keys

Generate object-storage-specific keys under **Settings → Access Keys → + Create Key**.
These are separate from your account password and can be scoped to specific buckets.

## Lifecycle Policies

Automatically transition or delete objects based on age:

1. Open the bucket → **Lifecycle Rules → + Add Rule**.
2. Specify a prefix filter (optional) and a transition action:
   - **Archive** after N days (cheaper, higher retrieval latency).
   - **Delete** after N days.

## Pricing

- Storage: $0.021/GB/month
- Egress: $0.09/GB (first 100 GB/month free per account)
- PUT/COPY/POST requests: $0.005 per 1,000
- GET requests: $0.0004 per 1,000

## Versioning

Enable versioning to retain previous object versions on overwrite or delete:
**Bucket Settings → Versioning → Enable**.

## Common Use Cases

- **Qdrant snapshots**: Store vector-database backups for point-in-time recovery.
- **ML model weights**: Serve large model files to GPU VMs on startup.
- **Static website hosting**: Enable static hosting under Bucket Settings and point
  a CNAME to the bucket URL.
