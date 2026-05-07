terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    nirvana = {
      source  = "nirvana-labs/nirvana"
      version = "~> 1.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Bypass STS/IMDS validation at plan time so skip_aws=true works without
  # AWS credentials. Creating real AWS resources still requires valid creds.
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

provider "nirvana" {}

# =============================================================================
# AWS NETWORKING
# =============================================================================

data "aws_ami" "ubuntu" {
  count       = var.skip_aws ? 0 : 1
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_vpc" "benchmark" {
  count                = var.skip_aws ? 0 : 1
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = "support-bench-vpc" }
}

resource "aws_internet_gateway" "benchmark" {
  count  = var.skip_aws ? 0 : 1
  vpc_id = aws_vpc.benchmark[0].id
  tags   = { Name = "support-bench-igw" }
}

resource "aws_subnet" "benchmark" {
  count                   = var.skip_aws ? 0 : 1
  vpc_id                  = aws_vpc.benchmark[0].id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags                    = { Name = "support-bench-subnet" }
}

resource "aws_route_table" "benchmark" {
  count  = var.skip_aws ? 0 : 1
  vpc_id = aws_vpc.benchmark[0].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.benchmark[0].id
  }
  tags = { Name = "support-bench-rt" }
}

resource "aws_route_table_association" "benchmark" {
  count          = var.skip_aws ? 0 : 1
  subnet_id      = aws_subnet.benchmark[0].id
  route_table_id = aws_route_table.benchmark[0].id
}

resource "aws_security_group" "benchmark" {
  count       = var.skip_aws ? 0 : 1
  name        = "support-bench-sg"
  description = "Allow SSH and Qdrant from anywhere (benchmark VMs are short-lived)"
  vpc_id      = aws_vpc.benchmark[0].id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 6333
    to_port     = 6334
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "support-bench-sg" }
}

resource "aws_key_pair" "benchmark" {
  count      = var.skip_aws ? 0 : 1
  key_name   = "support-bench-key"
  public_key = var.ssh_public_key
}

# =============================================================================
# AWS INSTANCES — one per storage variant
# Storage type drives the IOPS difference; instance type stays constant.
# Qdrant data is stored on the root volume, so root_block_device IOPS = the
# storage being benchmarked.
# =============================================================================

resource "aws_instance" "gp3_3k" {
  count                  = var.skip_aws ? 0 : 1
  ami                    = data.aws_ami.ubuntu[0].id
  instance_type          = var.aws_instance_type
  subnet_id              = aws_subnet.benchmark[0].id
  vpc_security_group_ids = [aws_security_group.benchmark[0].id]
  key_name               = aws_key_pair.benchmark[0].key_name

  root_block_device {
    volume_size = var.aws_storage_size
    volume_type = "gp3"
    iops        = 3000
    throughput  = 125
  }

  tags = { Name = "support-bench-gp3-3k" }
}

resource "aws_instance" "gp3_16k" {
  count                  = var.skip_aws ? 0 : 1
  ami                    = data.aws_ami.ubuntu[0].id
  instance_type          = var.aws_instance_type
  subnet_id              = aws_subnet.benchmark[0].id
  vpc_security_group_ids = [aws_security_group.benchmark[0].id]
  key_name               = aws_key_pair.benchmark[0].key_name

  root_block_device {
    volume_size = var.aws_storage_size
    volume_type = "gp3"
    iops        = 16000
    throughput  = 1000
  }

  tags = { Name = "support-bench-gp3-16k" }
}

resource "aws_instance" "io2_32k" {
  count                  = var.skip_aws || var.skip_io2 ? 0 : 1
  ami                    = data.aws_ami.ubuntu[0].id
  instance_type          = var.aws_instance_type
  subnet_id              = aws_subnet.benchmark[0].id
  vpc_security_group_ids = [aws_security_group.benchmark[0].id]
  key_name               = aws_key_pair.benchmark[0].key_name

  root_block_device {
    volume_size = var.aws_storage_size
    volume_type = "io2"
    iops        = 32000
  }

  tags = { Name = "support-bench-io2-32k" }
}

resource "aws_instance" "io2_64k" {
  count                  = var.skip_aws || var.skip_io2 ? 0 : 1
  ami                    = data.aws_ami.ubuntu[0].id
  instance_type          = var.aws_instance_type
  subnet_id              = aws_subnet.benchmark[0].id
  vpc_security_group_ids = [aws_security_group.benchmark[0].id]
  key_name               = aws_key_pair.benchmark[0].key_name

  root_block_device {
    volume_size = var.aws_storage_size
    volume_type = "io2"
    iops        = 64000
  }

  tags = { Name = "support-bench-io2-64k" }
}

# =============================================================================
# NIRVANA RESOURCES
# =============================================================================

resource "nirvana_networking_vpc" "benchmark" {
  count       = var.skip_nirvana ? 0 : 1
  name        = "support-bench-vpc"
  region      = var.nirvana_region
  project_id  = var.nirvana_project_id
  subnet_name = "support-bench-subnet"
}

resource "nirvana_networking_firewall_rule" "ssh" {
  count               = var.skip_nirvana ? 0 : 1
  vpc_id              = nirvana_networking_vpc.benchmark[0].id
  name                = "support-bench-ssh"
  protocol            = "tcp"
  source_address      = "0.0.0.0/0"
  destination_address = nirvana_networking_vpc.benchmark[0].subnet.cidr
  destination_ports   = ["22"]
}

resource "nirvana_networking_firewall_rule" "qdrant" {
  count               = var.skip_nirvana ? 0 : 1
  vpc_id              = nirvana_networking_vpc.benchmark[0].id
  name                = "support-bench-qdrant"
  protocol            = "tcp"
  source_address      = "0.0.0.0/0"
  destination_address = nirvana_networking_vpc.benchmark[0].subnet.cidr
  destination_ports   = ["6333", "6334"]
}

resource "nirvana_compute_vm" "benchmark" {
  count             = var.skip_nirvana ? 0 : 1
  name              = "support-bench-nirvana"
  region            = var.nirvana_region
  project_id        = var.nirvana_project_id
  instance_type     = var.nirvana_instance_type
  os_image_name     = "ubuntu-noble-2025-10-01"
  boot_volume       = { size = var.nirvana_storage_size, type = var.nirvana_storage_type }
  public_ip_enabled = true
  subnet_id         = nirvana_networking_vpc.benchmark[0].subnet.id
  ssh_key           = { public_key = var.ssh_public_key }

  depends_on = [
    nirvana_networking_firewall_rule.ssh,
    nirvana_networking_firewall_rule.qdrant,
  ]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "gp3_3k_ip" {
  value       = var.skip_aws ? "" : aws_instance.gp3_3k[0].public_ip
  description = "AWS gp3 3,000 IOPS (empty when skip_aws=true)"
}

output "gp3_16k_ip" {
  value       = var.skip_aws ? "" : aws_instance.gp3_16k[0].public_ip
  description = "AWS gp3 16,000 IOPS (empty when skip_aws=true)"
}

output "io2_32k_ip" {
  value       = var.skip_aws || var.skip_io2 ? "" : aws_instance.io2_32k[0].public_ip
  description = "AWS io2 32,000 IOPS (empty when skip_aws or skip_io2 = true)"
}

output "io2_64k_ip" {
  value       = var.skip_aws || var.skip_io2 ? "" : aws_instance.io2_64k[0].public_ip
  description = "AWS io2 64,000 IOPS (empty when skip_aws or skip_io2 = true)"
}

output "nirvana_ip" {
  value       = var.skip_nirvana ? "" : nirvana_compute_vm.benchmark[0].public_ip
  description = "Nirvana ABS (empty when skip_nirvana=true)"
}

output "aws_ami" {
  value       = var.skip_aws ? "" : data.aws_ami.ubuntu[0].name
  description = "AWS AMI used (empty when skip_aws=true)"
}

output "next_steps" {
  value = <<-EOT

    VMs ready. Next steps:
      1. ./infra/scripts/generate-inventory.sh
      2. cd infra/ansible && ansible-playbook playbook.yml

  EOT
}
