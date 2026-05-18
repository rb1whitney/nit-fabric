# SRE Runbook: Multi-Cloud Security Policy & OPA Violation Mitigation

## 1. Alert Metadata
*   **Alert Name**: `SRE_Security_Policy_Violation` / `OPA_Compliance_Failure`
*   **Severity**: **P1 - Critical (Immediate Audit Failure)**
*   **SLA / Time-to-Mitigate**: 10 minutes (Exposed Network Boundary)
*   **Target Components**: OPA Rego Engine, AWS VPC Security Groups, GCP Firewall Rules, Route Tables.
*   **PagerDuty Escalation Policy**: `Security-Operations-Oncall`

---

## 2. Triggering Alert Criteria
This runbook is triggered when an automated preflight check or live truth scan discovers a rule or route that violates corporate security policies:
```text
ComplianceViolationError: Policy Check Failed!
  Resource: aws_route_table.public_routes
  Reason: Route entry 0.0.0.0/0 maps directly to Internet Gateway (igw-*), violating Zero-Trust egress policy!
  Policy Ref: .agent/policies/egress_control.rego
```

---

## 3. Triage & Quick Diagnostics

### Step 3.1: Execute Local Compliance Audit
Run a local scan using the `nit-fabric` CLI to pinpoint the exact resources violating the policy boundaries:
```bash
# Execute local scan with policy enforcement
PYTHONPATH=src python3 src/nit_fabric/main.py scan --mode mock
```
Inspect the violations report generated inside `out/violations.json`:
```json
{
  "resource_id": "aws_route_table.public_routes",
  "policy_id": "ZT_EGRESS_01",
  "status": "FAIL",
  "reason": "Direct egress to internet gateway is strictly prohibited. Egress traffic must transit transit-gateway (tgw-*) or egress proxy."
}
```

### Step 3.2: Inspect Live AWS Security Groups & Routing Table
If the violation resides in AWS, query the offending route table configurations:
```bash
# Query specific Route Table entries
aws ec2 describe-route-tables \
  --route-table-ids rtb-0123456789abcdef0 \
  --query "RouteTables[*].Routes" \
  --output table
```

### Step 3.3: Inspect Live GCP Firewall Policies
If the violation resides in GCP, query the target firewall configuration for broad ingress permissions:
```bash
# Locate any GCP firewall rules allowing unrestricted access (0.0.0.0/0)
gcloud compute firewall-rules list \
  --filter="network:vpc-prod AND sourceRanges:0.0.0.0/0 AND allowed.ports:*" \
  --format="table(name,direction,allowed,targetTags)"
```

---

## 4. Remediation Steps

### Step 4.1: Isolate the Compromised Boundary
If the violation represents an active, unauthorized security exposure (e.g. open SSH port `22` to `0.0.0.0/0`), manually patch the boundary immediately:

```bash
# AWS: Remove permissive Security Group ingress rule
aws ec2 revoke-security-group-ingress \
  --group-id sg-0987654321fedcba0 \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# GCP: Disable offending firewall rule
gcloud compute firewall-rules update allow-ssh-prod-all \
  --disabled
```

### Step 4.2: Generate and Validate Policy-Compliant HCL
To make the fix permanent and compliant with Terraform state:

1.  **Generate HCL Patch**:
    Run `nit-fabric remediate` to generate a safe, policy-compliant patch targeting the Route Table or Firewall resource:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py remediate --provider terraform
    ```
2.  **Verify Patch Integrity**:
    The remediator automatically passes the patch through `ValidatorGate` to ensure that:
    *   HCL syntax is 100% correct (`terraform validate`).
    *   The generated configuration satisfies all OPA Rego policy rules.
3.  **Confirm Output**:
    Upon success, the output will log:
    ```text
    Validation Gate Passed: Patch matches 'ZT_EGRESS_01' egress compliance policies.
    ```

### Step 4.3: Deploy Safe Changes
Commit the updated Terraform definitions to stage the permanent fix:
```bash
git add terraform/
git commit -m "security(remediation): fix route tables to comply with Zero-Trust egress policies"
git push origin feat/nit-fabric-agents-standardization
```

---

## 5. Escalation Matrix
*   **L1 Security Analyst**: SecOps On-Call
*   **L2 Senior Cloud Security Architect**: PagerDuty Escalation L2
*   **L3 Chief Information Security Officer (CISO)**: Urgent Executive Escalation.

---

## 6. Post-Mortem Log Collection
Extract OPA validation logs to trace compliance failure events:
```bash
# Capture and archive all policy violation reports
cp out/violations.json discovery_logs/policy_violations_$(date +%F).json
```
Archived reports are saved directly in `discovery_logs/`.
