# IAM & Access Control

Nirvana Cloud uses role-based access control (RBAC) to manage who can do what within
your organization.

## Roles

| Role | Permissions |
|------|-------------|
| Owner | Full access including billing and member management |
| Admin | Full resource access; cannot modify billing or remove Owners |
| Developer | Create/manage VMs, storage, networking; read-only billing |
| Viewer | Read-only access to all resources |
| Billing | Read/write billing and invoices only |

## Inviting Team Members

1. Navigate to **Settings → Team → + Invite Member**.
2. Enter the email address and select a role.
3. The invitee receives an email to accept and set a password.

## Service Accounts

Service accounts are machine identities for automated workloads (CI/CD, scripts, Terraform):

1. **Settings → Service Accounts → + Create**.
2. Assign a role (prefer least-privilege: Viewer or Developer).
3. Generate an API key for the service account.
4. Use the key in your automation — it never expires unless rotated manually.

## API Keys

Personal API keys are scoped to your user account:
- **Settings → API Keys → + Create Key**.
- Label keys by purpose (e.g., `terraform-prod`, `local-dev`).
- Rotate keys regularly; revoke any that are no longer needed.

## Resource-Level Permissions (Enterprise)

Enterprise plans support resource-level policies to restrict access to specific
VMs, buckets, or VPCs by user or service account.

## Audit Log

All API calls and dashboard actions are recorded:
- **Settings → Audit Log**.
- Filter by user, action type, or resource.
- Export to CSV or stream to an external SIEM via webhook.

## SSO Integration

See the dedicated **SSO Configuration** article for SAML/OIDC setup.
