# nit-fabric Examples

This directory contains sample AWS and GCP infrastructure definitions (Terraform) designed to be scanned by `nit-fabric`.

## Structure

- `aws-sample/`: AWS resources with security violations.
- `gcp-sample/`: GCP resources with security violations.

## Included Violations

### AWS Sample
- **S3 Public Access**: `nit-fabric-public-data-bucket` has Public Access Block disabled.
- **VPC Flow Logs**: Disabled for the main VPC.
- **S3 Versioning**: Disabled for the public bucket.
- **Missing VPC Endpoints**: S3 and KMS endpoints are missing, forcing traffic over the public internet.
- **Missing Transit Gateway**: VPC is not attached to the central TGW hub.

### GCP Sample
- **External IPs**: GCE instance `insecure-instance` has a public IP.
- **Unrestricted Ingress**: Firewall rule `allow-ssh-insecure` allows SSH (22) from `0.0.0.0/0`.
- **GKE Workload Identity**: Cluster `legacy-cluster` has Workload Identity disabled.
- **Private Google Access**: Subnet `insecure-subnet` has Private Google Access disabled.
- **Cloud SQL Public IP**: Database `public-db` has a public IP enabled.

## Scanning

To scan these resources with `nit-fabric` (once Terraform discovery is fully implemented):

```bash
nit-fabric scan --mode terraform
```

Currently, you can use these as templates for testing the remediation logic.
