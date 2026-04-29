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
