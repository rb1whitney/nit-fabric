output "vpc_id" {
  description = "The VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "The VPC CIDR"
  value       = var.vpc_cidr_aws
}

output "eks_cluster_name" {
  description = "The EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "The EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC provider for IRSA"
  value       = module.eks.oidc_provider_arn
}

output "oidc_provider_url" {
  description = "The URL of the OIDC provider for IRSA"
  value       = module.eks.oidc_provider
}

output "project_account_id" {
  description = "The AWS Account ID of the project account"
  value       = module.org.account_id
}
