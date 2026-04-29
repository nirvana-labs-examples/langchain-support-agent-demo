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
