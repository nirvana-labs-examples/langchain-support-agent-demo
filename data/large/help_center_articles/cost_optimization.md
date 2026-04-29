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
