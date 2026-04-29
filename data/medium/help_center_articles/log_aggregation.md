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
