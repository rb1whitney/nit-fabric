# Specification: High-Resolution AWS Discovery Engine

## 1. Objective
Replace the current brittle, naming-based AWS discovery logic in `nit-fabric` with a high-resolution, tag-driven engine capable of mapping complex enterprise networking topologies.

## 2. Scope of Discovery
The engine must discover and map the following AWS resources:

### 2.1 Core Networking
- **VPCs**: CIDR blocks, secondary CIDRs, and association state.
- **Subnets**: Availability Zone mapping, CIDR blocks, and route table associations.
- **Route Tables**: 
    - Explicit vs. Implicit associations.
    - Routes (Local, Static, Propagated).
    - Target types (IGW, VGW, TGW, VPC Peering, NAT Gateway, VPC Endpoint).

### 2.2 Hybrid & Inter-VPC Connectivity
- **Transit Gateways (TGW)**: 
    - Attachments (VPC, VPN, Direct Connect).
    - Route Tables and Propagation/Association logic.
- **Direct Connect (DX)**: 
    - Virtual Interfaces (Private, Public, Transit).
    - Direct Connect Gateways.
- **VPC Peering**: Active and pending connections.

### 2.3 Security & Endpoints
- **VPC Endpoints**: 
    - Interface Endpoints (PrivateLink).
    - Gateway Endpoints (S3, DynamoDB).
    - Security Group associations for Interface Endpoints.
- **Security Groups**: Ingress/Egress rules with reference resolution (CIDR vs. SG-ID).
- **Network ACLs**: Stateless rule mapping.

## 3. Discovery Mechanism: Tag-Driven Protocol
Instead of relying on resource names or "mock" defaults, the engine will prioritize resources tagged with:
- `nit-fabric:managed = "true"`
- `nit-fabric:environment = ["prod", "stage", "dev"]`
- `nit-fabric:role = ["hub", "spoke", "dmz"]`

## 4. Output Schema
The discovery output must be a structured JSON object (Network State) that represents the graph of connectivity, not just a flat list of CIDRs.

## 5. Success Criteria
- Ability to detect a route to a Transit Gateway from a private subnet.
- Identification of VPC Endpoints without Private DNS enabled.
- Mapping of Direct Connect Gateway associations to multiple VPCs.
