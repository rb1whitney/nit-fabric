# Multi-Cloud Network Auditor | SRE Operations & Deployment Playbook
*CLI Usage, Local Installation, Credentials, and Incident Response Playbooks*

---

## 1. Quick Start & Prerequisites

### 1.1 Local Setup
Verify Python 3.8+ and pip are installed, then set up the local virtual environment:
```bash
# Initialize and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 1.2 Access Validation & Environment Safety
Before initiating a scan, confirm that your active shell session points to the correct target landing zones:
```bash
# Validate AWS STS identity context
aws sts get-caller-identity

# Validate GCP identity context
gcloud config get-value project
```

> [!CAUTION]
> **Profile Safety Warning**: `nit-fabric` queries the active provider session configurations. Ensure your shell environment variable `AWS_PROFILE` or `AWS_DEFAULT_REGION` matches your sandbox/staging environment before running scans. Running scans on default administrative profiles might target production environments accidentally.

---

## 2. Command-Line Interface (CLI) Manual
The SRE workflow uses the `nit-fabric` binary for auditing and remediation:

### 2.1 Step 1: Discover Active Infrastructure
Queries active cloud resource managers and serializes current topology:
```bash
./bin/nit-fabric scan --mode cli
```
*Creates [context.json](example-out/context.json) and [network_state.md](example-out/network_state.md).*

### 2.2 Step 2: Evaluate Compliance & Policies
Executes rule validation to display remediation advice:
```bash
./bin/nit-fabric remediate --explain
```
*Generates [violations.json](example-out/violations.json).*

### 2.3 Step 3: Patch Generation & Safe Dry-Run Workflows
Outputs executable command patches or Terraform updates:
```bash
# Generate the fix script
./bin/nit-fabric remediate --provider cli > fix.sh
```

> [!IMPORTANT]
> **No Blind Execution**: Running `chmod +x fix.sh && ./fix.sh` directly in production is strictly prohibited. SREs must perform a dry-run check by reading the generated script first.
> For Terraform patches: Copy the generated block from [patches.hcl](example-out/patches.hcl) into your local staging Terraform codebase and run `terraform plan` to verify the execution plan.

---

## 3. Automated CI/CD Pipelines Execution
To run the tool headless in GitOps pipelines (e.g., GitHub Actions, GitLab CI):
* **AWS Authentication**: Configure OIDC Role Assumption to exchange pipeline JWT tokens for temporary AWS IAM session tokens.
* **GCP Authentication**: Expose the pipeline container to Workload Identity Pool bindings.
* **Fail-on-Error Pipeline Integration**: Add the `--strict` flag to fail the pipeline build phase if any `CRITICAL` vulnerability is found:
```bash
./bin/nit-fabric scan --mode cli && ./bin/nit-fabric remediate --strict
```

---

## 4. Reference Artifacts (Walkthrough)
When running tests or scans, examine these files in `docs/example-out/` to debug:
* **Current Cloud Context**: [context.json](example-out/context.json)
* **Active Compliance Violations**: [violations.json](example-out/violations.json)
* **Generated Infrastructure Patches**: [patches.hcl](example-out/patches.hcl)
* **Visual Topology Diagram**: [network_state.md](example-out/network_state.md)

---

## 5. Incident Response & Troubleshooting Runbook

| Symptom | Root Cause | Remediation Step |
| :--- | :--- | :--- |
| **BGP Session Down (IPsec Down)** | ASN Mismatch between AWS TGW (`64512`) and GCP Cloud Router (`64600`). | Execute `nit-fabric remediate --explain` to fetch structural changes. Apply BGP configuration corrections. |
| **VPN Packet Loss / High Latency** | MTU Fragmentation on encapsulated IPsec frames. | Verify tunnel interfaces are forced to an MTU of `1440` bytes. Check that MSS clamping is set to `1400` bytes. |
| **CIDR Collision Alert** | Newly provisioned VPC subnets overlapping with existing networks. | Inspect [violations.json](example-out/violations.json). Locate the intersecting subnet, and re-allocate using the non-overlapping IP address space. |
| **API Discovery Failure** | Stale session tokens or expired local credentials. | Run `aws sts get-caller-identity` to check AWS credentials. Run `gcloud auth application-default login` to refresh GCP credential context. |
