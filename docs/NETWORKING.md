# Multi-Cloud Network Auditor | Networking & Routing Specification
*BGP Peering, IPAM, and MTU Architecture Specifications*

---

## 1. Peering Design & Topology
Cross-cloud network integration requires high-availability routing loops between AWS (us-east-1) and GCP (us-central1). This is established over IPsec VPN tunnels with dynamic Border Gateway Protocol (BGP) routing sessions.

```
       AWS HUB (us-east-1)                        GCP SPOKE (us-central1)
+-------------------------------+              +------------------------------+
| Primary VPC: 10.10.0.0/16     |              | Spoke VPC: 10.20.0.0/16      |
|                               |              |                              |
|  +-------------------------+  |              |  +------------------------+  |
|  | Transit Subnet:         |  |              |  | Primary Subnet         |  |
|  | 10.10.100.0/24          |  |              |  | 10.20.0.0/24           |  |
|  +------------+------------+  |              |  +-----------+------------+  |
|               |               |              |              |               |
|  +------------v------------+  |              |  +-----------v------------+  |
|  | Transit Gateway (TGW)   |  |              |  | Cloud Router (BGP)     |  |
|  | ASN: 64512              |  |              |  | ASN: 64600             |  |
|  +------------+------------+  |              |  +-----------+------------+  |
+---------------|---------------+              +--------------|---------------+
                |                                             |
                +============== IPsec VPN Tunnel =============+
                                BGP Peer IPs
                           AWS: 169.254.0.1/30
                           GCP: 169.254.0.2/30
                           Standard MTU: 1440
```

### 1.1 BGP Autonomous System Numbers (ASNs)
To prevent routing loops and ensure deterministic route prioritization, private ASNs are statically assigned:
* **AWS Transit Gateway (TGW)**: `64512`
* **GCP Cloud Router**: `64600`
* **Private ASN Range Enforcement**: The Policy Engine ensures that any BGP configuration utilizes values strictly within the RFC 6996 private ASN range (`64512` to `65534`).

### 1.2 Point-to-Point Address Space
Tunnels terminate on point-to-point IP configurations inside the link-local space:
* **AWS tunnel endpoint**: `169.254.0.1/30`
* **GCP tunnel endpoint**: `169.254.0.2/30`

---

## 2. Packet Optimization (MTU Standards)
To prevent IP packet fragmentation over the encapsulated IPsec VPN tunnel, the Maximum Transmission Unit (MTU) must be configured:
* **Standard Interface MTU**: **`1440` bytes** on both AWS Transit Gateway and GCP Cloud Router BGP tunnel interfaces.
* **TCP Maximum Segment Size (MSS) Clamping**: Routing interfaces on both ends must enforce TCP MSS clamping to **`1400` bytes** (equivalent to MTU minus 40 bytes for TCP/IPv4 headers).
  * *AWS implementation*: Enforced via the VPN Connection configuration.
  * *GCP implementation*: Enforced on the Cloud Router BGP Peer configurations.
* **Rationale**: Configuring a default 1500-byte MTU results in packet fragmentation at the physical layer, degrading throughput and causing SRE troubleshooting overhead.

---

## 3. Algebraic IPAM & Overlap Solver

### 3.1 Mathematical Formulation
Given two network CIDRs $A$ and $B$, they are disjoint if and only if:
$$A \cap B = \emptyset$$
For any subnets $S_a \subset A$ and $S_b \subset B$, the validation engine verifies that no subnet overlaps with another. If an intersection is found:
$$\text{Overlap}(S_a, S_b) \implies \text{VIOLATION}$$

This verification covers:
1. **Intra-Cloud Overlaps**: Overlapping subnets within the same VPC (e.g. AWS `10.0.0.0/16` vs `10.0.1.0/24`).
2. **On-Premises Conflicts**: Overlaps with registered on-premises routing tables (e.g. GCP `192.168.1.0/24` vs Local datacenter `192.168.0.0/16`).

### 3.2 Handling NAT and Isolated Environments
* **Coexistence via NAT**: In systems where overlapping subnets must coexist (e.g. legacy VPCs mapped to a shared service via 1-to-1 NAT), the policy engine allows exemptions. These are defined via explicit label tags (e.g., `exempt_nat = true`) in `bin/policies.yaml`. When tagged, the checker bypasses the intersection validation block for those specific endpoints.

### 3.3 Computational Complexity & Performance Limitations
* **Scale Limitations**: Because pairwise intersection checks run at $O(n^2)$ complexity, execution latency scales poorly when managing large inventories (1000+ subnets).
* **Mitigation**: The engine optimizes execution by bucketizing subnets by VPC and Cloud Region. This limits the pairwise comparisons to networks bound to shared routing domains, ensuring typical audit sweeps complete in under 5 seconds.

For a live representation of the network topology, refer to [network_state.md](example-out/network_state.md).
