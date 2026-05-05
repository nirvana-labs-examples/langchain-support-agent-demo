variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
}

variable "skip_nirvana" {
  description = "When true, skip provisioning the Nirvana VPC + VM. Use this when you only have AWS credentials."
  type        = bool
  default     = false
}

variable "skip_aws" {
  description = "When true, skip provisioning all AWS resources (VPC + 4 instances). Use this when you only want to benchmark Nirvana."
  type        = bool
  default     = false
}

variable "skip_io2" {
  description = "When true, skip the io2 EBS variants. Useful when the account io2 IOPS quota is constrained (default 100,000 IOPS region-wide)."
  type        = bool
  default     = false
}

variable "nirvana_project_id" {
  description = "Nirvana project ID (from the Nirvana dashboard). Required only when skip_nirvana=false."
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-1"
}

variable "nirvana_region" {
  description = "Nirvana region"
  type        = string
  default     = "us-sva-2"
}

variable "aws_instance_type" {
  description = "AWS EC2 instance type. m6i.xlarge gives 4 vCPU / 16 GB RAM and a 40k IOPS instance ceiling, matching n1-standard-4."
  type        = string
  default     = "m6i.xlarge"
}

variable "aws_storage_size" {
  description = "AWS root volume size in GB"
  type        = number
  default     = 256
}

variable "nirvana_instance_type" {
  description = "Nirvana VM instance type"
  type        = string
  default     = "n1-standard-4"
}

variable "nirvana_storage_size" {
  description = "Nirvana boot volume size in GB"
  type        = number
  default     = 256
}

variable "nirvana_storage_type" {
  description = "Nirvana storage type. abs = Accelerated Block Storage."
  type        = string
  default     = "abs"
}
