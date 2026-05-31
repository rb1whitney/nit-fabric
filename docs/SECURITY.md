# Multi-Cloud Network Auditor | Security & Governance Specification
*Zero-Trust Perimeter Isolation, Resource Policies, and Audit Logic*

---

## 1. Zero-Trust Transit Boundary Rules
Zero-Trust perimeter design mandates strict ingress and egress isolation at the multi-cloud transit interface.

### 1.1 AWS Transit Gateway Security Group (`terraform/boundary_rules.tf`)
The security group `aws_security_group.tgw_boundary` locks down all traffic entering and leaving the Transit Gateway:
* **Ingress Filtering**: Restricts source traffic strictly to the GCP VPC CIDR (`10.20.0.0/16`). All other external IP spaces are blocked at the edge.
* **Egress Lockdown**: Symmetrically, the egress rule permits outbound traffic only to the GCP VPC CIDR (`10.20.0.0/16`). Any attempt to communicate with unauthorized external IP addresses is rejected.

### 1.2 GCP Cloud Router Boundary Firewall (`terraform/boundary_rules.tf`)
Symmetrically, the GCP Cloud Router is protected by `google_compute_firewall.hub_boundary`:
* **Source IP Verification**: Only traffic originating from the AWS VPC CIDR (`10.10.0.0/16`) is permitted.
* **Target Isolation**: Placed directly on the secondary VPC network interface to defend against lateral movement.

> [!NOTE]
> **Tiered Security Architecture**: These CIDR-level perimeter rules represent **Tier-0 (Transit Boundary)** guardrails. They do not replace local application-level firewalls, security groups, or Service Mesh (Istio) controls, which operate at **Tier-1 (Workload Layer)** to enforce least-privilege down to specific ports and identities.

---

## 2. Resource Security Audits
`nit-fabric` programmatically enforces security hygiene across storage, compute, and container workloads.

### 2.1 AWS Storage Hardening (`AWS_PUBLIC_S3`)
The Policy Engine checks S3 buckets against two distinct threat vectors:
1. **Public Exposure**: Buckets configured with public visibility (e.g., `public_access: true`) without an associated account-level Public Access Block are flagged as `CRITICAL`.
2. **Default Encryption (SSE-KMS)**: Buckets must have default encryption enabled using KMS Customer Managed Keys (CMKs) to defend against physical media theft or unauthorized storage-layer queries.
* **Remediation**: The remediator generates Terraform blocks to apply `aws_s3_bucket_public_access_block` and `aws_s3_bucket_server_side_encryption_configuration` resources. See the practical example in [patches.hcl](example-out/patches.hcl).

### 2.2 GCP Compute Exposure (`GCP_EXTERNAL_IP`)
To minimize the external attack surface, no VM instance is permitted to have an external public IPv4 address.
* **Remediation**: The remediator provides advice to remove the `access_config` block from the GCE instance configuration.

### 2.3 GKE Workload Identity Verification (`GKE_WORKLOAD_IDENTITY`)
Legacy Kubernetes service accounts bound to node-scoped metadata credentials represent a high risk of lateral privilege escalation. `nit-fabric` verifies:
* **Cluster Setting**: Ensures `workload_identity_config` is declared on the GKE cluster resource.
* **Workload Bindings**: Audits container definitions to verify that high-privilege namespaces are explicitly configured to assume GCP Service Accounts via Workload Identity annotations, flagging legacy nodes still using compute engine default service accounts.

---

## 3. Cryptographic and State Protection
All discovered network contexts are treated as sensitive intellectual property.
* **Encrypted Backend State**: State files must be resident in an encrypted S3 bucket (`encrypt = true`) configured with KMS CMKs and DynamoDB-based distributed locking to prevent state manipulation.
* **Credential Isolation**: The controller uses IAM role assumption and GCP workload identity federation, running only short-lived tokens in execution contexts.

For a full list of detected security violations, refer to [violations.json](example-out/violations.json).
