#!/usr/bin/env python3
import sys
import subprocess
import argparse
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Pre-flight checks (only for scan command)
    if args.command == "scan":
        mode = getattr(args, "mode", "cli")
        checker = PreFlightChecker()
        if not checker.run_all(mode=mode):
            if mode != "mock":
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
            if args.explain:
                cmd.append("--explain")
            subprocess.run(cmd, check=True)
        
        elif args.command == "test":
            print("### nit-fabric regression test suite ###")
            subprocess.run([sys.executable, str(project_root / "tests" / "test_engine.py")], check=True)
    
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
