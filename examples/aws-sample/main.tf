terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name                 = "nit-fabric-sample-vpc"
    "nit-fabric:managed" = "true"
  }
}

# VIOLATION: VPC Flow Logs not enabled
# (Missing aws_flow_log resource)

# VIOLATION: Public S3 Bucket
resource "aws_s3_bucket" "public_data" {
  bucket = "nit-fabric-public-data-bucket"

  tags = {
    "nit-fabric:managed" = "true"
  }
}

resource "aws_s3_bucket_public_access_block" "bad_config" {
  bucket = aws_s3_bucket.public_data.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# VIOLATION: S3 Bucket Versioning Disabled
resource "aws_s3_bucket_versioning" "disabled" {
  bucket = aws_s3_bucket.public_data.id
  versioning_configuration {
    status = "Disabled"
  }
}

# VIOLATION: Missing VPC Endpoints
# (Missing aws_vpc_endpoint for s3, kms)

# VIOLATION: Missing TGW Attachment
# (VPC exists but no aws_ec2_transit_gateway_vpc_attachment)
