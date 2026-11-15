import unittest
from unittest.mock import MagicMock, patch

from nit_fabric.discover import CloudDiscoverer


class TestCloudDiscoverer(unittest.TestCase):
    def setUp(self):
        self.discoverer = CloudDiscoverer(mode="mock")

    def test_get_mock_data(self):
        data = self.discoverer._get_mock_data()
        self.assertIn("aws_cidrs", data)
        self.assertIn("gcp_cidrs", data)
        self.assertTrue(len(data["aws_cidrs"]) > 0)

    @patch("nit_fabric.discover.logger")
    def test_discover_all_mock_mode(self, mock_logger):
        data = self.discoverer.discover_all()
        self.assertIn("aws_cidrs", data)
        self.assertIn("sovereignty_score", data)
        mock_logger.info.assert_any_call("Running in MOCK mode. Returning synthetic truth-report.")

    @patch("nit_fabric.discover.AWSDiscoverer")
    @patch("nit_fabric.discover.GCPDiscoverer")
    @patch("nit_fabric.discover.SovereigntyGovernor")
    @patch("nit_fabric.discover.CloudDiscoverer._run_cli")
    def test_discover_all_cli_mode(self, mock_run_cli, mock_gov_cls, mock_gcp_cls, mock_aws_cls):
        # Setup
        disc = CloudDiscoverer(mode="cli")
        
        mock_aws = mock_aws_cls.return_value
        mock_aws.discover_all.return_value = {
            "vpcs": [{"CidrBlock": "10.0.0.0/16"}],
            "aws_s3_buckets": []
        }
        
        mock_gcp = mock_gcp_cls.return_value
        mock_gcp.discover_all.return_value = {
            "gcp_cidrs": ["10.1.0.0/16"]
        }
        
        mock_gov = mock_gov_cls.return_value
        mock_gov.calculate_score.return_value = {"sovereignty_score": 100}
        
        mock_run_cli.side_effect = ["my-project", '{"parent": {"type": "organization", "id": "123"}}']

        # Execute
        data = disc.discover_all()

        # Verify
        self.assertEqual(data["aws_cidrs"], ["10.0.0.0/16"])
        self.assertEqual(data["gcp_cidrs"], ["10.1.0.0/16"])
        self.assertEqual(data["sovereignty_score"], 100)
        mock_aws.discover_all.assert_called_once()
        mock_gcp.discover_all.assert_called_once_with("my-project", "organizations/123")

    def test_run_cli_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="output", returncode=0)
            result = self.discoverer._run_cli(["ls"])
            self.assertEqual(result, "output")

    def test_run_cli_failure(self):
        with patch("subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.CalledProcessError(1, ["ls"], stderr="error")
            with self.assertRaises(RuntimeError):
                self.discoverer._run_cli(["ls"])

if __name__ == "__main__":
    unittest.main()
