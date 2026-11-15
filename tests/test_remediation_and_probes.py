import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from nit_fabric.policies import InspectionVPCPolicy, VPCEndpointPolicy
from nit_fabric.preflight import PreFlightChecker
from nit_fabric.probes import aws_probe
from nit_fabric.remediator import PolicyRemediator
from nit_fabric.schemas import UnifiedSecurityRule
from nit_fabric.validator import ValidatorGate
from nit_fabric.verification.solver import NetworkSolver
from nit_fabric.visualizer import NetworkVisualizer


class TestRemediationAndProbes(unittest.TestCase):
    def test_cli_remediation_quotes_shell_metacharacters_and_validates(self):
        remediator = PolicyRemediator(provider="cli")
        scenario = {
            "id": "AWS_PUBLIC_S3",
            "metadata": {"bucket_name": "evil; rm -rf /"},
        }
        _, patch_out = remediator.analyze_failure(scenario)
        self.assertIn("aws s3api put-public-access-block", patch_out)
        self.assertIn("'evil; rm -rf /'", patch_out)

    def test_terraform_templates_render_valid_hcl_blocks(self):
        remediator = PolicyRemediator(provider="terraform")
        for scenario in [
            {
                "id": "bgp-asn-mismatch",
                "truth_report": {"aws_tgw_asn": 64512, "gcp_router_asn": 65000},
            },
            {
                "id": "AWS_PUBLIC_S3",
                "metadata": {"bucket_name": "my-public-bucket"},
            },
            {
                "id": "GCP_EXTERNAL_IP",
                "metadata": {"instance_name": "web-vm-1"},
            },
            {
                "id": "UNRESTRICTED_INGRESS",
                "rule": {"rule_id": "allow-ssh", "port_range": "22"},
            },
        ]:
            _, patch_out = remediator.analyze_failure(scenario)
            self.assertIn("resource \"", patch_out)
            self.assertNotIn("\n- ", patch_out)

    def test_validator_gate_catches_nested_rule_and_wildcard_iam(self):
        gate = ValidatorGate()
        nested_ingress = {
            "rule": {"direction": "INGRESS", "action": "ALLOW", "source_cidr": "::/0"}
        }
        self.assertTrue(gate.evaluate_security(nested_ingress))

        wildcard_iam = {
            "metadata": {
                "resource_type": "aws_iam_policy",
                "effect": "Allow",
                "actions": ["s3:*"],
            }
        }
        self.assertTrue(gate.evaluate_security(wildcard_iam))

    def test_policies_handle_boto3_vpc_id_key(self):
        ctx = {"vpcs": [{"VpcId": "vpc-inspection-123", "endpoints": []}]}
        insp = InspectionVPCPolicy("Inspection", "desc").evaluate(ctx)
        self.assertEqual(insp, [])

        ep_violations = VPCEndpointPolicy("EP", "desc").evaluate(ctx)
        self.assertTrue(any("vpc-inspection-123" in v.remediation_proposal for v in ep_violations))

    def test_visualizer_keeps_s3_database_nodes_and_vpc_id(self):
        import tempfile

        ctx = {
            "vpcs": [{"VpcId": "vpc-abc", "endpoints": []}],
            "aws_s3_buckets": [{"name": "logs-bucket"}],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
            json.dump(ctx, f)
            f.flush()
            viz = NetworkVisualizer(f.name)
        viz.build_topology()
        mermaid = viz.emit_mermaid()
        self.assertIn("VPC: vpc-abc", mermaid)
        self.assertIn("logs-bucket", mermaid)

    def test_preflight_check_gcloud_requires_non_empty_account(self):
        checker = PreFlightChecker()
        with patch("subprocess.run", return_value=MagicMock(stdout="   \n")):
            self.assertFalse(checker.check_gcloud())
        with patch("subprocess.run", return_value=MagicMock(stdout="user@example.com\n")):
            self.assertTrue(checker.check_gcloud())

    def test_aws_probe_blocks_ssrf_and_enforces_token(self):
        with patch.dict(os.environ, {"PROBE_AUTH_TOKEN": "secret-token"}):
            unauth = aws_probe.lambda_handler({"rawPath": "/ping", "headers": {}}, None)
            self.assertEqual(unauth["statusCode"], 401)

            ssrf = aws_probe.lambda_handler(
                {
                    "rawPath": "/test-gcp",
                    "headers": {"Authorization": "Bearer secret-token"},
                    "body": json.dumps({"url": "http://169.254.169.254/latest/meta-data/"}),
                },
                None,
            )
            self.assertEqual(ssrf["statusCode"], 403)

            port_block = aws_probe.lambda_handler(
                {
                    "rawPath": "/check-port",
                    "headers": {"Authorization": "Bearer secret-token"},
                    "body": json.dumps({"host": "169.254.169.254", "port": 80}),
                },
                None,
            )
            self.assertEqual(port_block["statusCode"], 403)

    def test_solver_handles_rfc1918_172_and_192_networks(self):
        solver = NetworkSolver()
        rules = [
            {
                "action": "ALLOW",
                "direction": "INGRESS",
                "source_ranges": ["192.168.1.0/24", "172.16.10.0/24"],
                "destination_ranges": ["10.0.1.0/24"],
            }
        ]
        is_safe, msg = solver.verify_ingress_security(rules, "10.0.1.0/24")
        self.assertTrue(is_safe, msg)

        _ = UnifiedSecurityRule(rule_id="r1", platform="AWS", direction="INGRESS", action="ALLOW")


if __name__ == "__main__":
    unittest.main()
