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
