# Nirvana Cloud Onboarding Guide

## Welcome

This guide walks you through your first 30 minutes on Nirvana Cloud, from account creation
to launching your first virtual machine.

## Step 1: Create Your Account

1. Visit app.nirvanacloud.io and click **Get Started**.
2. Enter your email address and choose a strong password.
3. Verify your email by clicking the link we send you.
4. Complete your organization profile (name, billing contact).

## Step 2: Add a Payment Method

1. Navigate to **Settings → Billing**.
2. Add a credit card or bank account.
3. For Enterprise customers, contact sales@nirvanacloud.io to set up invoice billing.

## Step 3: Create Your First VM

1. From the dashboard, click **+ New VM**.
2. Select a region (us-east-1, eu-west-1, ap-south-1).
3. Choose an instance type. For AI workloads, we recommend **GPU-optimized** instances.
4. Select an operating system (Ubuntu 22.04 LTS recommended).
5. Upload your SSH public key or let us generate a key pair.
6. Click **Launch**.

## Step 4: Attach Block Storage

1. Navigate to **Storage → Volumes**.
2. Click **+ Create Volume**.
3. Choose size (minimum 10 GB, maximum 64 TB per volume).
4. Attach the volume to your running VM.
5. SSH into your VM and mount the volume:
   ```
   sudo mkfs.ext4 /dev/vdb
   sudo mount /dev/vdb /data
   ```

## Step 5: Connect via SSH

```
ssh -i ~/.ssh/nirvana_key ubuntu@<your-vm-ip>
```

## Troubleshooting Login Issues

- **Forgot password**: Use the "Reset Password" link on the login page.
- **SSH key rejected**: Verify the public key was added before VM creation. Re-adding a key
  requires stopping and recreating the VM.
- **Account locked**: After 5 failed login attempts, accounts are locked for 15 minutes.
  Contact support@nirvanacloud.io to unlock immediately.

## Common First-Day Issues

### "VM stuck in Pending state"

VMs typically start within 60 seconds. If your VM is pending for more than 5 minutes,
try stopping and restarting it. If the issue persists, open a support ticket.

### "Cannot connect to VM"

1. Verify the VM is in **Running** state.
2. Check that port 22 is open in your firewall rules.
3. Confirm you are using the correct SSH key.

## Getting Help

- Documentation: docs.nirvanacloud.io
- Support portal: support.nirvanacloud.io
- Status page: status.nirvanacloud.io
