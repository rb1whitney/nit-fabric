# nit-fabric State Schema (v1.0.0)

This schema defines the interface between the **Core Mathematical Controller** and the **Cloud Specialists**.

## IPAM Assignment Schema
```json
{
  "request": {
    "parent_cidr": "string",
    "requested_prefix": "number",
    "labels": ["string"]
  },
  "response": {
    "assigned_cidr": "string",
    "status": "APPROVED|REJECTED",
    "audit_id": "uuid"
  }
}
```

## Topology Audit Schema
```json
{
  "topology": {
    "nodes": [
      { "id": "string", "type": "vpc|gateway|restricted", "provider": "aws|gcp" }
    ],
    "edges": [
      { "from": "string", "to": "string", "type": "peering|tgw|vpn" }
    ]
  },
  "verdict": {
    "sovereign": "boolean",
    "violations": ["string"]
  }
}
```
