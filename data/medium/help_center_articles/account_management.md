# Account Management

## Changing Your Email Address

1. Navigate to **Settings → Profile → Email**.
2. Enter the new email and confirm your password.
3. A verification link is sent to both addresses.
4. Click the link in the new email to confirm the change.

Note: After changing your email, you must log in with the new address.
Existing API keys remain valid.

## Changing Your Password

1. **Settings → Security → Change Password**.
2. Enter your current password and the new password (minimum 12 characters).
3. All active sessions except the current one are invalidated.

## Closing Your Account

1. Ensure all resources are deleted (VMs, volumes, load balancers, buckets).
2. Download any invoices you need from **Settings → Billing → Invoice History**.
3. Navigate to **Settings → Account → Close Account**.
4. Confirm by entering your password.

Account closure is irreversible. Any remaining credits are forfeited.

## Account Suspension

Accounts are suspended when:
- Payment fails after 3 retries over 7 days.
- Suspected abuse (automated policy enforcement).
- Violation of the Terms of Service.

To reactivate after payment failure: update your payment method in **Settings → Billing**.
For other suspension reasons, contact support@nirvanacloud.io.

## Multiple Accounts

You may create multiple Nirvana accounts using different email addresses.
For team access, use the Team Management feature instead of sharing credentials.

## Two-Person Rule (Enterprise)

Require two administrators to approve sensitive actions (account closure, large
resource deletions, billing changes):
**Settings → Security → Two-Person Rule → Enable**.
