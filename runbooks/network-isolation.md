# SRE Runbook: Multi-Cloud Network Isolation & Routing Outages

## 1. Alert Metadata
*   **Alert Name**: `SRE_Network_Isolation` / `Multi_Cloud_Routing_Blackhole`
*   **Severity**: **P1 - Critical (Total Peer Isolation)**
*   **SLA / Time-to-Mitigate**: 10 minutes
*   **Target Components**: AWS VPC Transit Gateway (TGW), GCP VPC Peering, Cloud Routers, Route Tables.
*   **PagerDuty Escalation Policy**: `Network-Security-Emergency`

---

## 2. Triggering Alert Criteria
This runbook is triggered when an automated ping check or synthetic endpoint monitoring detects a total reachability loss between peered AWS and GCP application subnets:
```promql
# Alert fires if synthetic reachability drops to 0
avg_over_time(multi_cloud_endpoint_reachability_status[1m]) == 0
```

---

## 3. Triage & Quick Diagnostics

### Step 3.1: Execute Local Topology Diagnostics
Visualize the complete, live-truth topological mapping of the network to locate route blackholes or isolated subnets:
```bash
# Generate high-resolution topology map
PYTHONPATH=src python3 src/nit_fabric/main.py visualize
```
Inspect the generated graph or open `out/network_state.md`. If a subnet or transit connection is marked as red (unreachable), target that connection.

### Step 3.2: Run AWS Transit Gateway Diagnostics
Check the status of Transit Gateway attachments and associated route tables:
```bash
# Query TGW attachment states
aws ec2 describe-transit-gateway-attachments \
  --filters "Name=state,Values=associating,associated" \
  --query "TransitGatewayAttachments[*].[TransitGatewayAttachmentId,ResourceId,ResourceType,State]" \
  --output table

# Verify AWS TGW routing tables for active blackholes
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-0123456789abcdef0 \
  --filters "Name=state,Values=blackhole" \
  --query "Routes[*].[DestinationCidrBlock,TransitGatewayAttachmentId,Type,State]"
```

### Step 3.3: Run GCP VPC Peering Status Verification
Verify that VPC Peering connections inside GCP are active:
```bash
# Query active VPC Peering connections in GCP
gcloud compute networks peerings list \
  --network=vpc-prod \
  --format="table(name,peerNetwork,state,useCustomRoutes)"
```

---

## 4. Remediation Steps

### Scenario A: Restoring Blackholed Routes
If the AWS Transit Gateway route search identified a route flagged as `blackhole` (which occurs when the target VPC attachment was deleted or re-associated incorrectly):

1.  **Locate healthy VPC target attachment** (e.g. `tgw-attach-0987654321fedcba0`).
2.  **Generate HCL Route Patch**:
    Update the static route configuration inside `terraform/main.tf` to point back to the healthy target attachment:
    ```hcl
    resource "aws_ec2_transit_gateway_route" "prod_route" {
      destination_cidr_block         = "10.200.0.0/16"
      transit_gateway_attachment_id  = "tgw-attach-0987654321fedcba0"  # Replace blackhole
      transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.main.id
    }
    ```
3.  **Validate Patch Syntax & Safety**:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py remediate --provider terraform
    ```

### Scenario B: Restoring GCP Peering Custom Route Propagation
If VPC Peering status is active but custom routes (such as BGP routes advertised from AWS) are not reaching GCP subnets:

1.  **Check custom route import/export settings**:
    ```bash
    gcloud compute networks peerings update prod-to-transit \
      --network=vpc-prod \
      --import-custom-routes \
      --export-custom-routes
    ```
2.  **Verify Reachability**:
    Confirm peer reachability maps successfully by running a discovery scan:
    ```bash
    PYTHONPATH=src python3 src/nit_fabric/main.py scan --mode mock
    ```

---

## 5. Escalation Matrix
*   **L1 Multi-Cloud Engineer**: SecOps Emergency On-Call
*   **L2 Lead Security Solutions Architect**: PagerDuty Escalation L2
*   **L3 Director of Security & Network Infrastructure**: Executive Escalation.

---

## 6. Post-Mortem Log Collection
Extract CloudTrail audit trail of Transit Gateway or route modifications:
```bash
# Export CloudTrail events relating to network routing changes
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ReplaceTransitGatewayRoute \
  --start-time $(date -d '1 hour ago' +%s) \
  --output json > discovery_logs/trail_events_$(date +%F).json
```
Audit logs are preserved inside `discovery_logs/`.
