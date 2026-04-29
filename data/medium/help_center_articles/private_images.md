# Custom VM Images

Build and reuse a custom VM image to standardise your environment and speed up
VM provisioning.

## Building an Image

### Step 1: Prepare a Base VM

1. Launch a VM from a base image (e.g., Ubuntu 22.04).
2. Install your software and apply your configuration:
   ```bash
   sudo apt update && sudo apt install -y docker.io python3-pip
   pip3 install fastapi uvicorn
   # Configure OS settings, users, etc.
   ```
3. Clean up before snapshotting:
   ```bash
   sudo cloud-init clean --logs
   sudo rm -rf /tmp/* /var/log/*
   sudo history -c
   ```

### Step 2: Create an Image from the VM

**Dashboard**: VM Actions → Create Image.

**API**:
```bash
curl -X POST https://api.nirvanacloud.io/v1/vms/<id>/image   -H "Authorization: Bearer <key>"   -d '{"name": "my-app-base-v1.0"}'
```

The VM is stopped during the image capture and restarted afterwards.

## Using Your Image

When creating a new VM, select **My Images** and choose the custom image.

**Terraform**:
```hcl
resource "nirvana_vm" "worker" {
  image = data.nirvana_image.my_image.id
}

data "nirvana_image" "my_image" {
  name = "my-app-base-v1.0"
}
```

## Sharing Images

Share an image across projects or with other accounts:
**Storage → Images → [Image] → Share → Enter account ID or project**.

## Image Versioning

Name images with version suffixes (`v1.0`, `v1.1`) and keep the last 3 versions.
Delete old images to avoid storage charges ($0.05/GB/month).

## Packer Integration

Automate image builds with HashiCorp Packer:
```hcl
source "nirvana" "ubuntu" {
  api_key       = var.nirvana_api_key
  instance_type = "standard-2"
  source_image  = "ubuntu-22-04"
}

build {
  provisioner "shell" {
    script = "setup.sh"
  }
}
```
