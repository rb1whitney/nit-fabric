import unittest
import tempfile
import shutil
from pathlib import Path
from nit_fabric.validator import ValidatorGate

class TestValidatorGate(unittest.TestCase):
    """
    Test suite for Phase 2 SRE Production Gate.
    """
    
    def setUp(self) -> None:
        self.gate = ValidatorGate()

    def test_terraform_validate_syntax_pass(self) -> None:
        valid_hcl = """
        resource "aws_security_group_rule" "allow_ssh" {
          type              = "ingress"
          from_port         = 22
          to_port           = 22
          protocol          = "tcp"
          cidr_blocks       = ["10.0.0.0/16"]
          security_group_id = "sg-123456"
        }
        """
        success, errors = self.gate.validate_syntax(valid_hcl)
        self.assertTrue(success, f"Syntax validation failed unexpectedly: {errors}")
        self.assertEqual(len(errors), 0)

    def test_terraform_validate_syntax_fail(self) -> None:
        invalid_hcl = """
        resource "aws_security_group_rule" "broken" {
          type = "ingress"
          # Missing closing brace and invalid attribute
          from_port = "invalid"
        """
        success, errors = self.gate.validate_syntax(invalid_hcl)
        self.assertFalse(success)
        self.assertTrue(len(errors) > 0)

    def test_opa_rego_ingress_block(self) -> None:
        # Ingress to 0.0.0.0/0 is a critical breach
        unsafe_patch_data = {
          "resource_type": "aws_security_group_rule",
          "cidr_blocks": ["0.0.0.0/0"],
          "from_port": 22,
          "to_port": 22,
          "protocol": "tcp"
        }
        violations = self.gate.evaluate_security(unsafe_patch_data)
        self.assertIn("Critical Breach: Unrestricted public ingress (0.0.0.0/0) is prohibited.", violations)

    def test_opa_rego_iam_wildcard_block(self) -> None:
        # Over-privileged IAM policy wildcard binding is prohibited
        unsafe_iam_data = {
          "resource_type": "aws_iam_policy",
          "actions": ["*"],
          "effect": "Allow",
          "resources": ["*"]
        }
        violations = self.gate.evaluate_security(unsafe_iam_data)
        self.assertIn("Least Privilege Violation: Wildcard actions or roles are prohibited.", violations)

    def test_opa_rego_destruction_block(self) -> None:
        # Destructive patches (contain destroy action) must be blocked
        unsafe_action = {
          "action_type": "destroy",
          "resource_name": "aws_vpc.hub_vpc"
        }
        violations = self.gate.evaluate_security(unsafe_action)
        self.assertIn("Destruction Violation: Resource destruction of critical assets is prohibited.", violations)

    def test_opa_rego_pass(self) -> None:
        # Safe configuration must pass cleanly
        safe_patch_data = {
          "resource_type": "aws_security_group_rule",
          "cidr_blocks": ["10.0.0.0/16"],
          "from_port": 443,
          "to_port": 443,
          "protocol": "tcp"
        }
        violations = self.gate.evaluate_security(safe_patch_data)
        self.assertEqual(len(violations), 0)

if __name__ == "__main__":
    unittest.main()
