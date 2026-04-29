# Team Management

## Inviting Members

1. Navigate to **Settings → Team → + Invite Member**.
2. Enter the member's email and assign a role.
3. The invite expires after 7 days. Resend under **Pending Invites**.

## Managing Roles

Change a member's role:
**Settings → Team → [Member] → Edit Role**.

Available roles: Owner, Admin, Developer, Viewer, Billing.
See the **IAM & Access Control** article for permission details.

## Removing Members

1. **Settings → Team → [Member] → Remove Member**.
2. All API keys belonging to the member are immediately revoked.
3. Resources created by the member remain; ownership is not transferred.

## Groups (Enterprise)

Organise members into groups for bulk role assignment:
**Settings → Groups → + Create Group**.

Assign groups to projects:
**Project Settings → Members → + Add Group**.

## Projects

Projects provide a logical boundary for resources (VMs, volumes, networks):

1. **Projects → + Create Project**.
2. Assign members and their roles within this project.
3. Resources created within the project are billed to the project cost centre.

## Usage by Member

View resource usage broken down by team member:
**Settings → Billing → Cost Explorer → Group by User**.

## Off-boarding Checklist

When a member leaves:
- [ ] Remove from team (**Settings → Team → Remove**)
- [ ] Rotate any secrets they had access to
- [ ] Review and transfer ownership of any personal API keys
- [ ] Audit recent API calls in the Audit Log
