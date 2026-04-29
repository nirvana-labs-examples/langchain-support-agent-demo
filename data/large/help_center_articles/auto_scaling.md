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
