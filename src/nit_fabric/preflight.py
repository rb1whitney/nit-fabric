import subprocess
import sys

class PreFlightChecker:
    """Verifies environment readiness for nit-fabric operations."""
    
    def check_aws(self) -> bool:
        """Verify AWS CLI authentication."""
        try:
            subprocess.run(
                ["aws", "sts", "get-caller-identity"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def check_gcloud(self) -> bool:
        """Verify Google Cloud CLI authentication."""
        try:
            # Using 'config list' as a lightweight check that doesn't require a full token refresh if not needed
            subprocess.run(
                ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def run_all(self, mode: str = "cli") -> bool:
        """Run all checks and return status. In mock mode, always returns True."""
        if mode == "mock":
            print("[PREFLIGHT] Mock mode enabled. Skipping auth checks.")
            return True
            
        print("[PREFLIGHT] Verifying cloud provider authentication...")
        aws_ok = self.check_aws()
        gcloud_ok = self.check_gcloud()
        
        if not aws_ok:
            print("[PREFLIGHT] ERROR: AWS authentication failed. Run 'aws configure' or check credentials.")
        else:
            print("[PREFLIGHT] AWS authentication: OK")
            
        if not gcloud_ok:
            print("[PREFLIGHT] ERROR: Google Cloud authentication failed. Run 'gcloud auth login'.")
        else:
            print("[PREFLIGHT] Google Cloud authentication: OK")
            
        return aws_ok and gcloud_ok
