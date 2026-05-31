# SRE Runbook: Cross-Cloud BGP Peer Flapping & Outages

## 1. Alert Metadata
*   **Alert Name**: `SRE_BGP_Peer_Flapping` / `SRE_BGP_Peer_Down`
*   **Severity**: **P1 - Critical**
*   **SLA / Time-to-Mitigate**: 15 minutes
*   **Target Components**: AWS Transit Gateway (TGW), GCP Cloud Routers, Multi-Cloud IPSec Tunnels.
*   **PagerDuty Escalation Policy**: `Multi-Cloud-Network-Oncall`

---

## 2. Triggering Alert Criteria
This runbook is triggered when the PromQL query below evaluates to `0` or flaps frequently (state churn > 3 transitions per 5 minutes):
```promql
# Alert fires if any cross-cloud BGP session is down
avg_over_time(gcp_router_bgp_peer_status{peer_ip=~"169.254..*"}[2m]) == 0
or
aws_tgw_bgp_peer_state{state="down"} == 1
```

---

## 3. Triage & Quick Diagnostics

### Step 3.1: Run Local Nit-Fabric Live Discovery Scan
Validate the current state of cross-cloud routing endpoints using the `nit-fabric` CLI:
```bash
# Execute local scan to pull topology state
PYTHONPATH=src python3 src/nit_fabric/main.py scan --mode mock
```
Inspect the output or check `/mnt/d/OneDrive/Email_attachments/Programming-Work/projects/nit-fabric/out/network_state.json`. If a BGP peering peer IP is flagged as inactive, verify the physical connectivity endpoints.

### Step 3.2: Run AWS Peering Status Verification
Execute AWS CLI checks to verify the status of the virtual interfaces and IPSec VPN connections:
```bash
# Query AWS VPN Connection BGP status
aws ec2 describe-vpn-connections \
  --query "VpnConnections[*].[VpnConnectionId,VgwTelemetry]" \
  --output table

# Query Direct Connect Virtual Interface state
aws directconnect describe-virtual-interfaces \
  --query "VirtualInterfaces[*].[VirtualInterfaceId,VirtualInterfaceState,BgpPeers[*].[BgpStatus,BgpState]]" \
  --output table
```

### Step 3.3: Run GCP Peering Status Verification
Check the status of GCP Cloud Routers and corresponding BGP sessions:
```bash
# Get GCP router status and peer details
gcloud compute routers get-status vpc-tran-router \
  --region us-east1 \
  --format="yaml(bgpPeerStatus)"
```

---

## 4. Remediation Steps

### Scenario A: Flapping due to MTU / MSS Mismatch
If packet sizes are causing TCP resets on the BGP session (typically occurring when tunnels transit public internet routes), clamp the MSS:

1.  **Check current tunnel MTU** on AWS/GCP endpoints. Standard IPSec should be `1400` bytes with MSS clamped to `1360`.
2.  **Generate HCL MTU Correction Patch**:
    Locate the Tunnel resource in `/terraform/main.tf` and ensure the following variables are declared:
    ```hcl
    resource "aws_vpn_connection" "tgw_vpn" {
      # ...
      tunnel1_inside_cidr   = "169.254.10.0/30"
      tunnel1_max_transmission_unit = 1400  # Enforce MSS clamping boundary
    }
    ```
3.  **Validate Patch**:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py remediate --provider terraform
    ```

### Scenario B: Hard Peering Outage (Tunnel Failover)
If BGP is hard down and traffic is not automatically failing over to the backup link (Direct Connect or secondary VPN tunnel), manually force AS-Path Prepending adjustments:

1.  **Generate Policy Patch**: Expand AS-Path Prepending on the primary failing tunnel to force GCP/AWS to route via the healthy secondary link:
    ```bash
    # Apply prepends to GCP Cloud Router Peer config
    gcloud compute routers update-bgp-peer vpc-tran-router \
      --peer-name=aws-tunnel-1 \
      --region=us-east1 \
      --advertised-route-priority=1000  # Deprioritize primary tunnel
    ```
2.  **Verify Routing Stability**:
    Run `nit-fabric visualize` to synthesize a new network state diagram and confirm traffic routes through the healthy tunnel:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py visualize
    ```

---

## 5. Escalation Matrix
*   **L1 Multi-Cloud Engineer**: Network On-Call
*   **L2 Senior Network Engineer**: PagerDuty Escalation L2
*   **L3 AWS/GCP Technical Account Manager (TAM)**: Urgent Cloud Support Ticket.

---

## 6. Post-Mortem Log Collection
Extract historical metrics for BGP status change events:
```bash
# Capture AWS CloudWatch logs for Transit Gateway routing changes
aws logs filter-log-events \
  --log-group-name "/aws/tgw/routing" \
  --start-time $(date -d '2 hours ago' +%s000) \
  --filter-pattern "BGP_STATE_CHANGE"
```
Save the logs directly into `discovery_logs/bgp_flap_incident_$(date +%F).log`.
