# SRE Runbook: Subnet IP Address Capacity Exhaustion

## 1. Alert Metadata
*   **Alert Name**: `SRE_Subnet_IP_Exhaustion_Warning` / `SRE_Subnet_IP_Exhaustion_Critical`
*   **Severity**: **P2 - Major / P1 - Critical (Capacity Limits reached)**
*   **SLA / Time-to-Mitigate**: 30 minutes (Major) / 15 minutes (Critical)
*   **Target Components**: AWS VPC Subnets, GCP VPC Subnets, IPAM registry.
*   **PagerDuty Escalation Policy**: `Infrastructure-Capacity-Oncall`

---

## 2. Triggering Alert Criteria
This runbook is triggered when the Prometheus or cloud metric indicates available IP count in a subnet is low (utilization ratio exceeds 90%):
```promql
# Alert fires if utilization exceeds 90%
cloud_ipam_subnet_utilization_ratio{subnet_id=~"subnet-.*"} >= 0.90
```

---

## 3. Triage & Quick Diagnostics

### Step 3.1: Query Available Subnet IPs via Cloud CLIs
Analyze the current live capacity status across the targets:

```bash
# Query AWS available IP counts for all subnets in VPC
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=vpc-0123456789abcdef0" \
  --query "Subnets[*].[SubnetId,CidrBlock,AvailableIpAddressCount]" \
  --output table

# Query GCP subnet IP ranges
gcloud compute networks subnets list \
  --network=vpc-prod \
  --format="table(name,ipCidrRange)"
```

### Step 3.2: Run Local Nit-Fabric Topology Check
Verify the exact CIDR constraints mapped in the registered fabric:
```bash
# Execute local scan to capture network states
PYTHONPATH=src python3 src/nit_fabric/main.py scan --mode mock
```
Inspect `out/network_state.json` to identify adjacent subnets that might restrict this subnet's capacity to grow.

---

## 4. Remediation Steps

### Scenario A: Clean Subnet Range Expansion
If there is free, adjacent space within the VPC CIDR block, expand the subnet mask (e.g. from `/24` to `/23`):

1.  **Formulate proposed CIDR expansion** (e.g., changing `10.100.4.0/24` to `10.100.4.0/23`).
2.  **Prove Disjointness with Z3 SMT Solver**:
    Run a local verification checks to mathematically guarantee that this expanded range does not overlap with any existing AWS or GCP subnets in the peered network:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py scan --mode mock
    ```
    If Z3 returns `unsat` for overlap, the expansion is mathematically safe!
3.  **Generate HCL Variable Patch**:
    Locate the subnet definition in `terraform/main.tf` and increase the allocation size:
    ```diff
    -  cidr_block = "10.100.4.0/24"
    +  cidr_block = "10.100.4.0/23"
    ```
4.  **Validate HCL Patch**:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py remediate --provider terraform
    ```

### Scenario B: Adding Secondary CIDR Block to VPC
If the primary VPC CIDR block is completely saturated, allocate a secondary CIDR block to the VPC and deploy a secondary subnet:

1.  **Add secondary VPC CIDR in HCL**:
    ```hcl
    resource "aws_vpc_ipv4_cidr_block_association" "secondary_cidr" {
      vpc_id     = aws_vpc.main.id
      cidr_block = "10.101.0.0/16"  # Secondary disjoint class-B block
    }
    ```
2.  **Verify Peer Disjointness**:
    Verify that the new secondary class-B range `10.101.0.0/16` is completely disjoint from all GCP cloud router peered CIDRs:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py remediate --provider terraform
    ```
3.  **Deploy changes**:
    Commit and push changes to unblock the capacity gates:
    ```bash
    git add terraform/
    git commit -m "capacity(ipam): resolve IP exhaustion by associating secondary CIDR 10.101.0.0/16"
    git push origin feat/nit-fabric-agents-standardization
    ```

---

## 5. Escalation Matrix
*   **L1 Systems Engineer**: Infrastructure Capacity On-Call
*   **L2 Senior Cloud Engineer**: PagerDuty Escalation L2
*   **L3 Systems Architect**: Core Platforms Strategy.

---

## 6. Post-Mortem Log Collection
Extract IPAM allocation history to document capacity consumption:
```bash
# Export IPAM allocation logs
cp out/network_state.json discovery_logs/ipam_capacity_$(date +%F).json
```
Archived reports are saved in `discovery_logs/`.
