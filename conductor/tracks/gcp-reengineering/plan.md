# Implementation Plan: GCP Re-engineering (Nit-Fabric Sovereignty)

## Phase 1: Test-Driven Foundation (TDD)
Before implementing the discovery logic, we define the "Success Wall" using mock GCP responses and validation scripts.

### 1.1 Discovery Unit Tests
- **Test 1: Shared VPC Resolver**
    - **Input**: Mock output of `gcloud compute shared-vpc list-associated-resources`.
    - **Expected**: Correct identification of Host/Service project mapping and subnet isolation.
- **Test 2: Firewall Policy Auditor**
    - **Input**: Mock JSON of hierarchical firewall policies.
    - **Expected**: Detection of a "Deny All" override at the Org level.
- **Test 3: Workload Identity Validator**
    - **Input**: Mock IAM policy for a GSA.
    - **Expected**: Verification of `roles/iam.workloadIdentityUser` binding for the correct KSA.

### 1.2 Integration Tests (Live Environment)
- **Test 4: Asset Inventory Connectivity**
    - Verify that the engine can successfully query `cloudasset.googleapis.com`.
- **Test 5: Sovereignty Report Generation**
    - Verify that the final JSON output matches the schema defined in `spec.md`.

## Phase 2: Discovery Engine Implementation

### 2.1 Asset Inventory Module
- Implement the `GCPAssetScout` class.
- Integrate with `gcloud asset search-all-resources` to build the initial resource graph.
- Filter resources by project and region.

### 2.2 Network Topology Module
- Implement `SharedVPCMapper`.
- Logic to trace subnets back to the Host project.
- Audit for Public IPs and External Load Balancers.

### 2.3 Identity & Security Module
- Implement `IAMAuditor`.
- Logic to fetch and parse IAM policies for Service Accounts.
- Verify Workload Identity configuration for GKE clusters.

## Phase 3: Sovereignty Scoring Logic

### 3.1 Policy Engine
- Implement `SovereigntyGovernor`.
- Map resources against `constraints/gcp.resourceLocations`.
- Flag any resource residing in a non-compliant region.

### 3.2 Scoring Algorithm
- Assign weights to different security/sovereignty dimensions:
    - Network Isolation: 40%
    - Identity Isolation: 30%
    - Data Residency: 30%
- Generate a final `SovereigntyScore` (0-100).

## Phase 4: Reporting & Verification

### 4.1 JSON Reporter
- Format the discovery data and scores into a standardized JSON report.
- Include "Remediation Tips" for low-scoring areas.

### 4.2 Final Audit
- Run the engine against a test GCP environment.
- Verify that all TDD tests pass.
- Perform a manual review of the generated report.

## Timeline & Milestones
- **Milestone 1**: TDD Suite Complete (End of Day 1).
- **Milestone 2**: Discovery Engine Functional (End of Day 3).
- **Milestone 3**: Sovereignty Scoring & Reporting (End of Day 5).
