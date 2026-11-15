import subprocess
import time

import requests


class ProbeManager:
    def __init__(self, gcp_url=None, aws_url=None, gcp_token=None):
        self.gcp_url = gcp_url
        self.aws_url = aws_url
        self.gcp_token = gcp_token

    def _get_gcp_headers(self):
        token = self.gcp_token
        if not token and self.gcp_url:
            try:
                res = subprocess.run(
                    ["gcloud", "auth", "print-identity-token"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                token = res.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                token = None
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _headers_for(self, url):
        if self.gcp_url and url == self.gcp_url:
            return self._get_gcp_headers()
        return {}

    def run_tests(self):
        results = []

        if self.gcp_url:
            print(f"[*] Testing GCP Probe at {self.gcp_url}")
            results.append(self._test_ping(self.gcp_url, "GCP"))
            if self.aws_url:
                results.append(self._test_cross_cloud(self.gcp_url, self.aws_url, "GCP-to-AWS"))

        if self.aws_url:
            print(f"[*] Testing AWS Probe at {self.aws_url}")
            results.append(self._test_ping(self.aws_url, "AWS"))
            if self.gcp_url:
                results.append(self._test_cross_cloud(self.aws_url, self.gcp_url, "AWS-to-GCP"))

        return results

    def _test_ping(self, url, cloud):
        try:
            start = time.time()
            headers = self._headers_for(url) if cloud == "GCP" else {}
            resp = requests.get(f"{url.rstrip('/')}/ping", headers=headers, timeout=5)
            latency = (time.time() - start) * 1000
            if resp.status_code == 200:
                return {"test": f"{cloud} Ping", "status": "PASS", "latency": f"{latency:.2f}ms"}
            return {"test": f"{cloud} Ping", "status": "FAIL", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"test": f"{cloud} Ping", "status": "FAIL", "error": str(e)}

    def _test_cross_cloud(self, source_url, target_url, direction):
        try:
            endpoint = "/test-aws" if "GCP" in direction else "/test-gcp"
            headers = self._headers_for(source_url)
            resp = requests.post(
                f"{source_url.rstrip('/')}{endpoint}",
                json={"url": f"{target_url.rstrip('/')}/ping"},
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                return {"test": direction, "status": "PASS"}
            return {"test": direction, "status": "FAIL", "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"test": direction, "status": "FAIL", "error": str(e)}

    def check_port(self, source_url, host, port):
        try:
            headers = self._headers_for(source_url)
            resp = requests.post(
                f"{source_url.rstrip('/')}/check-port",
                json={"host": host, "port": port},
                headers=headers,
                timeout=10,
            )
            return resp.json()
        except Exception as e:
            return {"status": "failure", "message": str(e)}
