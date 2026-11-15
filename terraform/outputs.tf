output "vpc_id" {
  description = "The AWS Hub VPC ID"
  value       = module.aws_hub.vpc_id
}

output "vpc_cidr" {
  description = "The AWS Hub VPC CIDR"
  value       = var.vpc_cidr_aws
}

output "gcp_network_name" {
  description = "The GCP Spoke VPC network name"
  value       = module.gcp_spoke.network_name
}
