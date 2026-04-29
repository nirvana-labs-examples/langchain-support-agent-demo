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
