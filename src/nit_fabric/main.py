#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

# Add src to sys.path to allow imports when running directly
sys.path.append(str(Path(__file__).parent.parent))

try:
    from nit_fabric.preflight import PreFlightChecker
except ImportError:
    # Fallback for different execution contexts
    from preflight import PreFlightChecker

def main():
    parser = argparse.ArgumentParser(description="nit-fabric Industrial Connectivity Engine")
    subparsers = parser.add_subparsers(dest="command", help="Operational commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Execute security and connectivity scan")
    scan_parser.add_argument("--mode", choices=["mock", "cli", "terraform"], default="mock", help="Discovery mode")
    scan_parser.add_argument("--verbose", action="store_true", help="Show raw CLI commands during discovery")

    # Visualize command
    subparsers.add_parser("visualize", help="Synthesize network topology (Mermaid)")

    # Remediate command
    rem_parser = subparsers.add_parser("remediate", help="Generate and validate remediation patches")
    rem_parser.add_argument("--provider", choices=["terraform", "cli"], default="terraform", help="Remediation provider")
    rem_parser.add_argument("--validate", action="store_true", help="Perform validation check")
    rem_parser.add_argument("--explain", action="store_true", help="Just explain how to fix each issue (Advisor Mode)")

    # Test command
    subparsers.add_parser("test", help="Execute TDD Coverage Audit")

    # Probe command
    probe_parser = subparsers.add_parser("probe", help="Run active connectivity probes between clouds")
    probe_parser.add_argument("--gcp-url", help="GCP Probe URL")
    probe_parser.add_argument("--aws-url", help="AWS Probe URL")
    probe_parser.add_argument("--check-port", nargs=3, metavar=("SOURCE", "HOST", "PORT"), help="Check port from source (gcp/aws) to host:port")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Pre-flight checks (only for scan command)
    if args.command == "scan":
        mode = getattr(args, "mode", "cli")
        checker = PreFlightChecker()
        if not checker.run_all(mode=mode) and mode != "mock":
            print("[FATAL] Pre-flight checks failed. Aborting.")
            sys.exit(1)

    base_dir = Path(__file__).parent
    project_root = base_dir.parent.parent
    
    # Ensure out directory exists
    out_dir = project_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if args.command == "scan":
            cmd = [sys.executable, str(base_dir / "discover.py"), "--mode", args.mode]
            if args.verbose:
                cmd.append("--verbose")
            subprocess.run(cmd, check=True)
            subprocess.run([sys.executable, str(base_dir / "security_graph.py")], check=True)
        
        elif args.command == "visualize":
            subprocess.run([sys.executable, str(base_dir / "visualizer.py")], check=True)
        
        elif args.command == "remediate":
            cmd = [sys.executable, str(base_dir / "remediator.py"), "--provider", args.provider]
            if args.validate:
                cmd.append("--validate")
            if args.explain:
                cmd.append("--explain")
            subprocess.run(cmd, check=True)
        
        elif args.command == "test":
            print("### nit-fabric regression test suite ###")
            subprocess.run([sys.executable, "-m", "pytest", str(project_root / "tests")], check=True)
        
        elif args.command == "probe":
            from nit_fabric.probe_manager import ProbeManager
            
            gcp_url = args.gcp_url
            aws_url = args.aws_url
            
            # Try to auto-discover from context.json
            context_path = project_root / "out" / "context.json"
            if (not gcp_url or not aws_url) and context_path.exists():
                with open(context_path) as f:
                    context = json.load(f)
                    if not gcp_url:
                        gcp_probes = context.get("gcp_probes", [])
                        if gcp_probes:
                            gcp_url = gcp_probes[0].get("url")
                            print(f"[*] Auto-discovered GCP Probe: {gcp_url}")
                    if not aws_url:
                        aws_probes = context.get("aws_probes", [])
                        if aws_probes:
                            aws_url = aws_probes[0].get("url")
                            print(f"[*] Auto-discovered AWS Probe: {aws_url}")

            manager = ProbeManager(gcp_url=gcp_url, aws_url=aws_url)
            
            if args.check_port:
                source, host, port = args.check_port
                url = gcp_url if source.lower() == "gcp" else aws_url
                if not url:
                    print(f"[ERROR] {source.upper()} URL required for port check")
                    sys.exit(1)
                result = manager.check_port(url, host, int(port))
                print(json.dumps(result, indent=2))
            else:
                results = manager.run_tests()
                print("\n### Probe Results ###")
                for r in results:
                    status_col = "\033[92mPASS\033[0m" if r["status"] == "PASS" else "\033[91mFAIL\033[0m"
                    latency = f" ({r['latency']})" if "latency" in r else ""
                    error = f" - {r['error']}" if "error" in r else ""
                    print(f"[{status_col}] {r['test']}{latency}{error}")
    
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
