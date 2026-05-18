import json
import logging
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger("nit-fabric.discovery.gcp")

class GCPDiscoverer:
    def __init__(self):
        pass

    def _run_cli(self, cmd: List[str]) -> str:
        logger.debug(f"Executing GCP CLI command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = f"GCP CLI Command failed: {' '.join(cmd)}\nReturn Code: {e.returncode}\nStderr: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except FileNotFoundError as e:
            error_msg = f"gcloud SDK command not found: {cmd[0]}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_shared_vpc_topology(self, host_project: str) -> Dict[str, Any]:
        """Maps host project and associated service projects + usable subnets."""
        try:
            # Service projects
            srv_out = self._run_cli([
                "gcloud", "compute", "shared-vpc", "list-associated-resources",
                host_project, "--format=json"
            ])
            srv_data = json.loads(srv_out) if srv_out else []
            service_projects = [
                item["resourceId"] for item in srv_data 
                if item.get("resourceType") == "PROJECT"
            ]

            # Usable subnets
            sub_out = self._run_cli([
                "gcloud", "compute", "networks", "subnets", "list-usable",
                f"--project={host_project}", "--format=json"
            ])
            sub_data = json.loads(sub_out) if sub_out else []

            return {
                "host_project": host_project,
                "service_projects": service_projects,
                "usable_subnets": sub_data
            }
        except Exception as e:
            logger.error(f"Failed to map Shared VPC topology for {host_project}: {e}")
            return {
                "host_project": host_project,
                "service_projects": [],
                "usable_subnets": []
            }

    def get_vpc_peerings(self, project_id: str) -> List[Dict[str, Any]]:
        """Audits active VPC network peerings to verify project isolation."""
        try:
            out = self._run_cli([
                "gcloud", "compute", "networks", "peerings", "list",
                f"--project={project_id}", "--format=json"
            ])
            return json.loads(out) if out else []
        except Exception as e:
            logger.error(f"Failed to audit VPC peerings for {project_id}: {e}")
            return []

    def get_hierarchical_firewalls(self, parent_id: str) -> List[Dict[str, Any]]:
        """Audits Org or Folder level effective firewall policies."""
        try:
            # e.g., parent_id = "organizations/123456" or "folders/78910"
            out = self._run_cli([
                "gcloud", "compute", "firewall-policies", "list",
                f"--parent={parent_id}", "--format=json"
            ])
            return json.loads(out) if out else []
        except Exception as e:
            logger.error(f"Failed to audit hierarchical firewalls for {parent_id}: {e}")
            return []

    def get_project_firewall_rules(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetches project-level firewall rules to detect shadow policies."""
        try:
            out = self._run_cli([
                "gcloud", "compute", "firewall-rules", "list",
                f"--project={project_id}", "--format=json"
            ])
            data = json.loads(out) if out else []
            return [
                {
                    "name": f["name"],
                    "network": f["network"].split("/")[-1],
                    "allowed": f.get("allowed", []),
                    "source_ranges": f.get("sourceRanges", []),
                    "disabled": f.get("disabled", False),
                    "priority": f.get("priority", 1000)
                } for f in data
            ]
        except Exception as e:
            logger.error(f"Failed to fetch project firewall rules for {project_id}: {e}")
            return []

    def audit_workload_identity(self, gsa_email: str) -> List[str]:
        """Audits KSA-to-GSA Workload Identity bindings."""
        try:
            out = self._run_cli([
                "gcloud", "iam", "service-accounts", "get-iam-policy",
                gsa_email, "--format=json"
            ])
            policy = json.loads(out) if out else {}
            bindings = []
            for b in policy.get("bindings", []):
                if b.get("role") == "roles/iam.workloadIdentityUser":
                    for member in b.get("members", []):
                        if "svc.id.goog" in member:
                            # Extract KSA namespace/name e.g., serviceAccount:project.svc.id.goog[ns/ksa]
                            ksa = member.split("[")[-1].rstrip("]")
                            bindings.append(ksa)
            return bindings
        except Exception as e:
            logger.error(f"Failed to audit Workload Identity for {gsa_email}: {e}")
            return []

    def get_project_iam_policy(self, project_id: str) -> List[Dict[str, Any]]:
        """Audits project-level IAM bindings to detect GSA over-privileges."""
        try:
            out = self._run_cli([
                "gcloud", "projects", "get-iam-policy", project_id, "--format=json"
            ])
            data = json.loads(out) if out else {}
            return data.get("bindings", [])
        except Exception as e:
            logger.error(f"Failed to fetch project IAM policy for {project_id}: {e}")
            return []

    def get_asset_inventory_resources(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetches a point-in-time snapshot of resources via Cloud Asset Inventory."""
        try:
            out = self._run_cli([
                "gcloud", "asset", "search-all-resources",
                f"--scope=projects/{project_id}", "--format=json"
            ])
            return json.loads(out) if out else []
        except Exception as e:
            logger.error(f"Failed to search asset inventory resources for {project_id}: {e}")
            return []

    def get_instances(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetches Compute Engine instances to audit public IP exposure."""
        try:
            out = self._run_cli([
                "gcloud", "compute", "instances", "list",
                f"--project={project_id}", "--format=json"
            ])
            data = json.loads(out) if out else []
            results = []
            for i in data:
                has_external = False
                for ni in i.get("networkInterfaces", []):
                    for ac in ni.get("accessConfigs", []):
                        if ac.get("type") == "ONE_TO_ONE_NAT":
                            has_external = True
                            break
                results.append({
                    "name": i["name"],
                    "has_external_ip": has_external,
                    "zone": i["zone"].split("/")[-1]
                })
            return results
        except Exception as e:
            logger.error(f"Failed to fetch compute instances for {project_id}: {e}")
            return []

    def get_gke_clusters(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetches GKE clusters to audit Workload Identity configuration."""
        try:
            out = self._run_cli([
                "gcloud", "container", "clusters", "list",
                f"--project={project_id}", "--format=json"
            ])
            data = json.loads(out) if out else []
            results = []
            for c in data:
                results.append({
                    "name": c["name"],
                    "location": c["location"],
                    "workload_identity_enabled": "workloadIdentityConfig" in c,
                    "node_pools": [np["name"] for np in c.get("nodePools", [])]
                })
            return results
        except Exception as e:
            logger.error(f"Failed to fetch GKE clusters for {project_id}: {e}")
            return []

    def get_subnets(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetches VPC subnets to audit Private Google Access properties."""
        try:
            out = self._run_cli([
                "gcloud", "compute", "networks", "subnets", "list",
                f"--project={project_id}", "--format=json"
            ])
            data = json.loads(out) if out else []
            return [
                {
                    "name": s["name"],
                    "private_google_access": s.get("privateIpGoogleAccess", False),
                    "region": s["region"].split("/")[-1]
                } for s in data
            ]
        except Exception as e:
            logger.error(f"Failed to fetch VPC subnets for {project_id}: {e}")
            return []

    def get_vpc_service_controls(self, project_id: str) -> List[Dict[str, Any]]:
        """Audits active VPC Service Controls policies."""
        try:
            # Query policies
            out = self._run_cli([
                "gcloud", "access-context-manager", "policies", "list",
                f"--project={project_id}", "--format=json"
            ])
            return json.loads(out) if out else []
        except Exception as e:
            logger.warning(f"Could not retrieve VPC Service Controls: {e}")
            return []

    def get_scc_findings(self, project_id: str) -> List[Dict[str, Any]]:
        """Audits Security Command Center findings for vulnerabilities."""
        try:
            out = self._run_cli([
                "gcloud", "scc", "findings", "list",
                f"projects/{project_id}", "--format=json"
            ])
            data = json.loads(out) if out else []
            return [
                {
                    "category": f["finding"]["category"],
                    "resource": f["finding"]["resourceName"],
                    "severity": f["finding"]["severity"]
                } for f in data
            ]
        except Exception as e:
            logger.warning(f"Could not retrieve SCC findings: {e}")
            return []

    def get_resource_locations(self) -> List[Dict[str, Any]]:
        """Checks for active Organization resource location constraints."""
        try:
            out = self._run_cli([
                "gcloud", "resource-manager", "org-policies", "describe",
                "constraints/gcp.resourceLocations", "--format=json"
            ])
            policy = json.loads(out) if out else {}
            return [policy] if policy else []
        except Exception as e:
            logger.warning(f"Could not retrieve Org Policy constraints: {e}")
            return []

    def discover_all(self, project_id: str, parent_id: str = "") -> Dict[str, Any]:
        """Orchestrates comprehensive GCP sovereignty mapping."""
        return {
            "gcp_shared_vpc": self.get_shared_vpc_topology(project_id),
            "gcp_peerings": self.get_vpc_peerings(project_id),
            "gcp_hierarchical_firewalls": self.get_hierarchical_firewalls(parent_id) if parent_id else [],
            "gcp_firewall_rules": self.get_project_firewall_rules(project_id),
            "gcp_iam_policies": self.get_project_iam_policy(project_id),
            "gcp_assets": self.get_asset_inventory_resources(project_id),
            "gcp_instances": self.get_instances(project_id),
            "gke_clusters": self.get_gke_clusters(project_id),
            "gcp_subnets": self.get_subnets(project_id),
            "gcp_vpc_sc": self.get_vpc_service_controls(project_id),
            "gcp_scc_findings": self.get_scc_findings(project_id),
            "gcp_resource_locations": self.get_resource_locations()
        }
