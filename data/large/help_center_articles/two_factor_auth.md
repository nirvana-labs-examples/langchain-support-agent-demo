# Two-Factor Authentication (2FA)

Enabling 2FA adds a second verification step to your login, protecting your account
even if your password is compromised.

## Enabling 2FA

1. Navigate to **Settings → Security → Two-Factor Authentication**.
2. Click **Enable 2FA**.
3. Scan the QR code with an authenticator app (Google Authenticator, Authy, 1Password, etc.).
4. Enter the 6-digit code to confirm setup.
5. Save your backup codes in a secure location — these let you access your account
   if you lose your device.

## Backup Codes

Each account receives 10 single-use backup codes. Use one if you cannot access
your authenticator app:

- Navigate to **Settings → Security → View Backup Codes**.
- Each code can only be used once.
- Regenerate codes after using one: **Regenerate Backup Codes**.

## Lost Authenticator Device

If you lose your device and have no backup codes:

1. Contact support@nirvanacloud.io from your account's registered email.
2. We will verify your identity via an out-of-band process.
3. Once verified, support will disable 2FA so you can re-enrol.

## Organization-Wide 2FA Enforcement (Enterprise)

Require all team members to enable 2FA:
- **Settings → Security → Enforce 2FA for all members**.
- Members without 2FA will be locked out of the dashboard until they enrol.

## App-Specific Notes

- **Google Authenticator**: Does not support encrypted backups — use Authy or 1Password
  if you want cross-device sync.
- **Authy**: Supports multi-device sync and encrypted backups.
- **Hardware keys (YubiKey)**: FIDO2/WebAuthn support is available on Enterprise plans.
