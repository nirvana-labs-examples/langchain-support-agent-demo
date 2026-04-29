# Nirvana Cloud Terraform Provider

## Installation

Add the provider to your Terraform configuration:

```hcl
terraform {
  required_providers {
    nirvana = {
      source  = "nirvana-labs/nirvana"
      version = "~> 1.0"
    }
  }
}

provider "nirvana" {
  api_key = var.nirvana_api_key
  region  = "us-east-1"
}
```

Run `terraform init` to download the provider.

## Creating a VM

```hcl
resource "nirvana_vm" "web" {
  name          = "web-server"
  instance_type = "standard-2"
  image         = "ubuntu-22-04"
  region        = "us-east-1"
  ssh_key_ids   = [nirvana_ssh_key.my_key.id]

  network_interface {
    vpc_id    = nirvana_vpc.main.id
    subnet_id = nirvana_subnet.public.id
    public_ip = true
  }
}
```

## Attaching a Volume

```hcl
resource "nirvana_volume" "data" {
  name   = "data-volume"
  size   = 100
  region = "us-east-1"
}

resource "nirvana_volume_attachment" "attach" {
  vm_id     = nirvana_vm.web.id
  volume_id = nirvana_volume.data.id
}
```

## State Backend

Store Terraform state in Nirvana Object Storage:

```hcl
terraform {
  backend "s3" {
    bucket   = "my-tf-state"
    key      = "prod/terraform.tfstate"
    region   = "us-east-1"
    endpoint = "https://storage.nirvanacloud.io"
    # disable AWS-specific features
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
  }
}
```

## Importing Existing Resources

```bash
terraform import nirvana_vm.web vm_abc123
```

## Docs

Full resource reference: docs.nirvanacloud.io/terraform
