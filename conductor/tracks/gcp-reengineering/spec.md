# Specification: GCP Re-engineering (Nit-Fabric Sovereignty)

## 1. Objective
Transform the `nit-fabric` discovery engine from a generic placeholder into a high-precision GCP-native auditing and sovereignty enforcement tool. The engine must provide a "Ground Truth" view of infrastructure isolation and data residency.

## 2. Core Components

### 2.1 GCP Discovery Engine (The "Scout")
The engine will utilize the following GCP-specific mechanisms to map the environment:

#### 2.1.1 Shared VPC Topology
- **Logic**: Identify Host Projects and Service Projects.
- **Discovery**: Use `gcloud compute shared-vpc list-associated-resources` and `gcloud compute networks subnets list-usable`.
- **Requirement**: Map cross-project subnet attachments and verify that service projects do not have unauthorized peering or external gateways.

#### 2.1.2 Hierarchical Firewall Auditing
- **Logic**: Traverse the resource hierarchy (Org -> Folder -> Project) to identify effective firewall policies.
- **Discovery**: Use `gcloud compute firewall-policies list` and `gcloud compute firewall-rules list`.
- **Requirement**: Detect "Shadow Rules" inherited from higher levels that might bypass project-level security controls.

#### 2.1.3 Workload Identity Verification
- **Logic**: Audit the mapping between Kubernetes Service Accounts (KSA) and Google Service Accounts (GSA).
- **Discovery**: Use `gcloud container clusters describe` (to check if Workload Identity is enabled) and `gcloud iam service-accounts get-iam-policy`.
- **Requirement**: Ensure the "Least Privilege" principle is enforced at the pod level and that no GSA has over-privileged roles (e.g., `roles/editor`).

### 2.2 Sovereignty Logic (The "Governor")
- **Asset Inventory Integration**: Use `gcloud asset search-all-resources` and `gcloud asset search-all-iam-policies` for a unified, point-in-time snapshot.
- **Data Residency Enforcement**: Verify that resources (Cloud SQL, GCS, BigQuery) are restricted to specific regions using Organization Policy Constraints (`constraints/gcp.resourceLocations`).
- **Sovereignty Scoring**: Calculate a score based on:
    - Network Isolation (Private Service Connect usage vs. Public IPs).
    - Identity Isolation (Workload Identity usage vs. Static Keys).
    - Data Locality (Compliance with residency constraints).

## 3. Technical Constraints
- **Read-Only**: The discovery engine must operate with `roles/viewer` and `roles/cloudasset.viewer` permissions.
- **Performance**: Use asynchronous API calls or batching for large-scale Asset Inventory exports.
- **Security**: No storage of long-lived service account keys. Use Workload Identity Federation for the engine itself.

## 4. Success Criteria
- Successful mapping of a Shared VPC environment across at least two projects.
- Identification of a hierarchical firewall rule affecting a target project.
- Verification of a Workload Identity binding for a GKE pod.
- Generation of a "Sovereignty Report" in JSON format.
