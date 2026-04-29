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
