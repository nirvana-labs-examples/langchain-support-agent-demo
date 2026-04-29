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
