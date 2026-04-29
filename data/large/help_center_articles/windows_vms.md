# Windows VMs on Nirvana Cloud

## Available Windows Images

| Image | License | Notes |
|-------|---------|-------|
| Windows Server 2022 Standard | Included in VM price | Most common for production |
| Windows Server 2022 Datacenter | Included | Unlimited Windows VMs for nested virtualisation |
| Windows Server 2019 Standard | Included | LTS option |
| Windows 11 Pro | Additional license fee | Desktop workloads |

## Launching a Windows VM

1. When creating a VM, select the **Windows Server 2022** image.
2. Set the administrator password in the **User Data** field:
   ```
   <powershell>
   net user Administrator "YourStrongPassword123!"
   </powershell>
   ```
3. Ensure port **3389 (RDP)** is open in firewall rules.
4. After boot (~3 minutes), connect via Remote Desktop.

## RDP Connection

**Windows**: Open Remote Desktop Connection → enter the VM's public IP.

**macOS**: Use Microsoft Remote Desktop (from the Mac App Store).

**Linux**:
```bash
xfreerdp /v:<vm-ip> /u:Administrator /p:'YourPassword'
```

## WinRM (Remote Management)

For automated configuration with Ansible or PowerShell remoting:
```powershell
# Run on the VM after first login
Enable-PSRemoting -Force
```

Allow port 5985 (WinRM HTTP) or 5986 (WinRM HTTPS) in firewall rules.

## Windows Firewall

The Windows built-in firewall applies in addition to the Nirvana VM firewall.
If a port is open in Nirvana but still unreachable, check Windows Firewall rules:
```powershell
New-NetFirewallRule -DisplayName "My App" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

## Pricing

Windows VMs are billed at the same compute rate as Linux VMs. Windows Server
licenses are included in the price.
