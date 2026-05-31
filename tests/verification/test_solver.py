import unittest
from nit_fabric.verification.solver import NetworkSolver
from nit_fabric.verification.models import FirewallAction, SecurityGroupAction, RouteAction
from nit_fabric.verification.generator import RemediationGenerator

class TestFormalVerificationEngine(unittest.TestCase):
    """
    Test suite for Phase 3 Formal Verification Engine.
    """
    
    def setUp(self) -> None:
        self.solver = NetworkSolver()
        self.generator = RemediationGenerator()

    def test_cidr_containment_proven(self) -> None:
        # 10.0.0.0/24 is a subnet of 10.0.0.0/16
        is_contained = self.solver.check_containment("10.0.0.0/16", "10.0.0.0/24")
        self.assertTrue(is_contained)

    def test_cidr_containment_rejected(self) -> None:
        # 10.1.0.0/24 is NOT a subnet of 10.0.0.0/16
        is_contained = self.solver.check_containment("10.0.0.0/16", "10.1.0.0/24")
        self.assertFalse(is_contained)

    def test_cidr_overlap_proven(self) -> None:
        # 10.0.0.0/16 and 10.0.1.0/24 overlap
        overlaps = self.solver.check_overlap("10.0.0.0/16", "10.0.1.0/24")
        self.assertTrue(overlaps)

    def test_cidr_overlap_rejected(self) -> None:
        # 10.0.0.0/16 and 10.1.0.0/16 do NOT overlap
        overlaps = self.solver.check_overlap("10.0.0.0/16", "10.1.0.0/16")
        self.assertFalse(overlaps)

    def test_ingress_verification_secure(self) -> None:
        # Firewall rules only allow internal private access
        rules = [
            {
                "action": "allow",
                "direction": "ingress",
                "source_ranges": ["10.0.0.0/8"],
                "destination_ranges": ["10.0.1.0/24"]
            }
        ]
        is_secure, counterexample = self.solver.verify_ingress_security(rules, "10.0.1.0/24")
        self.assertTrue(is_secure)
        self.assertIsNone(counterexample)

    def test_ingress_verification_vulnerable(self) -> None:
        # Rules allow public 0.0.0.0/0 to the database zone
        rules = [
            {
                "action": "allow",
                "direction": "ingress",
                "source_ranges": ["0.0.0.0/0"],
                "destination_ranges": ["10.0.1.0/24"]
            }
        ]
        is_secure, counterexample = self.solver.verify_ingress_security(rules, "10.0.1.0/24")
        self.assertFalse(is_secure)
        self.assertIsNotNone(counterexample)
        self.assertIn("Vulnerability Discovered", counterexample)

    def test_remediation_generator_firewall(self) -> None:
        action = FirewallAction(
            name="allow-internal-https",
            network="default",
            action="allow",
            direction="INGRESS",
            priority=1000,
            source_ranges=["10.0.0.0/16"],
            allowed_protocols=["tcp"],
            ports=["443"]
        )
        hcl = self.generator.generate_hcl(action)
        self.assertIn('resource "google_compute_firewall" "allow-internal-https"', hcl)
        self.assertIn('network   = "default"', hcl)
        self.assertIn('source_ranges      = ["10.0.0.0/16"]', hcl)

    def test_remediation_generator_security_group(self) -> None:
        action = SecurityGroupAction(
            security_group_id="sg-99999",
            rule_type="ingress",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["10.0.0.0/16"]
        )
        hcl = self.generator.generate_hcl(action)
        self.assertIn('resource "aws_security_group_rule" "remediation_sg-99999"', hcl)
        self.assertIn('cidr_blocks       = ["10.0.0.0/16"]', hcl)

if __name__ == "__main__":
    unittest.main()
