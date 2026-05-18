import json
import logging
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from nit_fabric.aws_discoverer import AWSDiscoverer
from nit_fabric.gcp_discoverer import GCPDiscoverer
from nit_fabric.sovereignty_governor import SovereigntyGovernor

# --- SRE Configuration: Professional Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] nit-fabric.discovery: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("nit-fabric.discovery")

class CloudDiscoverer:
    def __init__(self, mode: str = "mock"):
        self.mode = mode
        self.aws_disc = AWSDiscoverer()
        self.gcp_disc = GCPDiscoverer()
        self.governor = SovereigntyGovernor()

    def discover_all(self) -> Dict[str, Any]:
        context = {}
        if self.mode == "mock":
            logger.info("Running in MOCK mode. Returning synthetic truth-report.")
            context = self._get_mock_data()
        else:
            logger.info(f"Initiating {self.mode.upper()} discovery sequence...")
            # Run high-res AWS discoverer
            aws_data = self.aws_disc.discover_all()
            
            # Legacy compatible keys
            context["aws_s3_buckets"] = self.aws_disc.get_vpc_endpoints_detailed() # Mock public check
            context["vpcs"] = aws_data.get("vpcs", [])
            context["aws_cidrs"] = [vpc.get("CidrBlock") for vpc in aws_data.get("vpcs", []) if vpc.get("CidrBlock")]

            # Run high-res GCP discoverer
            project_id = self._run_cli(["gcloud", "config", "get-value", "project"]).strip()
            # Try to get active folder/org parent id from environment or command line
            parent_id = ""
            if project_id:
                gcp_data = self.gcp_disc.discover_all(project_id, parent_id)
                context.update(gcp_data)
        
        # Injects Sovereignty Audit & Score into context
        audit_results = self.governor.calculate_score(context)
        context.update(audit_results)
        
        return context

    def _run_cli(self, cmd: List[str]) -> str:
        logger.debug(f"Executing CLI command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = f"CLI Command failed: {' '.join(cmd)}\nReturn Code: {e.returncode}\nStderr: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except FileNotFoundError as e:
            error_msg = f"CLI Command not found: {cmd[0]}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            "aws_cidrs": ["10.0.0.0/16", "10.0.1.0/24"],
            "gcp_cidrs": ["10.1.0.0/16", "192.168.1.0/24"],
            "aws_s3_buckets": [{"name": "prod-public-bucket", "public_access": True}],
            "gcp_instances": [{"name": "insecure-instance", "has_external_ip": True, "zone": "us-central1-a"}],
            "vpcs": [{"id": "vpc-001", "endpoints": [{"Service": "s3", "Type": "Interface", "DnsEnabled": False}]}],
            "gke_clusters": [{
                "name": "legacy-cluster", 
                "location": "us-central1",
                "workload_identity_enabled": False,
                "node_pools": ["default-pool", "highmem-pool"]
            }],
            "gcp_subnets": [{"name": "prod-subnet", "private_google_access": False, "region": "us-central1"}],
            "gcp_iam_policies": [
                {"role": "roles/owner", "members": ["user:unauthorized@example.com"]},
                {"role": "roles/editor", "members": ["serviceAccount:legacy-sa@project.iam.gserviceaccount.com"]}
            ],
            "gcp_firewall_rules": [
                {"name": "allow-all-ingress", "network": "default", "allowed": [{"IPProtocol": "all"}], "source_ranges": ["0.0.0.0/0"]}
            ],
            "gcp_vpc_sc": [],
            "gcp_scc_findings": [
                {"category": "OPEN_FIREWALL", "resource": "//compute.googleapis.com/projects/mock/zones/us-central1-a/instances/insecure", "severity": "HIGH"}
            ],
            "gcp_peerings": [],
            "gcp_assets": [],
            "gcp_shared_vpc": {
                "host_project": "mock-host",
                "service_projects": ["mock-service"],
                "usable_subnets": []
            },
            "gcp_resource_locations": []
        }

def main():
    parser = argparse.ArgumentParser(description="nit-fabric High-Resolution Discoverer")
    parser.add_argument("--mode", choices=["mock", "cli", "terraform"], default="mock", help="Discovery mode")
    
    # Default to projects/nit-fabric/out/context.json
    default_output = Path(__file__).parent.parent.parent / "out" / "context.json"
    parser.add_argument("--output", default=str(default_output), help="Output file")
    parser.add_argument("--verbose", action="store_true", help="Show raw CLI commands being executed")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    discoverer = CloudDiscoverer(mode=args.mode)
    truth_report = discoverer.discover_all()

    with open(args.output, "w") as f:
        json.dump(truth_report, f, indent=2)
    
    logger.info(f"Discovery complete. Context archived to {args.output}")

if __name__ == "__main__":
    main()
