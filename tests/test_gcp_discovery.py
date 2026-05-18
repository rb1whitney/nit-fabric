import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Adjust path to import nit_fabric modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from nit_fabric.gcp_discoverer import GCPDiscoverer

class TestGCPDiscovery(unittest.TestCase):
    def setUp(self):
        self.discoverer = GCPDiscoverer()

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_shared_vpc_resolver(self, mock_cli):
        """Verify host and service project subnets are mapped correctly."""
        mock_cli.side_effect = [
            # gcloud compute shared-vpc list-associated-resources
            '[{"resourceId":"service-proj-01", "resourceType":"PROJECT"}]',
            # gcloud compute networks subnets list-usable
            '[{"ipCidrRange":"10.10.1.0/24", "network":"host-vpc", "subnet":"usable-sub-01"}]'
        ]
        
        shared_vpc_data = self.discoverer.get_shared_vpc_topology("host-proj-01")
        self.assertEqual(shared_vpc_data["host_project"], "host-proj-01")
        self.assertIn("service-proj-01", shared_vpc_data["service_projects"])
        self.assertEqual(len(shared_vpc_data["usable_subnets"]), 1)
        self.assertEqual(shared_vpc_data["usable_subnets"][0]["subnet"], "usable-sub-01")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_vpc_peerings(self, mock_cli):
        """Verify VPC network peerings are parsed correctly."""
        mock_cli.return_value = '[{"name": "peering-01", "network": "https://www.googleapis.com/.../default", "peerNetwork": "https://www.googleapis.com/.../peer-vpc", "state": "ACTIVE"}]'
        peerings = self.discoverer.get_vpc_peerings("my-project")
        self.assertEqual(len(peerings), 1)
        self.assertEqual(peerings[0]["name"], "peering-01")
        self.assertEqual(peerings[0]["state"], "ACTIVE")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_hierarchical_firewalls(self, mock_cli):
        """Verify Org/Folder level firewall policies are resolved."""
        mock_cli.return_value = '[{"name":"org-policy-01", "rules":[{"priority":10, "action":"deny", "direction":"EGRESS", "match":{"destRanges":["0.0.0.0/0"]}}]}]'
        
        policies = self.discoverer.get_hierarchical_firewalls("organizations/12345")
        self.assertEqual(len(policies), 1)
        self.assertEqual(policies[0]["name"], "org-policy-01")
        self.assertEqual(policies[0]["rules"][0]["action"], "deny")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_project_firewall_rules(self, mock_cli):
        """Verify project firewall rules are parsed and formatted correctly."""
        mock_cli.return_value = '[{"name": "allow-ssh", "network": "global/networks/default", "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}], "sourceRanges": ["0.0.0.0/0"], "disabled": false, "priority": 1000}]'
        rules = self.discoverer.get_project_firewall_rules("my-project")
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], "allow-ssh")
        self.assertEqual(rules[0]["network"], "default")
        self.assertEqual(rules[0]["priority"], 1000)

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_workload_identity_validator(self, mock_cli):
        """Verify GKE Workload Identity bindings are audited."""
        mock_cli.return_value = '{"bindings": [{"role": "roles/iam.workloadIdentityUser", "members": ["serviceAccount:my-project.svc.id.goog[default/ksa-01]"]}]}'
        
        bindings = self.discoverer.audit_workload_identity("gsa-01@my-project.iam.gserviceaccount.com")
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0], "default/ksa-01")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_project_iam_policy(self, mock_cli):
        """Verify project IAM policy bindings are parsed correctly."""
        mock_cli.return_value = '{"bindings": [{"role": "roles/editor", "members": ["serviceAccount:my-sa@my-project.iam.gserviceaccount.com"]}]}'
        bindings = self.discoverer.get_project_iam_policy("my-project")
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0]["role"], "roles/editor")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_asset_inventory_resources(self, mock_cli):
        """Verify asset inventory query parsing."""
        mock_cli.return_value = '[{"name": "//compute.googleapis.com/projects/my-project/zones/us-central1-a/instances/my-vm", "assetType": "compute.googleapis.com/Instance"}]'
        assets = self.discoverer.get_asset_inventory_resources("my-project")
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["assetType"], "compute.googleapis.com/Instance")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_get_instances(self, mock_cli):
        """Verify compute instance scanning handles external IP auditing correctly."""
        mock_cli.return_value = '[{"name": "secure-instance", "zone": "global/zones/us-central1-a", "networkInterfaces": [{"accessConfigs": [{"type": "ONE_TO_ONE_NAT", "natIP": "34.56.78.90"}]}]}]'
        instances = self.discoverer.get_instances("my-project")
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["name"], "secure-instance")
        self.assertTrue(instances[0]["has_external_ip"])
        self.assertEqual(instances[0]["zone"], "us-central1-a")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_gke_clusters(self, mock_cli):
        """Verify GKE cluster workload identity config audit."""
        mock_cli.return_value = '[{"name": "prod-cluster", "location": "us-central1", "workloadIdentityConfig": {"workloadPool": "my-project.svc.id.goog"}, "nodePools": [{"name": "system-pool"}]}]'
        clusters = self.discoverer.get_gke_clusters("my-project")
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["name"], "prod-cluster")
        self.assertTrue(clusters[0]["workload_identity_enabled"])

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_get_subnets(self, mock_cli):
        """Verify subnet scanning mapping."""
        mock_cli.return_value = '[{"name": "sub-1", "privateIpGoogleAccess": true, "region": "global/regions/us-central1"}]'
        subnets = self.discoverer.get_subnets("my-project")
        self.assertEqual(len(subnets), 1)
        self.assertEqual(subnets[0]["name"], "sub-1")
        self.assertTrue(subnets[0]["private_google_access"])
        self.assertEqual(subnets[0]["region"], "us-central1")

    @patch.object(GCPDiscoverer, "_run_cli")
    def test_discover_all_orchestrator(self, mock_cli):
        """Verify discover_all triggers all internal mapping sub-methods correctly."""
        # Setup mock responses for every gcloud call triggered inside discover_all
        mock_cli.side_effect = [
            # get_shared_vpc_topology
            '[]', '[]',
            # get_vpc_peerings
            '[]',
            # get_hierarchical_firewalls
            '[]',
            # get_project_firewall_rules
            '[]',
            # get_project_iam_policy
            '{}',
            # get_asset_inventory_resources
            '[]',
            # get_instances
            '[]',
            # get_gke_clusters
            '[]',
            # get_subnets
            '[]',
            # get_vpc_service_controls
            '[]',
            # get_scc_findings
            '[]',
            # get_resource_locations
            '[]'
        ]
        
        data = self.discoverer.discover_all("my-project", "folders/123")
        self.assertIn("gcp_shared_vpc", data)
        self.assertIn("gcp_peerings", data)
        self.assertIn("gcp_hierarchical_firewalls", data)
        self.assertIn("gcp_firewall_rules", data)
        self.assertIn("gcp_iam_policies", data)
        self.assertIn("gcp_assets", data)

if __name__ == "__main__":
    unittest.main()
