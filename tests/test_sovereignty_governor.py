import unittest
import sys
import os

# Adjust path to import nit_fabric modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from nit_fabric.sovereignty_governor import SovereigntyGovernor

class TestSovereigntyGovernor(unittest.TestCase):
    def test_calculate_score_fully_compliant(self):
        """Verify 100/100 score under perfect conditions."""
        context = {
            "gcp_instances": [{"name": "inst-1", "has_external_ip": False}],
            "aws_s3_buckets": [{"name": "bucket-1", "public_access": False}],
            "gcp_firewall_rules": [{"name": "rule-1", "source_ranges": ["10.0.0.0/8"]}],
            "gke_clusters": [{"name": "cluster-1", "workload_identity_enabled": True}],
            "gcp_subnets": [{"name": "sub-1", "region": "us-central1"}]
        }
        
        governor = SovereigntyGovernor()
        res = governor.calculate_score(context)
        self.assertEqual(res["sovereignty_score"], 100.0)
        self.assertEqual(res["compliance_status"], "COMPLIANT")
        self.assertEqual(len(res["remediation_tips"]), 0)

    def test_calculate_score_violations(self):
        """Verify deductions and compliance failure on security breaches."""
        context = {
            "gcp_instances": [{"name": "inst-public", "has_external_ip": True}], # -20 Network
            "aws_s3_buckets": [{"name": "bucket-public", "public_access": True}], # -30 Network
            "gcp_firewall_rules": [{"name": "rule-wide", "source_ranges": ["0.0.0.0/0"]}], # -40 Network
            "gke_clusters": [{"name": "cluster-no-wi", "workload_identity_enabled": False}], # -50 Identity
            "gcp_subnets": [{"name": "sub-foreign", "region": "asia-east1"}] # -20 Data
        }
        
        governor = SovereigntyGovernor()
        res = governor.calculate_score(context)
        
        # Network: 100 - 20 - 30 - 40 = 10
        # Identity: 100 - 50 = 50
        # Data: 100 - 20 = 80
        # Score: (10 * 0.40) + (50 * 0.30) + (80 * 0.30) = 4 + 15 + 24 = 43
        self.assertEqual(res["sovereignty_score"], 43.0)
        self.assertEqual(res["compliance_status"], "NON_COMPLIANT")
        self.assertGreater(len(res["remediation_tips"]), 0)

if __name__ == "__main__":
    unittest.main()
