# Nit-Fabric Agents & Skills

This repository follows the **Agentic Hub Standardization (ACS 2026)**.
All agent logic and skills are centrally managed in the `.agent/` directory.

## System Architecture
- **Physical Sovereignty:** Logic resides in `.agent/`.
- **Symlink Bridges:** Vendor directories (`.claude/`, `.gemini/`, `.github/`) use symlinks to access the vault.
- **Automation:** Run `python3 bin/nexus.py` to synchronize environment bridges.

## Agents
*No custom agents defined yet.*

## Skills
- **BGP Audit:** Multi-Cloud BGP status auditing and identity verification.
- **Discovery Ops:** Instructions for executing and interpreting Live-Truth discovery scans.
- **IPAM Expert:** Bit-mask algebra expert for VPC CIDR disjointness verification.
- **Remediation Ops:** Workflow for deterministic remediation and patch validation.
- **Sovereignty Enforcer:** Zero-Trust boundary validation and firewall audit logic.
