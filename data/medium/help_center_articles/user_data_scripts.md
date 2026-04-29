# User Data / Cloud-Init Scripts

User data scripts run on first boot, allowing you to automate VM initialisation.

## Passing User Data

**Dashboard**: Expand **Advanced Options → User Data** when creating a VM.

**Terraform**:
```hcl
resource "nirvana_vm" "web" {
  user_data = file("cloud-init.yaml")
}
```

## Cloud-Config Syntax

```yaml
#cloud-config
packages:
  - docker.io
  - git
  - python3-pip

runcmd:
  - systemctl enable --now docker
  - git clone https://github.com/my-org/my-app /opt/my-app
  - cd /opt/my-app && docker compose up -d

write_files:
  - path: /etc/myapp/config.json
    content: |
      {"env": "production", "region": "us-east-1"}
    permissions: '0644'
```

## Shell Script

Prefix with `#!/bin/bash` for a plain shell script:
```bash
#!/bin/bash
set -e
apt update && apt install -y nginx
systemctl enable --now nginx
echo "Hello from Nirvana!" > /var/www/html/index.html
```

## Debugging

If your user data script fails:
```bash
# View cloud-init logs
sudo cat /var/log/cloud-init-output.log
sudo journalctl -u cloud-final
```

## Secrets in User Data

Avoid embedding secrets in user data (it's accessible via the metadata API).
Instead:
- Fetch secrets from Nirvana Object Storage at startup.
- Use environment variables passed via the Nirvana API (Enterprise).
- Use a secrets manager (Vault, AWS Secrets Manager with Nirvana).

## User Data Size Limit

Maximum size: 64 KB. For larger scripts, store the script in Object Storage
and use a minimal user data script to download and execute it.
