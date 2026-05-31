import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from nit_fabric.preflight import PreFlightChecker

class TestPreFlightChecker(unittest.TestCase):
    def setUp(self):
        self.checker = PreFlightChecker()

    @patch("subprocess.run")
    def test_check_aws_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.checker.check_aws())

    @patch("subprocess.run")
    def test_check_aws_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.assertFalse(self.checker.check_aws())

    @patch("subprocess.run")
    def test_check_gcloud_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.checker.check_gcloud())

    @patch("subprocess.run")
    def test_check_gcloud_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.assertFalse(self.checker.check_gcloud())

    def test_run_all_mock(self):
        # Mock mode should always return True and skip actual checks
        self.assertTrue(self.checker.run_all(mode="mock"))

if __name__ == "__main__":
    unittest.main()
