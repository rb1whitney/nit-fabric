# nit-fabric: Cognitive State & Formal Schema (v1.0.0)

## Executive Summary: The Formal Verification Interface
This schema defines the high-precision interface between the **Core Mathematical Controller** and the **Multi-Cloud Specialist Swarm**. It establishes the contract for the **Z3 SMT Solver**, ensuring that all network state transitions are "Correct-by-Construction" and mathematically disjoint.

## 1. IPAM Assignment: CIDR Disjointness Contract
The IPAM schema enforces strict O(k) bit-mask verification to prevent overlapping address space in high-concurrency VPC orchestration.

```json
{
  "request": {
    "parent_cidr": "string",
    "requested_prefix": "number",
    "labels": ["string"]
  },
  "response": {
    "assigned_cidr": "string",
    "status": "APPROVED | REJECTED",
    "audit_id": "uuid",
    "z3_proof": "base64_encoded_smt_output"
  }
}
```

## 2. Topology Audit: Sovereign Connectivity Graph
The Topology schema maps the blast radius of network peering, Transit Gateways, and PrivateLink endpoints across AWS and GCP.

```json
{
  "topology": {
    "nodes": [
      { 
        "id": "string", 
        "type": "vpc | gateway | restricted_spoke", 
        "provider": "aws | gcp",
        "governance_zone": "string"
      }
    ],
    "edges": [
      { 
        "from": "string", 
        "to": "string", 
        "type": "peering | tgw_attachment | vpn_tunnel | lattice_link" 
      }
    ]
  },
  "verdict": {
    "sovereign": "boolean",
    "violations": ["string"],
    "blast_radius_score": "float (0.0 - 1.0)"
  }
}
```

## 3. Remediation Strategy: Deterministic Patch Generation
Defines the output format for the **Type-Safe HCL Generator**, ensuring that remediation patches are syntactically valid and policy-compliant before they reach the Terraform provider.

```json
{
  "remediation": {
    "type": "HCL_PATCH | OPA_REGO_ADJUSTMENT",
    "diff": "string (strict-patch format)",
    "pre_flight_checksum": "sha256",
    "governance_approval_required": "boolean"
  }
}
```
