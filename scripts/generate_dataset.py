"""
Generate the medium dataset into data/medium/.

Copies data/small/ as-is, then adds:
  - 80 additional help center articles covering a broad topic range
  - 2,000 synthetic support tickets

Run:
  python -m scripts.generate_dataset
"""

import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SMALL = ROOT / "data" / "small"
MEDIUM = ROOT / "data" / "medium"

# ---------------------------------------------------------------------------
# Help center articles
# ---------------------------------------------------------------------------

ARTICLES: list[tuple[str, str, str]] = [
    # (filename, title, content)
    (
        "vpc_networking.md",
        "VPC & Networking Setup",
        """\
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
""",
    ),
    (
        "load_balancers.md",
        "Load Balancer Configuration",
        """\
# Load Balancer Configuration

Nirvana Cloud offers Layer 4 (TCP/UDP) and Layer 7 (HTTP/HTTPS) load balancers.

## Creating a Load Balancer

1. Navigate to **Networking → Load Balancers → + Create**.
2. Choose **Layer 4** (for raw TCP throughput) or **Layer 7** (for HTTP routing and SSL termination).
3. Select the region and VPC.
4. Configure the frontend listener (port and protocol).
5. Add backend VMs to the target group.
6. Set health check parameters.

## Health Checks

- **HTTP health check**: The load balancer sends a GET request to a configurable path
  (default `/health`). A 2xx response marks the VM healthy.
- **TCP health check**: A successful TCP connection marks the VM healthy.
- Unhealthy VMs are automatically removed from rotation and re-added once they recover.

## SSL Termination (Layer 7)

Upload your TLS certificate under **Settings → Certificates** or use Nirvana's
managed certificates (auto-renewed via Let's Encrypt):

1. Add your domain under **Settings → Domains**.
2. When creating the load balancer, select **Managed TLS certificate**.
3. Point your DNS A record to the load balancer's public IP.

## Sticky Sessions

Enable sticky sessions so a client always hits the same backend VM:
- **Layer 7**: Cookie-based stickiness; configure the cookie name and TTL.
- **Layer 4**: IP hash-based; no cookie required.

## Pricing

Load balancers are billed at $0.015/hour plus $0.008/GB of data processed.

## Common Issues

- **502 Bad Gateway**: Backend VMs are unhealthy or not listening on the target port.
- **High latency**: Check that backend VMs are in the same region as the load balancer.
- **SSL errors**: Verify the certificate covers the domain and is not expired.
""",
    ),
    (
        "dns_management.md",
        "DNS Management",
        """\
# DNS Management

Nirvana Cloud provides a managed DNS service supporting both public and private zones.

## Public DNS Zones

1. Navigate to **Networking → DNS → + Create Zone**.
2. Enter your domain (e.g., `example.com`).
3. Nirvana provides four authoritative nameservers — update your registrar's NS records.
4. Add records (A, AAAA, CNAME, MX, TXT, SRV) from the zone editor.

## Record Types

| Type  | Use case |
|-------|----------|
| A     | Map hostname to IPv4 address |
| AAAA  | Map hostname to IPv6 address |
| CNAME | Alias one hostname to another |
| MX    | Mail exchange records |
| TXT   | Domain ownership verification, SPF, DKIM |
| SRV   | Service discovery |

## Private DNS Zones

For internal hostnames resolvable only within a VPC:

1. Navigate to **Networking → Private DNS → + Create Zone**.
2. Specify the zone name (e.g., `internal.example.com`).
3. Associate it with one or more VPCs.
4. Add records pointing to private IPs.

VMs in the associated VPCs can resolve these hostnames without any additional configuration.

## TTL Recommendations

- Public records: 300 seconds (5 min) for frequently changing IPs; 3600 for stable ones.
- Private records: 60 seconds for service-discovery use cases.

## Propagation

DNS changes propagate globally within 30–120 seconds on the Nirvana network.
External resolvers may cache the old TTL value until it expires.

## Troubleshooting

- **Records not resolving**: Check nameserver delegation at your registrar.
- **Internal DNS not working**: Confirm the VPC is associated with the private zone.
- **DNSSEC errors**: Enable DNSSEC under zone settings and add the DS record at your registrar.
""",
    ),
    (
        "object_storage.md",
        "Object Storage",
        """\
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
""",
    ),
    (
        "iam_access_control.md",
        "IAM & Access Control",
        """\
# IAM & Access Control

Nirvana Cloud uses role-based access control (RBAC) to manage who can do what within
your organization.

## Roles

| Role | Permissions |
|------|-------------|
| Owner | Full access including billing and member management |
| Admin | Full resource access; cannot modify billing or remove Owners |
| Developer | Create/manage VMs, storage, networking; read-only billing |
| Viewer | Read-only access to all resources |
| Billing | Read/write billing and invoices only |

## Inviting Team Members

1. Navigate to **Settings → Team → + Invite Member**.
2. Enter the email address and select a role.
3. The invitee receives an email to accept and set a password.

## Service Accounts

Service accounts are machine identities for automated workloads (CI/CD, scripts, Terraform):

1. **Settings → Service Accounts → + Create**.
2. Assign a role (prefer least-privilege: Viewer or Developer).
3. Generate an API key for the service account.
4. Use the key in your automation — it never expires unless rotated manually.

## API Keys

Personal API keys are scoped to your user account:
- **Settings → API Keys → + Create Key**.
- Label keys by purpose (e.g., `terraform-prod`, `local-dev`).
- Rotate keys regularly; revoke any that are no longer needed.

## Resource-Level Permissions (Enterprise)

Enterprise plans support resource-level policies to restrict access to specific
VMs, buckets, or VPCs by user or service account.

## Audit Log

All API calls and dashboard actions are recorded:
- **Settings → Audit Log**.
- Filter by user, action type, or resource.
- Export to CSV or stream to an external SIEM via webhook.

## SSO Integration

See the dedicated **SSO Configuration** article for SAML/OIDC setup.
""",
    ),
    (
        "two_factor_auth.md",
        "Two-Factor Authentication",
        """\
# Two-Factor Authentication (2FA)

Enabling 2FA adds a second verification step to your login, protecting your account
even if your password is compromised.

## Enabling 2FA

1. Navigate to **Settings → Security → Two-Factor Authentication**.
2. Click **Enable 2FA**.
3. Scan the QR code with an authenticator app (Google Authenticator, Authy, 1Password, etc.).
4. Enter the 6-digit code to confirm setup.
5. Save your backup codes in a secure location — these let you access your account
   if you lose your device.

## Backup Codes

Each account receives 10 single-use backup codes. Use one if you cannot access
your authenticator app:

- Navigate to **Settings → Security → View Backup Codes**.
- Each code can only be used once.
- Regenerate codes after using one: **Regenerate Backup Codes**.

## Lost Authenticator Device

If you lose your device and have no backup codes:

1. Contact support@nirvanacloud.io from your account's registered email.
2. We will verify your identity via an out-of-band process.
3. Once verified, support will disable 2FA so you can re-enrol.

## Organization-Wide 2FA Enforcement (Enterprise)

Require all team members to enable 2FA:
- **Settings → Security → Enforce 2FA for all members**.
- Members without 2FA will be locked out of the dashboard until they enrol.

## App-Specific Notes

- **Google Authenticator**: Does not support encrypted backups — use Authy or 1Password
  if you want cross-device sync.
- **Authy**: Supports multi-device sync and encrypted backups.
- **Hardware keys (YubiKey)**: FIDO2/WebAuthn support is available on Enterprise plans.
""",
    ),
    (
        "audit_logs.md",
        "Audit Logs & Compliance",
        """\
# Audit Logs & Compliance

## What Is Logged?

Every action taken via the dashboard or API is recorded:

- Authentication events (login, logout, failed login, MFA challenge)
- Resource changes (VM create/delete/resize, firewall rule changes, etc.)
- Billing events (payment method added, invoice generated, subscription changed)
- Team management (member invited, role changed, member removed)
- Security events (API key created/revoked, 2FA enabled/disabled)

## Accessing the Audit Log

**Dashboard**: **Settings → Audit Log**

Filter by:
- Date range
- User or service account
- Action type
- Resource type

**API**:
```
GET /v1/audit-events?page=1&per_page=100&user_id=usr_xxx&action=vm.delete
```

## Exporting

- **CSV export**: Available from the dashboard for date ranges up to 90 days.
- **Real-time streaming**: Configure a webhook under **Settings → Audit Log → Stream**
  to receive events as they occur (JSON over HTTPS).

## Retention

- Standard plans: 30 days
- Business plans: 90 days
- Enterprise plans: 1 year (configurable up to 7 years with extended retention add-on)

## Compliance Certifications

Nirvana Cloud maintains the following certifications:

| Certification | Status |
|---------------|--------|
| SOC 2 Type II | Active — report available on request |
| ISO 27001 | Active |
| GDPR | Compliant — DPA available |
| HIPAA | BAA available for Enterprise |
| PCI DSS | Level 1 — applicable to payment processing only |

## Data Residency

Audit logs are stored in the same region as your primary workloads. For EU customers,
logs remain within the EU. Contact sales for custom data-residency arrangements.
""",
    ),
    (
        "kubernetes.md",
        "Kubernetes Clusters",
        """\
# Nirvana Kubernetes Service (NKS)

## Creating a Cluster

1. Navigate to **Containers → Kubernetes → + Create Cluster**.
2. Select Kubernetes version (latest stable recommended).
3. Configure the control plane region.
4. Add node pools (groups of identically-sized worker VMs).
5. Click **Create** — the cluster is ready in 3–5 minutes.

## Node Pools

A node pool is a set of VMs sharing the same instance type and configuration:

- Add pools for different workload types (CPU-optimized, GPU, memory-optimized).
- Enable **Autoscaling** per pool: specify min/max node count.
- Nodes are replaced with zero-downtime rolling updates during Kubernetes upgrades.

## Accessing Your Cluster

Download the kubeconfig:
```bash
nirvana kubernetes get-credentials <cluster-name> --region us-east-1
```
This writes the kubeconfig to `~/.kube/config` (or merges it).

## Persistent Volumes

NKS integrates with Nirvana Block Storage via a CSI driver pre-installed on every
cluster. Use the `nirvana-block` StorageClass:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  storageClassName: nirvana-block
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 50Gi
```

## Load Balancer Integration

Kubernetes `Service` resources of type `LoadBalancer` automatically provision a
Nirvana Layer 4 load balancer. Annotations control advanced options:

```yaml
metadata:
  annotations:
    service.beta.kubernetes.io/nirvana-load-balancer-type: "layer7"
```

## Upgrades

Control-plane upgrades are performed in-place. Worker nodes are drained, upgraded,
and uncordoned one at a time (rolling update). Typical upgrade time: 10–20 minutes
per node pool.

## Pricing

- Control plane: $0.10/hour (managed, highly available)
- Worker nodes: billed at standard VM rates
""",
    ),
    (
        "container_registry.md",
        "Container Registry",
        """\
# Nirvana Container Registry (NCR)

## Creating a Registry

1. Navigate to **Containers → Registry → + Create Registry**.
2. Choose a name (becomes part of the image URL: `registry.nirvanacloud.io/<org>/<name>`).
3. Set visibility: **Private** (default) or **Public**.

## Pushing Images

Authenticate Docker with NCR:
```bash
nirvana registry login
# or:
docker login registry.nirvanacloud.io -u <username> -p <api-key>
```

Tag and push:
```bash
docker tag my-app:latest registry.nirvanacloud.io/my-org/my-app:latest
docker push registry.nirvanacloud.io/my-org/my-app:latest
```

## Pulling in Kubernetes

NKS clusters are pre-authorized to pull from registries in the same organisation.
No imagePullSecret configuration required.

For external clusters, create a pull secret:
```bash
kubectl create secret docker-registry ncr-secret \
  --docker-server=registry.nirvanacloud.io \
  --docker-username=<username> \
  --docker-password=<api-key>
```

## Image Scanning

All pushed images are automatically scanned for known CVEs using Trivy:
- Results appear under the image tag in the registry UI.
- Optionally block pushes of images with critical vulnerabilities:
  **Registry Settings → Security → Block on Critical CVEs**.

## Retention Policies

Auto-delete old image tags to control storage costs:
- **Registry Settings → Retention → + Add Rule**.
- Example: keep only the 10 most recent tags per repository.

## Pricing

- Storage: $0.025/GB/month
- Data transfer (pull): free within the same region; $0.09/GB cross-region or egress
""",
    ),
    (
        "terraform_provider.md",
        "Terraform Provider",
        """\
# Nirvana Cloud Terraform Provider

## Installation

Add the provider to your Terraform configuration:

```hcl
terraform {
  required_providers {
    nirvana = {
      source  = "nirvana-labs/nirvana"
      version = "~> 1.0"
    }
  }
}

provider "nirvana" {
  api_key = var.nirvana_api_key
  region  = "us-east-1"
}
```

Run `terraform init` to download the provider.

## Creating a VM

```hcl
resource "nirvana_vm" "web" {
  name          = "web-server"
  instance_type = "standard-2"
  image         = "ubuntu-22-04"
  region        = "us-east-1"
  ssh_key_ids   = [nirvana_ssh_key.my_key.id]

  network_interface {
    vpc_id    = nirvana_vpc.main.id
    subnet_id = nirvana_subnet.public.id
    public_ip = true
  }
}
```

## Attaching a Volume

```hcl
resource "nirvana_volume" "data" {
  name   = "data-volume"
  size   = 100
  region = "us-east-1"
}

resource "nirvana_volume_attachment" "attach" {
  vm_id     = nirvana_vm.web.id
  volume_id = nirvana_volume.data.id
}
```

## State Backend

Store Terraform state in Nirvana Object Storage:

```hcl
terraform {
  backend "s3" {
    bucket   = "my-tf-state"
    key      = "prod/terraform.tfstate"
    region   = "us-east-1"
    endpoint = "https://storage.nirvanacloud.io"
    # disable AWS-specific features
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
  }
}
```

## Importing Existing Resources

```bash
terraform import nirvana_vm.web vm_abc123
```

## Docs

Full resource reference: docs.nirvanacloud.io/terraform
""",
    ),
    (
        "monitoring_alerts.md",
        "Monitoring & Alerts",
        """\
# Monitoring & Alerts

## Built-in Metrics

Every VM automatically reports:

| Metric | Description |
|--------|-------------|
| `cpu_utilization` | % CPU used across all vCPUs |
| `memory_utilization` | % RAM used |
| `disk_read_iops` / `disk_write_iops` | Block storage I/O operations per second |
| `disk_read_bytes` / `disk_write_bytes` | Throughput in bytes/sec |
| `network_in_bytes` / `network_out_bytes` | Network throughput |
| `gpu_utilization` | % GPU compute used (GPU instances only) |
| `gpu_memory_utilization` | % GPU VRAM used (GPU instances only) |

## Dashboards

Navigate to **Monitoring → Dashboards** to view time-series graphs for any resource.
Default retention: 30 days at 1-minute resolution.

## Alerts

Create alerts that trigger when a metric crosses a threshold:

1. **Monitoring → Alerts → + Create Alert**.
2. Select the metric, resource, condition (above/below), and threshold.
3. Configure the notification channel:
   - **Email** — sends to any address
   - **Slack** — paste a webhook URL
   - **PagerDuty** — enter your integration key
   - **Webhook** — POST JSON to any HTTPS endpoint

## Alert States

- **OK**: Metric is within threshold.
- **Alerting**: Threshold breached for longer than the configured evaluation window.
- **No data**: No metric data received (VM stopped or agent offline).

## Custom Metrics (Prometheus)

Install the Nirvana Prometheus exporter on your VM to push custom metrics:
```bash
curl -sSL https://install.nirvanacloud.io/prometheus-exporter | bash
```
Metrics appear in the dashboard under **Custom Metrics** within 60 seconds.

## Log-Based Alerts

Forward application logs to **Monitoring → Log Explorer**, then create alerts
based on log patterns (e.g., error rate exceeding N/min).
""",
    ),
    (
        "cost_optimization.md",
        "Cost Optimization",
        """\
# Cost Optimization Guide

## Understand Your Bill

Navigate to **Settings → Billing → Cost Explorer** for a breakdown by:
- Resource type (VM, storage, network)
- Project or team
- Region
- Time period

## Right-Sizing VMs

The most common source of overspend is over-provisioned VMs.

1. Review CPU and memory utilization in **Monitoring → Dashboards**.
2. If average CPU < 20% and memory < 40%, consider downsizing.
3. Stop the VM, resize under **VM Settings → Resize**, restart.

## Spot Instances

Spot instances use spare capacity at up to 80% discount. They may be interrupted
with 2 minutes notice. Best for:
- Batch jobs and data processing
- Distributed training (with checkpointing)
- Stateless workers behind a queue

Enable in **+ New VM → Pricing → Spot**.

## Reserved Instances

Commit to 1 or 3 years for discounts of 30–50%:

| Term | Discount |
|------|----------|
| 1 year | 30% |
| 3 years | 50% |

Reservations are applied automatically to matching running VMs.
Purchase under **Settings → Billing → Reserved Instances**.

## Storage Hygiene

- Delete unattached volumes (they still incur charges).
- Delete unused snapshots.
- Enable object storage lifecycle policies to archive or delete old data.

## Free Tier & Credits

- New accounts receive $200 in credits valid for 60 days.
- Startup Program: 50% off for 12 months (see the Startup Program article).
- Non-profit: contact sales for special pricing.

## Budget Alerts

Set spending limits to avoid surprises:
**Settings → Billing → Budget Alerts → + Create Budget**.
You'll receive an email when you reach 80% and 100% of the budget.
""",
    ),
    (
        "spot_instances.md",
        "Spot Instances",
        """\
# Spot Instances

## What Are Spot Instances?

Spot instances are spare Nirvana capacity offered at up to 80% discount compared
to on-demand pricing. The trade-off is that they can be interrupted when the capacity
is needed elsewhere, with a 2-minute warning.

## Interruption Behaviour

Before interrupting a spot instance, Nirvana:
1. Posts an interruption notice to the instance metadata endpoint
   (`http://169.254.169.254/latest/meta-data/spot/termination-time`).
2. Sends a 2-minute warning signal (SIGTERM equivalent).

Your application should handle this signal by checkpointing work and shutting down cleanly.

## Launching a Spot Instance

**Dashboard**: When creating a VM, toggle **Spot** under Pricing Options.

**Terraform**:
```hcl
resource "nirvana_vm" "worker" {
  instance_type = "standard-8"
  spot          = true
  spot_max_price = 0.10  # optional price ceiling in $/hr
}
```

## Best Practices

- **Use persistent storage**: Attach a block volume for work-in-progress data; the
  volume outlives the instance.
- **Checkpoint frequently**: Write progress to disk or object storage every few minutes.
- **Diversify instance types**: Request across multiple compatible types to increase
  availability.
- **Use a queue**: Worker pulls jobs from SQS/Redis; if the spot instance is killed,
  another worker picks up the job.

## Spot Pools

A Spot Pool is a group of spot instances with automatic replacement on interruption.
Configure under **Compute → Spot Pools**.

## Pricing

Spot prices fluctuate with demand. View the current price history:
**Compute → Spot Instances → Price History**.
""",
    ),
    (
        "auto_scaling.md",
        "Auto-Scaling",
        """\
# Auto-Scaling

Auto-scaling automatically adjusts the number of VMs in a group based on demand.

## Creating a Scaling Group

1. Navigate to **Compute → Scaling Groups → + Create**.
2. Attach a launch template (instance type, image, user-data script).
3. Set minimum and maximum VM count.
4. Attach a load balancer target group (optional but recommended).

## Scaling Policies

### Target Tracking

Maintain a target metric value — the most hands-off approach:
- **CPU target**: Scale out when average CPU > 70%, scale in when < 40%.
- **Request rate**: Scale to maintain N requests/second per instance.

### Step Scaling

Define explicit steps:
- If CPU > 80% for 2 min: add 2 instances.
- If CPU > 95% for 1 min: add 5 instances.
- If CPU < 30% for 10 min: remove 1 instance.

### Scheduled Scaling

Pre-scale for known traffic patterns:
```
cron(0 8 * * MON-FRI) → set min=10
cron(0 20 * * MON-FRI) → set min=2
```

## Warm-Up Period

New instances need time to initialise before receiving traffic. Set the warm-up
period (default 60 seconds) so the scaling policy doesn't add more instances
prematurely.

## Scale-In Protection

Prevent specific instances from being terminated during scale-in:
**Scaling Group → Instance → Enable Scale-In Protection**.
Useful for stateful instances running long jobs.

## Notifications

Receive alerts on scale-out and scale-in events:
**Scaling Group → Notifications → + Add**.
Supports email, Slack, and webhooks.
""",
    ),
    (
        "vpn.md",
        "Private Networking & VPN",
        """\
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
""",
    ),
    (
        "block_storage_advanced.md",
        "Block Storage (Advanced)",
        """\
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
""",
    ),
    (
        "backup_restore.md",
        "Backup & Restore",
        """\
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
""",
    ),
    (
        "multi_region.md",
        "Multi-Region Setup",
        """\
# Multi-Region Setup

## Available Regions

| Region | Location | Notes |
|--------|----------|-------|
| us-east-1 | Virginia, USA | Largest capacity, lowest latency to US East |
| us-west-1 | Oregon, USA | Low latency to US West and Asia-Pacific |
| eu-west-1 | Dublin, Ireland | EU data residency available |
| eu-central-1 | Frankfurt, Germany | German DSGVO compliance |
| ap-south-1 | Mumbai, India | Covers South and Southeast Asia |
| ap-east-1 | Singapore | Southeast Asia hub |

## Global Load Balancing

Route user traffic to the nearest healthy region using Nirvana Global Load Balancer:

1. **Networking → Global Load Balancer → + Create**.
2. Add regional endpoints (each backed by a regional load balancer).
3. Choose routing policy: **Latency-based** (default) or **Geo-based**.
4. Attach a Nirvana-managed domain or CNAME to the GLB endpoint.

## Data Replication

**Object storage**: Enable cross-region replication under **Bucket Settings →
Replication → + Add Rule**. Objects sync within 15 minutes.

**Databases**: Use streaming replication (PostgreSQL) or native replication to
maintain a read replica in a second region.

## Failover Architecture

Example: primary in us-east-1, standby in eu-west-1.

1. Primary region handles all traffic.
2. Standby keeps a warm replica (DB replica + idle VMs).
3. On failure: update DNS TTL to 60s before an incident, then point to eu-west-1.

RTO with DNS failover: 60–120 seconds.

## Latency Benchmarks

Typical inter-region latency (round trip):
- us-east-1 ↔ eu-west-1: ~80 ms
- us-east-1 ↔ ap-south-1: ~160 ms
- eu-west-1 ↔ ap-east-1: ~170 ms

## Cost Considerations

Data transferred between regions is billed at $0.02/GB. Design your architecture
to minimise cross-region traffic — keep data and compute co-located where possible.
""",
    ),
    (
        "sso_configuration.md",
        "SSO Configuration",
        """\
# SSO Configuration

Nirvana Cloud supports SAML 2.0 and OIDC for single sign-on (Enterprise plan).

## SAML 2.0 Setup

### Step 1: Get Nirvana SP Metadata

Navigate to **Settings → Security → SSO → Download SP Metadata**.
This XML file contains the entity ID and ACS URL needed to configure your IdP.

### Step 2: Configure Your IdP

Common IdPs (Okta, Azure AD, Google Workspace):

**Okta**:
1. Create a new SAML app.
2. Upload the SP metadata or enter the ACS URL and Entity ID manually.
3. Map the `email` and `name` attributes.
4. Assign users/groups to the app.

**Azure AD**:
1. Enterprise Applications → New Application → Create your own.
2. Set up Single Sign-On → SAML.
3. Upload SP metadata or configure manually.

### Step 3: Configure Nirvana

1. **Settings → Security → SSO → + Configure SAML**.
2. Paste your IdP metadata XML or enter the SSO URL, entity ID, and certificate.
3. Test the connection before enabling.
4. Enable SSO: once active, all members must sign in via SSO.

## OIDC Setup

1. Create an OIDC application in your IdP (Okta, Auth0, Google).
2. Set the redirect URI to `https://app.nirvanacloud.io/auth/callback`.
3. In Nirvana: **Settings → Security → SSO → + Configure OIDC**.
4. Enter Client ID, Client Secret, and the IdP's discovery URL.

## Just-in-Time Provisioning

New users who sign in via SSO are automatically provisioned in Nirvana with the
**Developer** role by default. Adjust the default role under SSO settings.

## Troubleshooting

- **SAML signature validation failed**: Ensure the IdP certificate is current and
  the clock on your IdP is synchronised (NTP).
- **User not provisioned**: Check that the `email` attribute is being sent by the IdP.
- **Redirect loop**: Verify the ACS URL in your IdP matches exactly (including trailing slash).
""",
    ),
    (
        "postgresql_hosting.md",
        "PostgreSQL Hosting",
        """\
# Running PostgreSQL on Nirvana Cloud

## Recommended Setup

For production workloads, run PostgreSQL on a **Performance SSD** or **ABS NVMe** volume
to handle high write IOPS.

### Instance Recommendation

| Use case | Instance type | Volume |
|----------|--------------|--------|
| Dev/staging | standard-2 | 50 GB SSD |
| Small production | standard-4 | 200 GB Performance SSD |
| High-traffic production | standard-8 | 500 GB ABS NVMe |
| Very high write load | standard-16 | 1 TB ABS NVMe |

## Installation

```bash
sudo apt update && sudo apt install -y postgresql-15
sudo systemctl enable --now postgresql
```

## Data Directory on Attached Volume

Move PostgreSQL data to the attached NVMe volume for better I/O:

```bash
sudo systemctl stop postgresql
sudo rsync -av /var/lib/postgresql/ /data/postgresql/
# Edit /etc/postgresql/15/main/postgresql.conf:
# data_directory = '/data/postgresql/15/main'
sudo systemctl start postgresql
```

## Key Configuration Tuning

```ini
# postgresql.conf
shared_buffers = 4GB          # 25% of RAM
effective_cache_size = 12GB   # 75% of RAM
work_mem = 64MB
wal_buffers = 64MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1        # for SSD/NVMe (default 4.0 is for spinning disk)
```

## Streaming Replication

Set up a hot-standby replica in another region:

```bash
# On primary:
pg_basebackup -h primary_ip -U replicator -D /data/postgresql -P -Xs -R
```

## Backups

Use `pgdump` for logical backups, or Nirvana volume snapshots for physical backups.
Schedule daily snapshots under **VM Settings → Backups**.

## Firewall Rules

PostgreSQL listens on port 5432. Add a firewall rule to allow only your app VMs:
**VM Settings → Firewall → + Add Rule → TCP 5432 from app-vm-ip**.
""",
    ),
    (
        "redis_caching.md",
        "Redis Caching",
        """\
# Redis on Nirvana Cloud

## Why Redis on Nirvana?

Self-hosting Redis on a Nirvana VM gives you:
- Full control over configuration and memory limits
- Persistent storage on ABS NVMe (sub-millisecond disk writes for AOF)
- No data leaving your VPC

## Installation

```bash
sudo apt update && sudo apt install -y redis-server
sudo systemctl enable --now redis-server
```

Configure to listen on the private IP only:
```ini
# /etc/redis/redis.conf
bind 0.0.0.0        # or bind to specific private IP
requirepass your_strong_password
maxmemory 8gb
maxmemory-policy allkeys-lru
```

## Persistence Options

| Mode | Description | Recommended For |
|------|-------------|-----------------|
| No persistence | In-memory only | Pure cache, ephemeral data |
| RDB snapshots | Periodic dump to disk | Cache with acceptable data loss |
| AOF | Append-only log | Session store, queues |
| RDB + AOF | Both | Mission-critical data |

For AOF on ABS NVMe, set `appendfsync everysec` — the NVMe latency makes this
nearly as fast as `no` with much better durability.

## Replication

```ini
# On replica:
replicaof primary_ip 6379
masterauth your_strong_password
```

## Sentinel (High Availability)

Run 3 Sentinel processes (one per VM) to monitor the primary and promote a replica
automatically on failure:

```bash
redis-sentinel /etc/redis/sentinel.conf
```

## Firewall

Redis listens on port 6379. Restrict access to your application VMs only.
Never expose Redis publicly without auth and TLS.

## Monitoring

Redis exports metrics via INFO command. Use the Prometheus `redis_exporter`
sidecar and push to Nirvana Monitoring for CPU, memory, and hit-rate dashboards.
""",
    ),
    (
        "log_aggregation.md",
        "Log Aggregation",
        """\
# Log Aggregation on Nirvana Cloud

## Built-in Log Explorer

Every VM's stdout/stderr is captured and available in **Monitoring → Log Explorer**
with a 7-day retention window (30 days on Business+).

Filter by:
- VM name
- Log level (ERROR, WARN, INFO, DEBUG)
- Free-text search with full-text indexing

## Shipping to External Systems

### Loki + Grafana

```bash
# Install Promtail on each VM
curl -O https://github.com/grafana/loki/releases/download/v2.9.0/promtail-linux-amd64.zip
unzip promtail-linux-amd64.zip
```

Point Promtail at your Loki endpoint (self-hosted or Grafana Cloud).

### Elastic Stack

Ship logs via Filebeat:
```yaml
# filebeat.yml
filebeat.inputs:
  - type: journald
    id: system-logs

output.elasticsearch:
  hosts: ["https://your-elastic-endpoint:9200"]
  api_key: "your-api-key"
```

### Datadog / New Relic

Install the vendor agent on each VM. Both support auto-discovery of Docker containers.

## Structured Logging Best Practices

Log in JSON to enable rich filtering:
```python
import structlog
logger = structlog.get_logger()
logger.info("request completed", path="/search", latency_ms=37, status=200)
```

## Audit Log Streaming

Stream security audit events to your SIEM:
**Settings → Audit Log → Stream → + Add Webhook**.

## Log-Based Alerts

In Log Explorer, click **Create Alert** on any search query to get notified when
the match rate exceeds a threshold (e.g., > 10 ERROR logs/minute).
""",
    ),
    (
        "migration_from_aws.md",
        "Migrating from AWS",
        """\
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
aws s3 sync s3://my-aws-bucket s3://my-nirvana-bucket \
  --source-region us-east-1 \
  --endpoint-url https://storage.nirvanacloud.io
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
""",
    ),
    (
        "migration_from_gcp.md",
        "Migrating from GCP",
        """\
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
rclone copy gcs:my-bucket nirvana:my-bucket \
  --transfers 16 --checkers 32 --progress
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
""",
    ),
    (
        "reserved_instances.md",
        "Reserved Instances",
        """\
# Reserved Instances

## What Are Reserved Instances?

Reserved instances are a billing commitment that provides a discount of 30–50%
in exchange for agreeing to use a specific instance type in a specific region
for 1 or 3 years.

## Commitment Types

| Term | Payment | Discount |
|------|---------|----------|
| 1 year | Monthly | 30% |
| 1 year | Full upfront | 35% |
| 3 years | Monthly | 45% |
| 3 years | Full upfront | 50% |

## Purchasing a Reservation

1. Navigate to **Settings → Billing → Reserved Instances → + Purchase**.
2. Select the instance type, region, term, and payment option.
3. Confirm. The reservation applies immediately to any matching running VM.

## How Reservations Are Applied

Reservations are applied automatically — no configuration required on the VM.
If you have a reservation for `standard-4` in `us-east-1` and you run a matching
VM, you are billed at the reserved rate for those hours.

## Unused Reservations

If you stop a VM covered by a reservation, you continue to be charged (the
reservation is for capacity, not usage). To avoid waste, keep reserved VMs
running or sell unused capacity (see Reservation Marketplace).

## Reservation Marketplace (Business & Enterprise)

Sell unused reservations to other Nirvana customers at a negotiated price:
**Settings → Billing → Reserved Instances → List for Sale**.

## Recommendations

Use **Settings → Billing → Cost Explorer → Reservation Recommendations** to see
which running on-demand VMs would benefit most from a reservation based on
your usage history.

## Scope

- **Regional**: Applies to any VM of the matching type in the specified region.
- **Zonal**: Applies to a specific availability zone, guarantees capacity (Enterprise).
""",
    ),
    (
        "file_storage.md",
        "File Storage (NFS)",
        """\
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
""",
    ),
    (
        "compliance_gdpr.md",
        "GDPR Compliance",
        """\
# GDPR Compliance on Nirvana Cloud

## Nirvana as a Data Processor

When you store personal data on Nirvana Cloud, Nirvana acts as a data processor.
You (the customer) remain the data controller.

## Data Processing Agreement (DPA)

Nirvana provides a GDPR-compliant DPA that covers:
- Categories of personal data processed
- Technical and organisational measures (TOMs)
- Sub-processor list
- Data subject rights obligations

**Signing the DPA**: Navigate to **Settings → Compliance → Download DPA**.
Return a signed copy to legal@nirvanacloud.io or sign electronically via DocuSign.

## EU Data Residency

To ensure personal data never leaves the EU:
1. Use only EU regions: `eu-west-1` (Ireland) or `eu-central-1` (Frankfurt).
2. Disable cross-region replication to non-EU regions.
3. Object storage encryption keys are stored in the same EU region.

## Sub-Processors

Nirvana uses a limited set of sub-processors (payment processors, infrastructure
providers). The current list is maintained at docs.nirvanacloud.io/sub-processors.
Customers are notified 30 days before adding a new sub-processor.

## Data Subject Requests

Nirvana provides tooling to export or delete all data associated with a user ID:
```
POST /v1/gdpr/export  { "user_id": "..." }
POST /v1/gdpr/delete  { "user_id": "..." }
```

## Audit Log for GDPR

All data access events are logged. Export the audit log as evidence of access
controls for supervisory authority inquiries.

## Breach Notification

In the event of a security incident affecting personal data, Nirvana will notify
affected customers within 72 hours, as required by GDPR Article 33.
""",
    ),
    (
        "support_slas.md",
        "Support Tiers & SLAs",
        """\
# Support Tiers & SLAs

## Support Plans

| Plan | Response Time | Channels | Included With |
|------|---------------|----------|---------------|
| Community | Best-effort | Documentation, community forum | Free |
| Standard | 8 business hours | Email, ticket portal | Pro |
| Business | 4 hours (24/7 for P1) | Email, ticket portal, Slack | Business |
| Enterprise | 1 hour (24/7 for P1) | Dedicated Slack, phone, TAM | Enterprise |

## Priority Levels

| Priority | Definition | Response SLA |
|----------|------------|--------------|
| P1 | Production system completely down | 1 hour (Enterprise), 4 hours (Business) |
| P2 | Significant degradation, no workaround | 4 hours (Enterprise), 8 hours (Business) |
| P3 | Partial impact, workaround exists | 8 hours (Enterprise), next business day (Business) |
| P4 | Questions, feature requests | 2 business days |

## Escalation Path

1. **Tier 1 (Support)**: Initial triage and known-issue resolution.
2. **Tier 2 (Senior Support)**: Complex multi-system issues.
3. **Tier 3 (Engineering)**: Bug investigations and hotfixes.
4. **Tier 4 (On-call Engineering)**: P1 incidents requiring immediate engineering intervention.

## SLA Credits

If Nirvana fails to meet a response-time SLA, customers receive service credits:
- Miss by < 2x SLA: 10% credit of affected month's invoice
- Miss by 2–5x SLA: 25% credit
- Miss by > 5x SLA: 50% credit

Credits are applied automatically to the next invoice.

## Reporting an Incident

- **Dashboard**: **Support → + New Ticket**
- **Email**: support@nirvanacloud.io
- **Enterprise hotline**: Available in your welcome email

Always include: VM IDs or resource identifiers, region, timestamps, and error messages.

## Status Page

Check real-time service status and incident history at status.nirvanacloud.io.
Subscribe to status updates via email or RSS.
""",
    ),
    (
        "ci_cd_integration.md",
        "CI/CD Integration",
        """\
# CI/CD Integration

## GitHub Actions

Deploy to a Nirvana VM from a GitHub Actions workflow:

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Nirvana VM
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VM_IP }}
          username: ubuntu
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /app
            git pull origin main
            docker compose up -d --build
```

Store `VM_IP` and `SSH_PRIVATE_KEY` as GitHub encrypted secrets.

## GitLab CI

```yaml
deploy:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | ssh-add -
  script:
    - ssh ubuntu@$VM_IP "cd /app && git pull && docker compose up -d"
  only:
    - main
```

## Terraform in CI

```yaml
- name: Terraform Apply
  env:
    NIRVANA_API_KEY: ${{ secrets.NIRVANA_API_KEY }}
  run: |
    terraform init
    terraform plan
    terraform apply -auto-approve
```

## Rolling Deployments

Use the Nirvana API to perform rolling updates across a scaling group:
```bash
nirvana scaling-group rolling-update my-group \
  --launch-template new-template-id \
  --max-surge 1 \
  --max-unavailable 0
```

## Container Registry in CI

```yaml
- name: Push image
  run: |
    docker login registry.nirvanacloud.io -u ${{ secrets.NCR_USER }} -p ${{ secrets.NCR_TOKEN }}
    docker build -t registry.nirvanacloud.io/my-org/my-app:$GITHUB_SHA .
    docker push registry.nirvanacloud.io/my-org/my-app:$GITHUB_SHA
```
""",
    ),
    (
        "static_website_hosting.md",
        "Static Website Hosting",
        """\
# Static Website Hosting

Host a static site (HTML, CSS, JS, or a built React/Vue/Next.js app) on
Nirvana Object Storage without managing a VM.

## Enabling Static Hosting

1. Create a bucket with a globally unique name (ideally matching your domain).
2. Open **Bucket Settings → Static Website Hosting → Enable**.
3. Set the **Index document** (e.g., `index.html`) and **Error document** (e.g., `404.html`).
4. Upload your build output:
   ```bash
   aws s3 sync ./dist s3://my-site/ --endpoint-url https://storage.nirvanacloud.io
   ```
5. The site is accessible at `https://my-site.storage.nirvanacloud.io`.

## Custom Domain & HTTPS

1. Create a CNAME record: `www.example.com → my-site.storage.nirvanacloud.io`.
2. Request a managed TLS certificate under **Settings → Certificates → + Request**.
3. Attach the certificate to the bucket: **Bucket Settings → Custom Domain → Add**.

## CDN (Cache)

Enable the Nirvana CDN to serve assets from edge nodes closest to your users:
**Bucket Settings → CDN → Enable**.

Benefits:
- Static assets cached at 15+ edge locations
- Reduced origin bandwidth costs
- Automatic HTTPS at the edge

## Cache Invalidation

After deploying a new version, invalidate the CDN cache:
```bash
nirvana cdn invalidate --bucket my-site --paths "/*"
```

Or set cache-control headers on your files to control TTL:
```bash
aws s3 cp dist/ s3://my-site/ --recursive \
  --cache-control "public, max-age=31536000" \
  --endpoint-url https://storage.nirvanacloud.io
```

## Deployment Pipeline

```bash
# .github/workflows/deploy.yml snippet
- name: Deploy site
  run: |
    npm run build
    aws s3 sync dist/ s3://my-site/ --delete \
      --endpoint-url https://storage.nirvanacloud.io
    nirvana cdn invalidate --bucket my-site --paths "/*"
```
""",
    ),
    (
        "gpu_ai_workloads.md",
        "GPU Instances for AI Workloads",
        """\
# GPU Instances for AI Workloads

## Available GPU Configurations

| Instance | GPUs | VRAM | vCPUs | RAM | Best For |
|----------|------|------|-------|-----|----------|
| gpu-small | 1x A10G | 16 GB | 8 | 32 GB | Fine-tuning small models, inference |
| gpu-medium | 2x A10G | 32 GB | 16 | 64 GB | Fine-tuning medium models |
| gpu-large | 8x A100 | 320 GB | 96 | 768 GB | Pre-training, large model inference |
| gpu-xl | 16x H100 | 640 GB | 192 | 2 TB | Frontier model training |

Note: 1.5 GB of VRAM is reserved per GPU for ECC error correction and driver overhead.

## Setting Up CUDA

GPU instances come with NVIDIA drivers pre-installed on CUDA-enabled images:

```bash
# Verify GPU is visible
nvidia-smi

# Check CUDA version
nvcc --version
```

Use the `ubuntu-22-04-cuda-12` image when creating your VM for a pre-configured
CUDA environment.

## Running Inference with Ollama

```bash
docker run --gpus all -p 11434:11434 ollama/ollama
docker exec -it ollama ollama pull llama3.2:8b
```

Ollama automatically detects and uses all available GPUs.

## Running Inference with vLLM

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --tensor-parallel-size 2
```

## Persistent Model Storage

Store model weights on an ABS NVMe volume (not the root disk):

```bash
# Mount volume at /models
sudo mkfs.ext4 /dev/vdb
sudo mount /dev/vdb /models
```

Download weights once; reload from disk on subsequent starts — no repeated downloads.

## GPU Monitoring

GPU metrics (utilization, VRAM, temperature) are available in **Monitoring → Dashboards**
for any GPU instance. Set alerts on `gpu_utilization > 95%` to detect training stalls.

## Cost

GPU instances are billed per second. Spot GPU instances are available at up to 70%
discount for interruptible training jobs.
""",
    ),
    (
        "vector_database_hosting.md",
        "Hosting a Vector Database",
        """\
# Hosting a Vector Database on Nirvana Cloud

Vector databases are I/O-intensive: they maintain large HNSW or IVF indexes that
must be read from disk during similarity search. Nirvana ABS NVMe volumes are
purpose-built for this workload.

## Qdrant

The recommended self-hosted vector database for Nirvana deployments.

### Quick Setup (Docker)

```bash
docker run -d --name qdrant \
  -p 6333:6333 \
  -v /data/qdrant:/qdrant/storage \
  qdrant/qdrant:latest
```

Mount Qdrant storage on an ABS NVMe volume (`/data/qdrant`) for 10,000+ IOPS.

### Sizing Guide

| Vectors | Dimensions | Index Size | Recommended Volume |
|---------|-----------|------------|-------------------|
| 100K | 384 | ~150 MB | 10 GB SSD |
| 1M | 384 | ~1.5 GB | 50 GB SSD |
| 10M | 384 | ~15 GB | 200 GB NVMe |
| 100M | 1536 | ~600 GB | 1 TB NVMe |

### Taking Snapshots

```bash
curl -X POST "http://localhost:6333/collections/my_collection/snapshots"
```

Store the resulting `.tar` file in Nirvana Object Storage for backup.

## Weaviate

```bash
docker run -d --name weaviate \
  -p 8080:8080 \
  -v /data/weaviate:/var/lib/weaviate \
  semitechnologies/weaviate:latest
```

## Milvus

```bash
docker compose up -d  # using Milvus's official docker-compose.yml
```

## Performance Tuning

- **NVMe mount**: `sudo mount -o noatime,nodiratime /dev/nvme0n1 /data`
- **Readahead**: `sudo blockdev --setra 256 /dev/nvme0n1`
- **Huge pages**: `echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages`

## Recommended Instance for Qdrant

For 10M vectors at 384 dims: `standard-8` with a 200 GB ABS NVMe volume.
""",
    ),
    (
        "team_management.md",
        "Team Management",
        """\
# Team Management

## Inviting Members

1. Navigate to **Settings → Team → + Invite Member**.
2. Enter the member's email and assign a role.
3. The invite expires after 7 days. Resend under **Pending Invites**.

## Managing Roles

Change a member's role:
**Settings → Team → [Member] → Edit Role**.

Available roles: Owner, Admin, Developer, Viewer, Billing.
See the **IAM & Access Control** article for permission details.

## Removing Members

1. **Settings → Team → [Member] → Remove Member**.
2. All API keys belonging to the member are immediately revoked.
3. Resources created by the member remain; ownership is not transferred.

## Groups (Enterprise)

Organise members into groups for bulk role assignment:
**Settings → Groups → + Create Group**.

Assign groups to projects:
**Project Settings → Members → + Add Group**.

## Projects

Projects provide a logical boundary for resources (VMs, volumes, networks):

1. **Projects → + Create Project**.
2. Assign members and their roles within this project.
3. Resources created within the project are billed to the project cost centre.

## Usage by Member

View resource usage broken down by team member:
**Settings → Billing → Cost Explorer → Group by User**.

## Off-boarding Checklist

When a member leaves:
- [ ] Remove from team (**Settings → Team → Remove**)
- [ ] Rotate any secrets they had access to
- [ ] Review and transfer ownership of any personal API keys
- [ ] Audit recent API calls in the Audit Log
""",
    ),
    (
        "ip_addressing.md",
        "IP Addressing & Public IPs",
        """\
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
""",
    ),
    (
        "firewall_advanced.md",
        "Advanced Firewall Configuration",
        """\
# Advanced Firewall Configuration

## Default Rules

Every VM starts with these default firewall rules:
- **Inbound**: Allow TCP 22 (SSH) from anywhere
- **Outbound**: Allow all traffic

## Adding Rules

**Dashboard**: VM Settings → Firewall → + Add Rule.

**API**:
```bash
curl -X POST https://api.nirvanacloud.io/v1/vms/<vm-id>/firewall-rules \
  -H "Authorization: Bearer <api-key>" \
  -d '{"direction":"inbound","protocol":"tcp","port":443,"source":"0.0.0.0/0"}'
```

## Source Filtering

Restrict access by IP range:
- Single IP: `203.0.113.42/32`
- CIDR range: `10.0.0.0/24`
- Anywhere: `0.0.0.0/0` (IPv4) or `::/0` (IPv6)
- Another VPC: use its CIDR block

## Security Groups (Enterprise)

A security group is a reusable set of firewall rules that can be applied to
multiple VMs:

1. **Networking → Security Groups → + Create**.
2. Define inbound and outbound rules.
3. Attach to VMs at creation time or via **VM Settings → Security Groups**.

Changes to a security group apply instantly to all attached VMs.

## Network ACLs

Applied at the subnet level, before security groups:
- Stateless (must explicitly allow return traffic)
- Support allow and deny rules
- Applied in order (lowest rule number first)

**Networking → Subnets → [Subnet] → Network ACL → Edit**.

## Logging Dropped Packets

Enable firewall logging to debug connectivity issues:
**VM Settings → Firewall → Enable Logging**.
Logs appear in **Monitoring → Log Explorer** under the `firewall` source.

## Common Configurations

| Use Case | Inbound Rules |
|----------|--------------|
| Web server | TCP 80, TCP 443 from 0.0.0.0/0 |
| API server (internal only) | TCP 8000 from VPC CIDR |
| Database | TCP 5432 from app subnet only |
| Redis | TCP 6379 from app subnet only |
""",
    ),
    (
        "api_reference.md",
        "API Reference Overview",
        """\
# Nirvana Cloud API Reference

## Base URL

```
https://api.nirvanacloud.io/v1
```

All responses are JSON. All requests must include an `Authorization` header:
```
Authorization: Bearer <api-key>
```

## Rate Limits

| Endpoint class | Limit |
|---------------|-------|
| Read (GET) | 600 requests/minute |
| Write (POST/PUT/DELETE) | 120 requests/minute |
| Bulk operations | 20 requests/minute |

On rate limit: HTTP 429 with `Retry-After` header.

## Pagination

List endpoints return paginated results:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 25,
    "total": 142,
    "total_pages": 6
  }
}
```

Pass `?page=2&per_page=50` to navigate pages.

## Common Endpoints

### VMs
```
GET    /vms                     List VMs
POST   /vms                     Create VM
GET    /vms/{id}                Get VM details
DELETE /vms/{id}                Delete VM
POST   /vms/{id}/actions/stop   Stop VM
POST   /vms/{id}/actions/start  Start VM
```

### Volumes
```
GET    /volumes                 List volumes
POST   /volumes                 Create volume
DELETE /volumes/{id}            Delete volume
POST   /volumes/{id}/attach     Attach to VM
POST   /volumes/{id}/detach     Detach from VM
```

### Snapshots
```
POST   /vms/{id}/snapshots      Take snapshot
GET    /snapshots               List snapshots
DELETE /snapshots/{id}          Delete snapshot
POST   /snapshots/{id}/restore  Restore snapshot
```

## Error Format

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "VM vm_abc123 not found",
    "request_id": "req_xyz789"
  }
}
```

Include the `request_id` when contacting support.

## Client Libraries

- Python: `pip install nirvana-cloud`
- Node.js: `npm install @nirvana-labs/sdk`
- Go: `go get github.com/nirvana-labs/nirvana-go`
- Terraform: registry.terraform.io/providers/nirvana-labs/nirvana
""",
    ),
    (
        "startup_program.md",
        "Startup Program",
        """\
# Nirvana Cloud Startup Program

## Who Qualifies?

- Company founded within the last 3 years
- Less than $5M in total funding
- Less than $1M ARR
- Not a current Nirvana customer (new accounts only)
- Incorporated entity (not individual freelancers)

## Benefits

| Benefit | Details |
|---------|---------|
| Credit | $5,000 in Nirvana credits (valid 12 months) |
| Discount | 50% off all resources for 12 months after credits are used |
| Support | Business-tier support included |
| Office hours | Monthly group office hours with Nirvana solutions engineers |
| Perks | Access to partner discounts (Stripe, Notion, Linear, etc.) |

## How to Apply

1. Visit nirvanacloud.io/startups.
2. Complete the application form (takes ~10 minutes).
3. Provide proof of incorporation and company age.
4. Receive a decision within 2 business days.
5. Credits are applied to your account within 24 hours of approval.

## Renewal

After 12 months, you may re-apply if you still meet the eligibility criteria.
Re-qualifying startups receive a 25% discount (credits are not renewable).

## Alumni

Notable companies that scaled from the Startup Program to Enterprise:
- The program has helped 1,000+ startups launch AI-native products on Nirvana.

## Investor Network

Nirvana partners with leading VC firms. If your investor is a Nirvana partner,
mention it in your application for expedited review.

## Contact

startup@nirvanacloud.io for questions about the program.
""",
    ),
    (
        "enterprise_contracts.md",
        "Enterprise Contracts & Pricing",
        """\
# Enterprise Contracts & Pricing

## What's Included in Enterprise?

- Committed spend discounts (15–40% based on volume)
- Dedicated account manager and Technical Account Manager (TAM)
- Private Slack channel with Nirvana engineering
- 1-hour P1 SLA (24/7)
- Custom data residency and compliance support
- SAML/OIDC SSO
- Resource-level IAM policies
- Extended audit log retention (up to 7 years)
- HIPAA BAA and custom DPA available
- Quarterly business reviews

## Pricing Structure

Enterprise pricing is negotiated based on:
- Committed monthly spend
- Contract length (1 or 3 years)
- Mix of resource types (compute, storage, networking)

Typical discounts:
| Committed Monthly Spend | Discount vs. List Price |
|------------------------|------------------------|
| $10K–$25K | 15% |
| $25K–$100K | 25% |
| $100K+ | 35–40% |

## Custom Pricing for AI Workloads

GPU-heavy workloads receive custom pricing:
- Reserved GPU capacity (guaranteed availability)
- Discounted NVMe storage
- Priority GPU queue during capacity constraints

## How to Start an Enterprise Conversation

1. Contact sales@nirvanacloud.io or fill out the form at nirvanacloud.io/enterprise.
2. A sales engineer will schedule a discovery call (30 minutes).
3. We provide a custom proposal within 5 business days.
4. Legal review and contract signing: typically 1–2 weeks.

## Payment Terms

- Standard: Net-30, monthly invoice
- Custom: Quarterly or annual prepay available

## Invoicing

Enterprise customers receive PDF invoices by email and can also access them via
**Settings → Billing → Invoice History**.
""",
    ),
    (
        "data_residency.md",
        "Data Residency",
        """\
# Data Residency

## What Is Data Residency?

Data residency refers to the physical location where your data is stored and processed.
Nirvana Cloud gives you explicit control over where your data lives.

## Regional Isolation

All resources you create are region-specific. When you launch a VM in `eu-west-1`,
its data stays in Ireland unless you explicitly move it. Nirvana never migrates
data between regions without your action.

## EU Data Residency (GDPR)

To comply with GDPR data-transfer requirements:

1. Use only `eu-west-1` (Ireland) or `eu-central-1` (Frankfurt).
2. Do not enable cross-region replication to non-EU regions.
3. Use EU endpoints for object storage: `storage.eu-west-1.nirvanacloud.io`.

All encryption keys for EU data are stored and managed within the EU.

## German Data Residency (DSGVO)

For stricter German requirements, use `eu-central-1` (Frankfurt). This region
is operated entirely within German data centres with German subcontractors.

## Data in Transit

All data in transit is encrypted using TLS 1.2 or higher. Connections to the
Nirvana API, dashboard, and object storage all enforce TLS.

## Customer-Managed Encryption Keys

Control where your encryption keys are stored with CMEK:
- Keys are created and stored in **Settings → Key Management**.
- Keys never leave the region you specify.
- You can revoke access by disabling the key — all encrypted resources become inaccessible.

## Compliance Reports

Download compliance reports (SOC 2 Type II, ISO 27001) from
**Settings → Compliance → Reports** or by requesting them via support.

## Custom Data Residency (Enterprise)

For requirements beyond the standard regions (e.g., dedicated infrastructure,
specific data centres, sovereign cloud), contact sales@nirvanacloud.io.
""",
    ),
    (
        "windows_vms.md",
        "Windows VMs",
        """\
# Windows VMs on Nirvana Cloud

## Available Windows Images

| Image | License | Notes |
|-------|---------|-------|
| Windows Server 2022 Standard | Included in VM price | Most common for production |
| Windows Server 2022 Datacenter | Included | Unlimited Windows VMs for nested virtualisation |
| Windows Server 2019 Standard | Included | LTS option |
| Windows 11 Pro | Additional license fee | Desktop workloads |

## Launching a Windows VM

1. When creating a VM, select the **Windows Server 2022** image.
2. Set the administrator password in the **User Data** field:
   ```
   <powershell>
   net user Administrator "YourStrongPassword123!"
   </powershell>
   ```
3. Ensure port **3389 (RDP)** is open in firewall rules.
4. After boot (~3 minutes), connect via Remote Desktop.

## RDP Connection

**Windows**: Open Remote Desktop Connection → enter the VM's public IP.

**macOS**: Use Microsoft Remote Desktop (from the Mac App Store).

**Linux**:
```bash
xfreerdp /v:<vm-ip> /u:Administrator /p:'YourPassword'
```

## WinRM (Remote Management)

For automated configuration with Ansible or PowerShell remoting:
```powershell
# Run on the VM after first login
Enable-PSRemoting -Force
```

Allow port 5985 (WinRM HTTP) or 5986 (WinRM HTTPS) in firewall rules.

## Windows Firewall

The Windows built-in firewall applies in addition to the Nirvana VM firewall.
If a port is open in Nirvana but still unreachable, check Windows Firewall rules:
```powershell
New-NetFirewallRule -DisplayName "My App" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

## Pricing

Windows VMs are billed at the same compute rate as Linux VMs. Windows Server
licenses are included in the price.
""",
    ),
    (
        "high_availability.md",
        "High Availability Patterns",
        """\
# High Availability Patterns

## What "High Availability" Means on Nirvana

Nirvana provides building blocks for HA; you design the pattern that fits your
availability target. Common SLA targets:

| Pattern | Achievable Uptime | Complexity |
|---------|------------------|------------|
| Single VM + daily backup | ~99.5% | Low |
| Active-passive failover | ~99.9% | Medium |
| Active-active multi-zone | ~99.95% | High |
| Active-active multi-region | ~99.99% | Very high |

## Active-Passive Failover

1. Run two identical VMs in different availability zones.
2. Assign a floating IP to the primary.
3. Monitor the primary with an external health check.
4. On failure, reassign the floating IP to the standby (API call, ~10 seconds).

## Active-Active with Load Balancer

1. Create a load balancer with both VMs as backends.
2. Enable health checks — traffic routes only to healthy VMs.
3. On VM failure, the load balancer removes it from rotation automatically.
4. Scale out by adding more VMs to the target group.

## Stateful Services

For databases and caches:
- Use primary-replica replication.
- Promote a replica automatically via a health-check script or a tool like Patroni (PostgreSQL).

## Qdrant High Availability

Qdrant supports distributed mode:
```yaml
# docker-compose.yml (3-node cluster)
services:
  qdrant_node1:
    image: qdrant/qdrant
    command: ./qdrant --cluster-enabled true --cluster-p2p-host qdrant_node1
  qdrant_node2: ...
  qdrant_node3: ...
```

Shards are replicated across nodes. A node failure does not interrupt search.

## Health Check Endpoints

Add a `/health` endpoint to every service:
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

The load balancer polls this endpoint every 10 seconds and removes unhealthy instances.
""",
    ),
    (
        "ipv6_support.md",
        "IPv6 Support",
        """\
# IPv6 Support

## Enabling IPv6 on a VPC

1. Navigate to **VPC Settings → IPv6 → Enable**.
2. Nirvana assigns a `/56` IPv6 prefix to the VPC.
3. Each subnet receives a `/64` from the VPC prefix.
4. VMs in IPv6-enabled subnets receive an IPv6 address automatically.

## Dual Stack

VMs with IPv6 enabled are dual-stack — they have both an IPv4 and an IPv6 address.
Services can listen on both:

```bash
# Python: bind to :: to listen on both IPv4 and IPv6
uvicorn app:main --host :: --port 8000
```

## Firewall Rules for IPv6

Add firewall rules separately for IPv6 traffic:
- IPv4 source: `0.0.0.0/0`
- IPv6 source: `::/0`

Both rules are required to allow traffic from all internet clients.

## Public IPv6 Addresses

IPv6 addresses on Nirvana are publicly routable by default (no NAT).
All addresses in the `/64` subnet are reachable from the internet.
Use firewall rules to restrict access.

## IPv6 in DNS

Add AAAA records for your services to DNS:
```
api.example.com.  300  IN  AAAA  2001:db8::1
```

## Common Issues

- **IPv6 not working on VM**: Ensure the OS has the IPv6 interface configured
  (`ip -6 addr show`). Most modern Linux distributions configure it automatically.
- **Services not listening on IPv6**: Check the bind address in your application config.
- **Firewall blocking IPv6**: Verify `::/0` rules are present alongside `0.0.0.0/0`.
""",
    ),
    (
        "managed_certificates.md",
        "Managed TLS Certificates",
        """\
# Managed TLS Certificates

Nirvana Cloud provides free, automatically renewed TLS certificates via Let's Encrypt.

## Requesting a Certificate

1. Navigate to **Settings → Certificates → + Request Certificate**.
2. Enter the domain name(s) (supports wildcard: `*.example.com`).
3. Choose the validation method:
   - **DNS validation** (recommended): Nirvana adds a TXT record if your domain
     uses Nirvana DNS, or you add it manually.
   - **HTTP validation**: Nirvana places a file on port 80; requires a running VM.
4. Click **Request**. Issuance takes 30–60 seconds.

## Attaching to a Load Balancer

1. Navigate to the load balancer → **Listeners → + Add Listener**.
2. Protocol: HTTPS, Port: 443.
3. Certificate: Select the managed certificate.
4. Nirvana automatically renews the certificate before expiry.

## Wildcard Certificates

Wildcard certificates (`*.example.com`) cover all single-level subdomains:
- ✅ `api.example.com`
- ✅ `app.example.com`
- ❌ `api.v2.example.com` (two levels deep)

Wildcard certificates require DNS validation.

## Custom Certificates (BYOC)

To use a certificate from your own CA or a commercial provider:
1. **Settings → Certificates → + Upload Certificate**.
2. Upload the certificate PEM, private key PEM, and certificate chain PEM.
3. Nirvana stores the private key encrypted at rest.

## Certificate Expiry Alerts

Nirvana sends email warnings 30 days and 7 days before a certificate expires.
Managed certificates renew automatically — expiry alerts indicate a renewal issue.

## Troubleshooting

- **Certificate not issued**: Verify DNS records are correct and have propagated.
- **Browser shows wrong certificate**: Check the load balancer listener is using
  the correct certificate and the CDN cache has been cleared.
""",
    ),
    (
        "account_management.md",
        "Account Management",
        """\
# Account Management

## Changing Your Email Address

1. Navigate to **Settings → Profile → Email**.
2. Enter the new email and confirm your password.
3. A verification link is sent to both addresses.
4. Click the link in the new email to confirm the change.

Note: After changing your email, you must log in with the new address.
Existing API keys remain valid.

## Changing Your Password

1. **Settings → Security → Change Password**.
2. Enter your current password and the new password (minimum 12 characters).
3. All active sessions except the current one are invalidated.

## Closing Your Account

1. Ensure all resources are deleted (VMs, volumes, load balancers, buckets).
2. Download any invoices you need from **Settings → Billing → Invoice History**.
3. Navigate to **Settings → Account → Close Account**.
4. Confirm by entering your password.

Account closure is irreversible. Any remaining credits are forfeited.

## Account Suspension

Accounts are suspended when:
- Payment fails after 3 retries over 7 days.
- Suspected abuse (automated policy enforcement).
- Violation of the Terms of Service.

To reactivate after payment failure: update your payment method in **Settings → Billing**.
For other suspension reasons, contact support@nirvanacloud.io.

## Multiple Accounts

You may create multiple Nirvana accounts using different email addresses.
For team access, use the Team Management feature instead of sharing credentials.

## Two-Person Rule (Enterprise)

Require two administrators to approve sensitive actions (account closure, large
resource deletions, billing changes):
**Settings → Security → Two-Person Rule → Enable**.
""",
    ),
    (
        "webhooks.md",
        "Webhooks",
        """\
# Webhooks

Webhooks allow Nirvana to notify your application when specific events occur.

## Creating a Webhook

1. Navigate to **Settings → Webhooks → + Create Webhook**.
2. Enter the HTTPS endpoint URL that will receive the events.
3. Select the event types to subscribe to.
4. Set a secret for payload signature verification.

## Event Types

| Category | Events |
|----------|--------|
| VM | `vm.created`, `vm.started`, `vm.stopped`, `vm.deleted`, `vm.error` |
| Volume | `volume.created`, `volume.attached`, `volume.detached`, `volume.deleted` |
| Billing | `invoice.created`, `payment.succeeded`, `payment.failed`, `subscription.cancelled` |
| Team | `member.invited`, `member.joined`, `member.removed` |
| Alert | `alert.triggered`, `alert.resolved` |

## Payload Format

```json
{
  "id": "evt_abc123",
  "type": "vm.stopped",
  "timestamp": "2024-11-15T14:32:00Z",
  "data": {
    "vm_id": "vm_xyz789",
    "name": "my-vm",
    "region": "us-east-1"
  }
}
```

## Signature Verification

Validate that the payload came from Nirvana:

```python
import hmac, hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

The signature is in the `X-Nirvana-Signature` header.

## Retry Policy

Failed webhook deliveries (non-2xx response or timeout) are retried:
- Immediately after failure
- After 5 minutes
- After 30 minutes
- After 2 hours
- After 12 hours

After 5 failures, the webhook is disabled. Re-enable under **Settings → Webhooks**.

## Testing

Use the **Send Test Event** button in the webhook settings to verify your endpoint
is receiving and processing events correctly.
""",
    ),
    (
        "cdr_pulumi.md",
        "Pulumi Provider",
        """\
# Nirvana Cloud Pulumi Provider

## Installation

```bash
pip install pulumi-nirvana     # Python
npm install @nirvana-labs/pulumi  # TypeScript/JavaScript
```

## Authentication

```bash
export NIRVANA_API_KEY=your-api-key
```

Or configure in `Pulumi.yaml`:
```yaml
config:
  nirvana:apiKey:
    secret: true
```

## Basic Example (Python)

```python
import pulumi
import pulumi_nirvana as nirvana

vpc = nirvana.Vpc("main",
    cidr_block="10.0.0.0/16",
    region="us-east-1",
)

vm = nirvana.Vm("web",
    instance_type="standard-4",
    image="ubuntu-22-04",
    region="us-east-1",
    vpc_id=vpc.id,
    public_ip=True,
)

pulumi.export("vm_ip", vm.public_ip)
```

## TypeScript Example

```typescript
import * as nirvana from "@nirvana-labs/pulumi";

const vm = new nirvana.Vm("api-server", {
    instanceType: "standard-8",
    image: "ubuntu-22-04",
    region: "us-east-1",
});

export const ip = vm.publicIp;
```

## State Management

Use Pulumi Cloud (free for individuals) or self-host the state in Nirvana Object Storage:

```bash
pulumi login s3://my-state-bucket?endpoint=https://storage.nirvanacloud.io
```

## Stack Configuration

```bash
pulumi config set nirvana:region us-east-1
pulumi config set --secret nirvana:apiKey your-api-key
```

## Resource Reference

Full resource reference: docs.nirvanacloud.io/pulumi
""",
    ),
    (
        "billing_cycle.md",
        "Billing Cycle & Invoices",
        """\
# Billing Cycle & Invoices

## How Billing Works

Nirvana bills by the second for compute resources and by the hour for storage.
At the end of each billing period, all charges are consolidated into a single invoice.

## Billing Periods

- **Monthly plans**: Billed on the same date each month (your billing anniversary).
- **Annual plans**: Billed upfront for the full year.

## What Appears on Your Invoice

| Line Item | Billing Unit |
|-----------|-------------|
| VM compute | Per second |
| Block storage | Per GB/hour |
| Object storage | Per GB/month |
| Outbound network | Per GB |
| Load balancers | Per hour + per GB |
| Floating IPs (unattached) | Per hour |
| Snapshots | Per GB/month |

## Viewing Your Invoice

1. **Settings → Billing → Invoice History**.
2. Select the invoice to view the line-item breakdown.
3. Download as PDF for accounting.

## Payment Methods

- Credit card (Visa, Mastercard, Amex)
- ACH bank transfer (US accounts)
- Wire transfer (Enterprise — contact billing@nirvanacloud.io)
- Nirvana credits (applied automatically before charging the payment method)

## Credits

Credits are applied automatically to your next invoice. They cannot be refunded
as cash but can be applied to any Nirvana resource.

## Taxes

Nirvana collects VAT for EU customers and GST for Australian customers.
Add your VAT/GST number under **Settings → Billing → Tax Information** to
receive tax-exempt invoices.

## Disputing a Charge

Contact billing@nirvanacloud.io within 30 days of the invoice date.
Disputes are reviewed within 5 business days.
""",
    ),
    (
        "user_data_scripts.md",
        "User Data (Cloud-Init) Scripts",
        """\
# User Data / Cloud-Init Scripts

User data scripts run on first boot, allowing you to automate VM initialisation.

## Passing User Data

**Dashboard**: Expand **Advanced Options → User Data** when creating a VM.

**Terraform**:
```hcl
resource "nirvana_vm" "web" {
  user_data = file("cloud-init.yaml")
}
```

## Cloud-Config Syntax

```yaml
#cloud-config
packages:
  - docker.io
  - git
  - python3-pip

runcmd:
  - systemctl enable --now docker
  - git clone https://github.com/my-org/my-app /opt/my-app
  - cd /opt/my-app && docker compose up -d

write_files:
  - path: /etc/myapp/config.json
    content: |
      {"env": "production", "region": "us-east-1"}
    permissions: '0644'
```

## Shell Script

Prefix with `#!/bin/bash` for a plain shell script:
```bash
#!/bin/bash
set -e
apt update && apt install -y nginx
systemctl enable --now nginx
echo "Hello from Nirvana!" > /var/www/html/index.html
```

## Debugging

If your user data script fails:
```bash
# View cloud-init logs
sudo cat /var/log/cloud-init-output.log
sudo journalctl -u cloud-final
```

## Secrets in User Data

Avoid embedding secrets in user data (it's accessible via the metadata API).
Instead:
- Fetch secrets from Nirvana Object Storage at startup.
- Use environment variables passed via the Nirvana API (Enterprise).
- Use a secrets manager (Vault, AWS Secrets Manager with Nirvana).

## User Data Size Limit

Maximum size: 64 KB. For larger scripts, store the script in Object Storage
and use a minimal user data script to download and execute it.
""",
    ),
    (
        "partner_integrations.md",
        "Partner Integrations",
        """\
# Partner Integrations

## Monitoring & Observability

| Partner | Integration | How to Connect |
|---------|-------------|----------------|
| Datadog | Agent-based | Install Datadog agent; configure API key |
| New Relic | Agent-based | Install NR agent; configure license key |
| Grafana Cloud | Prometheus + Loki | Configure remote_write endpoint |
| Sentry | SDK | Add Sentry SDK to application code |

## DevOps & Automation

| Partner | Integration | Notes |
|---------|-------------|-------|
| GitHub Actions | SSH deploy, Registry push | See CI/CD Integration article |
| GitLab CI | SSH deploy, Registry push | See CI/CD Integration article |
| Terraform | Native provider | See Terraform Provider article |
| Pulumi | Native provider | See Pulumi Provider article |
| Ansible | SSH inventory | Use floating IPs as stable targets |

## Security

| Partner | Integration |
|---------|-------------|
| Snyk | Container image scanning in NCR |
| Qualys | VM vulnerability scanning agent |
| CrowdStrike | Falcon sensor agent |

## Databases

| Partner | Notes |
|---------|-------|
| PlanetScale | Connect from Nirvana VM via public endpoint |
| Neon | Serverless Postgres; connect from VM |
| MongoDB Atlas | Connect from Nirvana VM via private endpoint |

## Setting Up an Integration

Most integrations follow the same steps:
1. Install the partner agent or SDK on your VM.
2. Provide the partner's API key or connection string.
3. Data flows from Nirvana to the partner's platform.

For integrations requiring inbound webhooks (e.g., PagerDuty escalation back to
Nirvana), configure a webhook in **Settings → Webhooks**.
""",
    ),
    (
        "network_pricing.md",
        "Network Pricing",
        """\
# Network Pricing

## Inbound Traffic

All inbound traffic to Nirvana Cloud is **free** — no ingress charges.

## Outbound Traffic (Egress)

| Destination | Price |
|-------------|-------|
| Same region (VM to VM in same VPC) | Free |
| Same region (VM to VM in different VPC) | Free |
| Different Nirvana region | $0.02/GB |
| Internet (first 100 GB/month) | Free |
| Internet (after 100 GB/month) | $0.09/GB |

## Load Balancer Data Processing

- $0.008/GB for all data processed (inbound + outbound)

## VPN Traffic

- Site-to-site VPN: $0.05/GB for data transferred over the tunnel
- Client VPN: $0.05/GB per active VPN connection-hour

## DNS Queries

- First 1 billion queries/month: $0.40 per million queries
- Over 1 billion: $0.20 per million queries

## Free Data Transfer Use Cases

These are never charged for egress:
- Traffic between VMs in the same VPC
- Traffic to Nirvana Object Storage in the same region
- Traffic to the Nirvana API (api.nirvanacloud.io)
- Traffic within a Kubernetes cluster

## Tips to Reduce Egress Costs

1. Keep compute and storage in the same region.
2. Use a CDN (Nirvana CDN) to serve static assets — CDN-to-user traffic is
   cheaper than VM-to-user.
3. Compress data before transferring across regions.
4. Use Nirvana Object Storage cross-region replication only for critical data.

## Estimating Your Bill

Use the pricing calculator at nirvanacloud.io/pricing to estimate costs
based on your expected resource usage and data transfer patterns.
""",
    ),
    (
        "instance_metadata.md",
        "Instance Metadata Service",
        """\
# Instance Metadata Service (IMDS)

The Instance Metadata Service provides information about the running VM,
accessible from within the VM at `http://169.254.169.254`.

## Available Metadata

```bash
# VM ID
curl http://169.254.169.254/latest/meta-data/instance-id

# Instance type
curl http://169.254.169.254/latest/meta-data/instance-type

# Region
curl http://169.254.169.254/latest/meta-data/placement/region

# Public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Private IP
curl http://169.254.169.254/latest/meta-data/local-ipv4

# Hostname
curl http://169.254.169.254/latest/meta-data/hostname
```

## User Data

Access the user data script passed at VM creation:
```bash
curl http://169.254.169.254/latest/user-data
```

## Spot Instance Interruption Notice

Check if a spot instance is scheduled for interruption:
```bash
curl http://169.254.169.254/latest/meta-data/spot/termination-time
# Returns 404 if not being terminated
# Returns timestamp if termination is imminent
```

## IMDSv2 (Session-Oriented)

For enhanced security, use IMDSv2, which requires a session token:
```bash
TOKEN=$(curl -X PUT \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
  http://169.254.169.254/latest/api/token)

curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id
```

## Restricting IMDS Access

Prevent container escapes from accessing IMDS:
```bash
# Block IMDS from Docker containers
iptables -I DOCKER-USER -d 169.254.169.254 -j REJECT
```

## Use Cases

- Auto-discover VM ID and region for logging and monitoring.
- Detect spot interruption in application code.
- Bootstrap configuration without hardcoding values.
""",
    ),
    (
        "private_images.md",
        "Custom VM Images",
        """\
# Custom VM Images

Build and reuse a custom VM image to standardise your environment and speed up
VM provisioning.

## Building an Image

### Step 1: Prepare a Base VM

1. Launch a VM from a base image (e.g., Ubuntu 22.04).
2. Install your software and apply your configuration:
   ```bash
   sudo apt update && sudo apt install -y docker.io python3-pip
   pip3 install fastapi uvicorn
   # Configure OS settings, users, etc.
   ```
3. Clean up before snapshotting:
   ```bash
   sudo cloud-init clean --logs
   sudo rm -rf /tmp/* /var/log/*
   sudo history -c
   ```

### Step 2: Create an Image from the VM

**Dashboard**: VM Actions → Create Image.

**API**:
```bash
curl -X POST https://api.nirvanacloud.io/v1/vms/<id>/image \
  -H "Authorization: Bearer <key>" \
  -d '{"name": "my-app-base-v1.0"}'
```

The VM is stopped during the image capture and restarted afterwards.

## Using Your Image

When creating a new VM, select **My Images** and choose the custom image.

**Terraform**:
```hcl
resource "nirvana_vm" "worker" {
  image = data.nirvana_image.my_image.id
}

data "nirvana_image" "my_image" {
  name = "my-app-base-v1.0"
}
```

## Sharing Images

Share an image across projects or with other accounts:
**Storage → Images → [Image] → Share → Enter account ID or project**.

## Image Versioning

Name images with version suffixes (`v1.0`, `v1.1`) and keep the last 3 versions.
Delete old images to avoid storage charges ($0.05/GB/month).

## Packer Integration

Automate image builds with HashiCorp Packer:
```hcl
source "nirvana" "ubuntu" {
  api_key       = var.nirvana_api_key
  instance_type = "standard-2"
  source_image  = "ubuntu-22-04"
}

build {
  provisioner "shell" {
    script = "setup.sh"
  }
}
```
""",
    ),
]

# ---------------------------------------------------------------------------
# Ticket generation
# ---------------------------------------------------------------------------

_TIERS = ["Free", "Pro", "Business", "Enterprise"]
_STATUSES = ["resolved", "resolved", "resolved", "open", "escalated"]

_TICKET_TEMPLATES: list[tuple[str, str, str]] = [
    # (subject, description_template, resolution_template)
    (
        "Cannot log in after password reset",
        "Customer reset password but login still fails with invalid credentials error.",
        "Cleared auth cache and guided customer to log in via incognito window. Resolved.",
    ),
    (
        "VM stuck in Pending state",
        "Launched a {instance} instance in {region}; still shows Pending after {minutes} minutes.",
        "Capacity was temporarily exhausted in {region}. VM launched after manual intervention by ops team.",
    ),
    (
        "SSH connection refused on port 22",
        "Cannot SSH into VM after reboot. Getting 'Connection refused' on port 22.",
        "Firewall rule for TCP 22 was inadvertently removed. Added rule back via dashboard.",
    ),
    (
        "Volume not mounting after VM reboot",
        "Attached volume /dev/vdb disappears after VM restart. Need to remount manually each time.",
        "Added persistent mount entry to /etc/fstab: /dev/vdb /data ext4 defaults,nofail 0 2",
    ),
    (
        "Account locked after failed login attempts",
        "Customer locked out after {n} failed login attempts. Cannot reset password via email.",
        "Unlocked account manually. Guided customer through password reset and 2FA setup.",
    ),
    (
        "High outbound data transfer charges",
        "Monthly bill is {x}x higher than expected. Suspecting unexpected data transfer fees.",
        "Found misconfigured backup job sending {tb}TB/day to S3-compatible endpoint. Fixed job config.",
    ),
    (
        "GPU instance VRAM lower than spec",
        "gpu-small shows {vram}GB VRAM instead of 16GB as advertised.",
        "{reserved}GB is reserved per GPU for ECC error correction. Documentation updated to clarify.",
    ),
    (
        "Snapshot restore failed",
        "Attempting to restore snapshot snap_{id} results in 'Restore failed' error.",
        "Engineering investigated. Snapshot had filesystem corruption. Customer took new snapshot successfully.",
    ),
    (
        "Cannot connect to VM after firewall rule change",
        "Added a new firewall rule to restrict SSH. Now locked out completely.",
        "Accessed VM via console and corrected firewall rules. Added a 'allow from admin IP' rule.",
    ),
    (
        "VM paused unexpectedly on free tier",
        "Free tier VM paused without warning after {days} days of activity.",
        "Free tier VMs are paused after 30 days of inactivity. Customer restarted and upgraded to Pro.",
    ),
    (
        "Payment method declined",
        "Credit card is being declined on payment form even though card is valid.",
        "Card processor flagged transaction as suspicious. Customer tried a different card successfully.",
    ),
    (
        "Slow disk I/O on Standard SSD volume",
        "Database queries taking {x}x longer than expected. Disk throughput appears throttled.",
        "Standard SSD burst credits were exhausted. Upgraded customer to Performance SSD volume.",
    ),
    (
        "MFA device lost, cannot log in",
        "Lost phone with authenticator app. Cannot use backup codes (also lost).",
        "Verified identity via out-of-band process. Disabled MFA. Customer re-enrolled on new device.",
    ),
    (
        "Kubernetes node not joining cluster",
        "Added new node pool to NKS cluster. Nodes stay in NotReady state.",
        "Incorrect kubeadm token. Ran 'kubeadm token create' and re-joined nodes. All nodes Ready.",
    ),
    (
        "Object storage bucket returns 403",
        "S3-compatible API returns 403 Forbidden on all GET requests to bucket.",
        "Bucket ACL was set to private. Customer updated bucket policy to allow their service account.",
    ),
    (
        "Load balancer health check failing",
        "Backend VMs are healthy but load balancer shows them as unhealthy.",
        "Health check path was /healthz but app serves /health. Updated health check path in LB config.",
    ),
    (
        "Cannot resize VM - option greyed out",
        "Resize option is greyed out in the dashboard for running VM.",
        "VM must be stopped before resizing. Guided customer through stop → resize → start workflow.",
    ),
    (
        "Terraform provider authentication error",
        "Terraform apply fails with: 'invalid API key' even though key is correct.",
        "API key had trailing newline in the environment variable. Fixed with: export NIRVANA_API_KEY=$(cat key.txt | tr -d '\\n')",
    ),
    (
        "DNS record not propagating",
        "Updated A record {hours} hours ago but domain still resolves to old IP.",
        "Old TTL of 86400s was still in effect. Had to wait for TTL expiry. Lowered TTL to 300s going forward.",
    ),
    (
        "Requesting refund for unused subscription",
        "Customer cancelled service and wants a prorated refund for {days} unused days.",
        "Per refund policy, prorated refund issued for unused days. Credit applied to payment method.",
    ),
    (
        "VPN tunnel keeps dropping",
        "Site-to-site VPN tunnel disconnects every {minutes} minutes. IKEv2 session expires.",
        "IKE lifetime mismatch between Nirvana and customer router. Aligned to 28800s / 3600s. Stable since.",
    ),
    (
        "Container image push fails with 401",
        "Docker push to Nirvana Container Registry fails with 'unauthorized' error.",
        "API key used for auth had expired. Generated new key and re-ran 'docker login'.",
    ),
    (
        "High CPU alert not triggering",
        "CPU has been at 100% for {minutes} minutes but no alert was received.",
        "Alert evaluation window was set to 30 minutes. Customer lowered to 5 minutes. Alert fired correctly.",
    ),
    (
        "Invoice shows incorrect company name",
        "Company name on invoice is {wrong} instead of the legal entity name.",
        "Updated organisation name in Settings → Profile. Reissued invoice with correct company name.",
    ),
    (
        "SSH key rejected on existing VM",
        "Added new SSH public key in settings but cannot log in with it on existing VM.",
        "SSH keys must be associated at VM creation time. Guided customer to create snapshot and relaunch.",
    ),
    (
        "Spot instance interrupted during training",
        "ML training job interrupted due to spot instance reclamation. Lost 4 hours of progress.",
        "Advised enabling checkpointing every 30 minutes and using a persistent volume for checkpoints.",
    ),
    (
        "Network latency between VMs is high",
        "Ping between two VMs in same region is {ms}ms. Expected <5ms.",
        "VMs were in different physical availability zones. Live-migrated one VM. Latency now <1ms.",
    ),
    (
        "Webhook not receiving events",
        "Configured webhook endpoint but not receiving any events after {hours} hours.",
        "Endpoint was returning 500 on Nirvana's test event. After fixing endpoint, events arrived within seconds.",
    ),
    (
        "Outbound email from VM being rejected",
        "Emails sent from VM on port 25 are rejected by receiving mail servers.",
        "Port 25 is blocked by default. Customer switched to port 587 (SMTP submission) via SendGrid relay.",
    ),
    (
        "Kubernetes PVC stuck in Pending",
        "PersistentVolumeClaim stays Pending. Pod cannot schedule.",
        "StorageClass was not set to 'nirvana-block'. Updated PVC manifest with correct storageClassName.",
    ),
    (
        "Free tier credit not applied",
        "Account shows $0 credits despite signing up within trial period.",
        "Credit promotion code was not entered at signup. Applied credit manually after verification.",
    ),
    (
        "SSO login loop",
        "After configuring SAML SSO, login redirects in a loop without completing.",
        "ACS URL in IdP config had a trailing slash mismatch. Corrected URL. SSO working correctly.",
    ),
    (
        "VM shows wrong timezone",
        "System clock on VM is off by {hours} hours. Services logging in wrong timezone.",
        "Guided customer to set timezone: timedatectl set-timezone UTC. Advised using UTC for all servers.",
    ),
    (
        "Object storage upload times out for large files",
        "Uploading files over {size}GB times out partway through.",
        "Switched to multipart upload (aws s3 cp with default multipart threshold). Upload completed successfully.",
    ),
    (
        "Auto-scaling not triggering scale-out",
        "CPU consistently above 80% but scaling group is not adding VMs.",
        "Scaling policy evaluation window was 30 minutes. Lowered to 5 minutes. Scale-out now triggers correctly.",
    ),
    (
        "Cannot delete VM - shows error",
        "Attempting to delete VM results in 'resource in use' error.",
        "VM had an attached floating IP. Detached floating IP first, then deleted VM successfully.",
    ),
    (
        "API rate limit hit unexpectedly",
        "Application receiving 429 responses from Nirvana API during peak hours.",
        "Application was polling VM status every second. Switched to webhook events. Rate limit no longer hit.",
    ),
    (
        "Windows VM cannot activate",
        "Windows Server VM showing activation error after launch.",
        "Nirvana uses KMS activation on an internal server. Configured Windows KMS client key and pointed to internal KMS.",
    ),
    (
        "Requesting P1 escalation for production outage",
        "Production system is completely down. {n} customers affected. Revenue impact.",
        "Escalated to Tier 4 engineering. Root cause: network switch failure in rack. VMs live-migrated. Resolved in {minutes} minutes.",
    ),
    (
        "Data transfer between regions charged unexpectedly",
        "Expected cross-region transfer to be free but being charged $0.02/GB.",
        "Cross-region transfer is $0.02/GB per pricing policy. Advised using object storage replication for bulk transfers.",
    ),
    (
        "Cannot enable IPv6 on existing VPC",
        "Option to enable IPv6 is greyed out on an existing VPC.",
        "IPv6 can only be enabled on VPCs created after June 2024. Guided customer to create a new VPC with IPv6 enabled.",
    ),
]


def _make_ticket(row_num: int) -> dict[str, str]:
    import random
    rng = random.Random(row_num)  # deterministic per row
    tmpl = _TICKET_TEMPLATES[row_num % len(_TICKET_TEMPLATES)]
    subject, desc_tmpl, res_tmpl = tmpl
    tier = _TIERS[rng.randint(0, len(_TIERS) - 1)]
    status = _STATUSES[rng.randint(0, len(_STATUSES) - 1)]

    fmt = {
        "instance": rng.choice(["standard-4", "gpu-small", "standard-8", "gpu-medium"]),
        "region": rng.choice(["us-east-1", "eu-west-1", "ap-south-1"]),
        "minutes": rng.choice([5, 10, 15, 20, 30]),
        "days": rng.randint(1, 30),
        "hours": rng.randint(2, 48),
        "n": rng.choice([5, 10, 3]),
        "x": rng.choice([2, 3, 5, 10]),
        "tb": rng.choice([1, 2, 5]),
        "vram": rng.choice([14, 14.5, 15]),
        "reserved": rng.choice([1, 1.5, 2]),
        "id": row_num * 7 + 100,
        "ms": rng.choice([20, 40, 80]),
        "wrong": "Nirvana Inc.",
        "size": rng.choice([5, 10, 20]),
    }

    description = desc_tmpl.format_map({k: fmt.get(k, f"{{{k}}}") for k in fmt})
    resolution = res_tmpl.format_map({k: fmt.get(k, f"{{{k}}}") for k in fmt})

    month = (row_num % 12) + 1
    day = (row_num % 28) + 1
    date = f"2024-{month:02d}-{day:02d}"

    return {
        "ticket_id": f"T-{row_num + 1:04d}",
        "date": date,
        "customer_tier": tier,
        "subject": subject,
        "description": description,
        "status": status,
        "resolution": resolution if status in ("resolved", "escalated") else "",
    }


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_medium() -> None:
    print("Generating data/medium/ ...")

    if MEDIUM.exists():
        shutil.rmtree(MEDIUM)
    MEDIUM.mkdir(parents=True)

    # Copy everything from small
    _ = shutil.copytree(SMALL, MEDIUM, dirs_exist_ok=True)
    print(f"  Copied {len(list(SMALL.rglob('*')))} files from data/small/")

    # Write extra help center articles
    articles_dir = MEDIUM / "help_center_articles"
    articles_dir.mkdir(exist_ok=True)
    for filename, _title, content in ARTICLES:
        _ = (articles_dir / filename).write_text(content, encoding="utf-8")
    print(f"  Generated {len(ARTICLES)} additional help center articles")

    # Generate 2000-row tickets CSV
    tickets_path = MEDIUM / "sample_tickets.csv"
    fieldnames = ["ticket_id", "date", "customer_tier", "subject", "description", "status", "resolution"]
    with tickets_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(2000):
            writer.writerow(_make_ticket(i))
    print("  Generated 2000-row sample_tickets.csv")

    total_bytes = sum(p.stat().st_size for p in MEDIUM.rglob("*") if p.is_file())
    print(f"  Total size: {total_bytes / 1024:.0f} KB")
    print("Done. data/medium/ is ready.")


if __name__ == "__main__":
    generate_medium()
