import logging
from typing import Dict, Any, List

logger = logging.getLogger("nit-fabric.sovereignty")

class SovereigntyGovernor:
    def __init__(self, allowed_regions: List[str] = None):
        # Default to US/EU regions if not specified
        self.allowed_regions = allowed_regions or ["us-central1", "us-east1", "us-west1", "europe-west1"]

    def calculate_score(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates a sovereignty score from 0 to 100 with detailed weights."""
        network_score = 100.0
        identity_score = 100.0
        data_score = 100.0
        tips = []

        # --- 1. Network Isolation (40% Weight) ---
        # Penalize for public IPs or wide open ingress
        public_instances = [inst for inst in context.get("gcp_instances", []) if inst.get("has_external_ip")]
        if public_instances:
            penalty = len(public_instances) * 20
            network_score = max(0.0, network_score - penalty)
            tips.append(f"Network: Disable public IPs for instances: {', '.join([i['name'] for i in public_instances])}.")

        public_buckets = [b for b in context.get("aws_s3_buckets", []) if b.get("public_access")]
        if public_buckets:
            penalty = len(public_buckets) * 30
            network_score = max(0.0, network_score - penalty)
            tips.append(f"Network: Enable Public Access Block for S3 Buckets: {', '.join([b['name'] for b in public_buckets])}.")

        open_ingress = [r for r in context.get("gcp_firewall_rules", []) if "0.0.0.0/0" in r.get("source_ranges", [])]
        if open_ingress:
            network_score = max(0.0, network_score - 40)
            tips.append(f"Network: Remove wide-open ingress (0.0.0.0/0) in firewall rules: {', '.join([r['name'] for r in open_ingress])}.")

        # --- 2. Identity Isolation (30% Weight) ---
        # Penalize for overprivileged roles or disabled Workload Identity
        gke_no_wi = [c for c in context.get("gke_clusters", []) if not c.get("workload_identity_enabled")]
        if gke_no_wi:
            identity_score = max(0.0, identity_score - 50)
            tips.append(f"Identity: Enable GKE Workload Identity on cluster(s): {', '.join([c['name'] for c in gke_no_wi])}.")

        owner_roles = [b for b in context.get("gcp_iam_policies", []) if b.get("role") in ["roles/owner", "roles/editor"]]
        if owner_roles:
            identity_score = max(0.0, identity_score - 30)
            tips.append("Identity: Restrict broad project-level Owner/Editor roles for service accounts.")

        # --- 3. Data Residency (30% Weight) ---
        # Check GCP subnets and resource locations
        misplaced_subnets = [s for s in context.get("gcp_subnets", []) if s.get("region") not in self.allowed_regions]
        if misplaced_subnets:
            penalty = len(misplaced_subnets) * 20
            data_score = max(0.0, data_score - penalty)
            tips.append(f"Residency: Relocate subnets outside allowed regions: {', '.join([s['name'] for s in misplaced_subnets])}.")

        # Weighted calculation
        final_score = (network_score * 0.40) + (identity_score * 0.30) + (data_score * 0.30)

        return {
            "sovereignty_score": round(final_score, 1),
            "dimensions": {
                "network_isolation": round(network_score, 1),
                "identity_isolation": round(identity_score, 1),
                "data_locality": round(data_score, 1)
            },
            "compliance_status": "COMPLIANT" if final_score >= 80 else "NON_COMPLIANT",
            "remediation_tips": tips
        }
