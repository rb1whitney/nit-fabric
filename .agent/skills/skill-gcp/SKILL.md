---
name: skill-gcp
description: Holistic 2026 GCP Expertise. Integration of Setup, Playbooks, and Dynamic CLI Discovery.
related_skills: []
---
# GCP Expert (Holistic 2026 Edition)

## Scripts & Automation
Skill directory: `{{SKILL_DIR}}/scripts/`
- `gcp_inventory.py`: **TRIGGER**: Run to discover active Shared VPCs, GKE clusters, and networking resource IDs.
- `setup_readonly_sa.sh`: **TRIGGER**: Run when a least-privilege investigator identity is required for production triage.

##  Capability Reference Guide
Reference library path: `{{SKILL_DIR}}/references/`

| Capability | Reference File | Trigger |
| :--- | :--- | :--- |
| **Gke Operations** | [gke-operations.md]({{SKILL_DIR}}/references/gke-operations.md) | Audit GKE Alias IP ranges and VPC-native cluster networking. |
| **Security Foundations** | [security-foundations.md]({{SKILL_DIR}}/references/security-foundations.md) | Verify Organizational Policies and hierarchical IAM roles. |
| **Security Expert** | [security-expert.md]({{SKILL_DIR}}/references/security-expert.md) | Investigate Cloud Armor, VPC Service Controls, and PSC. |
| **Troubleshooting** | [troubleshooting.md]({{SKILL_DIR}}/references/troubleshooting.md) | Triage BGP flapping, route reachability, and VPC peering issues. |

## Knowledge Bootstrap (MANDATORY)

1. **List References**: `ls {{SKILL_DIR}}/references/`
2. **Select Protocol**: 
   - Use `{{SKILL_DIR}}/references/security-expert.md` for PSC/VPC-SC investigations.
   - Use `{{SKILL_DIR}}/references/troubleshooting.md` for BGP/Peering failures.
   - Use `{{SKILL_DIR}}/references/gke-operations.md` for Pod/Service CIDR audits.
3. **Ingest & Execute**: Follow reference instructions exactly.

---
### Deep Technical Domains

#### 1. Setup & Preflight
- **Auth Verification**: **TRIGGER**: Run `gcloud config list` to validate project context before any scan.
- **Service Audit**: **TRIGGER**: Use to ensure Compute and Asset APIs are enabled for the "Truth" discovery layer.

#### 2. SRE Playbooks & Investigation
- **Connectivity Triage**: **TRIGGER**: Engage `{{SKILL_DIR}}/references/troubleshooting.md` for standardized BGP and route reachability sequences.

#### 3. GKE (Kubernetes Engine)
- **Advanced Networking**: **TRIGGER**: Engage `{{SKILL_DIR}}/references/gke-operations.md` to map Pod/Service CIDRs for overlap proofs.

#### 4. Resource & Identity Management
- **Hierarchy Mapping**: **TRIGGER**: Reconstruct resource tree for Org-level audit scope.

## Best Practices
- **Private-First**: backend resources MUST be private; no external IPs.
- **Identity-First**: Use Short-Lived Tokens or Workload Identity.
- **IaC-First**: Use `gcloud` for discovery, but `terraform` for state-modifying changes.

## Commands for Environmental Awareness
```bash
# Check current project and user
gcloud config list

# Discover all active VPCs
gcloud compute networks list
```
