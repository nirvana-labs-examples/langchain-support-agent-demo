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
