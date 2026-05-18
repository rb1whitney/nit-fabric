### Description
This PR implements the **Agentic Hub Standardization (ACS 2026)** to unify the agentic infrastructure and enforce "Physical Sovereignty" across the repository.

### Changes
- **Physical Sovereignty**: Logic is now centralized in the `.agent/` master vault.
- **Skill Migration**: All skills moved from root `skills/` to `.agent/skills/`.
- **Manifests**: Created root `AGENTS.md` and legacy `AGENT.md` bridge.
- **Automation**: Added `bin/nexus.py` to synchronize cross-IDE symlinks (Claude, Gemini, Copilot).
- **Vendor Bridges**: Established symlink bridges in `.claude/`, `.gemini/`, and `.github/`.
- **Zero-Duplication**: Enforced a single source of truth for agent logic.

### Verification
- Ran `python3 bin/nexus.py` to confirm symlink health.
- Verified file accessibility via vendor-specific directories.
- Confirmed Copilot discoverability with `.agent.md` suffixing.
