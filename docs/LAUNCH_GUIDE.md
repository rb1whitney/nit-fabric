# nit-fabric | Operational Guide & Peering Scaffolding

This guide provides instructions for launching **nit-fabric**, deploying the 'bare bones' multi-cloud infrastructure, and establishing BGP-backed peering between AWS and GCP.

## 1. Quick Launch Checklist

1.  **Environment Sync**:
    ```bash
    # Initialize virtual environment
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Credential Pre-flight**:
    Ensure you have active sessions for both providers:
    ```bash
    aws sts get-caller-identity
    gcloud auth application-default print-access-token
    ```

3.  **The "One-Command" Scan**:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py scan --mode cli
    ```

---

## 2. Cross-Cloud Peering Scaffolding (Bare Bones)

The repository provides high-fidelity modules to establish a **Site-to-Site HA-VPN** (IPsec) with **BGP Dynamic Routing**.

### Step A: Infrastructure Bootstrapping
Navigate to the `terraform/` directory. The `main.tf` is configured to sprout the hub-and-spoke topology.

```hcl
# terraform/main.tf
module "aws_hub" {
  source     = "./modules/aws_hub"
  vpc_cidr   = "10.0.0.0/16"
  asn        = 64512
  subnet_ids = ["subnet-xxxxxx"]
}

module "gcp_spoke" {
  source      = "./modules/gcp_spoke"
  subnet_cidr = "10.1.0.0/16"
  asn         = 64600
  region      = "us-central1"
}
```

### Step B: Establish Peering
Run the remediation engine to generate the peering HCL:
```bash
PYTHONPATH=src python3 src/nit_fabric/main.py remediate --provider terraform --explain
```
This will identify the missing link and propose a `google_compute_vpn_tunnel` and `aws_vpn_connection` configuration.

---

## 3. Active Probe Lifecycle

Once peering is established, use the **Probes** to verify the data plane.

### Deployment
```bash
# Deploy GCP Cloud Run Probe
cd terraform/modules/gcp_probe
terraform apply -var="image_url=gcr.io/PROJECT/nit-fabric-probe" -var="vpc_connector_id=..."

# Deploy AWS Lambda Probe
cd terraform/modules/aws_probe
terraform apply -var="lambda_zip_path=../../../src/nit_fabric/probes/aws_probe.zip"
```

### Verification Commands
| Intent | Command |
| :--- | :--- |
| **Bidirectional Ping** | `python3 src/nit_fabric/main.py probe` |
| **GCP -> AWS Port Check** | `python3 src/nit_fabric/main.py probe --check-port gcp 10.0.1.5 5432` |
| **AWS -> GCP Port Check** | `python3 src/nit_fabric/main.py probe --check-port aws 10.1.0.10 80` |

---

## 4. Troubleshooting Peering

If `probe` results in `FAIL`:
1.  **Check BGP**: Run `gcloud compute routers get-status <router-name>` to ensure BGP sessions are `ESTABLISHED`.
2.  **MTU Check**: Ensure AWS TGW and GCP VPN tunnels are both set to **1440**.
3.  **Firewall Audit**:
    - **AWS**: Check Security Group ingress for the Lambda.
    - **GCP**: Check Firewall Rules for the Cloud Run VPC connector range.
