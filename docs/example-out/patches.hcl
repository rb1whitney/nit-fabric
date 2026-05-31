Harden S3 Bucket prod-public-bucket
# File: modules/storage/s3.tf
resource "aws_s3_bucket_public_access_block" "harden" {
  bucket = "prod-public-bucket"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

Remove external IP from insecure-instance
# File: modules/compute/gce.tf
- access_config {} # Removed external IP block