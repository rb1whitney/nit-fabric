import unittest

from nit_fabric.probe_manager import ProbeManager


class TestProbeManager(unittest.TestCase):
    def test_init(self):
        manager = ProbeManager(gcp_url="http://gcp", aws_url="http://aws")
        self.assertEqual(manager.gcp_url, "http://gcp")
        self.assertEqual(manager.aws_url, "http://aws")

    def test_test_ping_fail(self):
        # Should fail as URLs are invalid
        manager = ProbeManager(gcp_url="http://invalid-gcp-url", aws_url="http://invalid-aws-url")
        results = manager.run_tests()
        for r in results:
            if "Ping" in r["test"]:
                self.assertEqual(r["status"], "FAIL")

if __name__ == "__main__":
    unittest.main()
