import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from nit_fabric.remediator import PolicyRemediator

class TestRemediator(unittest.TestCase):
    def setUp(self):
        self.remediator = PolicyRemediator()

    def test_analyze_failure_bgp_mismatch(self):
        """
        Ensures that the engine correctly identifies a BGP ASN mismatch
        and generates the appropriate removal/injection HCL patch.
        """
        scenario = {
            "id": "bgp-asn-mismatch",
            "symptom": "BGP Session Down",
            "truth_report": {
                "aws_tgw_asn": 64512,
                "gcp_router_asn": 64600
            }
        }
        
        investigation, patch = self.remediator.analyze_failure(scenario)
        
        self.assertIn("Finding: AWS ASN (64512) does not match GCP ASN (64600)", investigation)
        self.assertIn("- bgp { asn = 64600 }", patch)
        self.assertIn("+ bgp { asn = 64512 }", patch)

    def test_analyze_failure_malformed_input(self):
        """
        Verifies that the engine handles malformed truth reports without crashing.
        """
        scenario = {} # Missing id and violation_type to simulate malformed input
        
        investigation, patch = self.remediator.analyze_failure(scenario)
        
        self.assertEqual(investigation, "ERR_MALFORMED_INPUT")
        self.assertEqual(patch, "")

    def test_analyze_failure_unknown_mode(self):
        """
        Verifies that unrecognized failure modes are logged and returned as unknown.
        """
        scenario = {
            "id": "unknown-problem",
            "truth_report": {"some": "data"}
        }
        
        investigation, patch = self.remediator.analyze_failure(scenario)
        
        self.assertEqual(investigation, "Unknown failure mode: unknown-problem")
        self.assertEqual(patch, "")

if __name__ == "__main__":
    unittest.main()
