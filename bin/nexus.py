import os

def setup_symlinks():
    # Root Level Bridges
    root_links = {
        "AGENT.md": "AGENTS.md",
        "CLAUDE.md": "AGENTS.md",
        "GEMINI.md": "AGENTS.md",
    }
    
    for target, source in root_links.items():
        if os.path.islink(target):
            os.remove(target)
        elif os.path.exists(target):
            os.rename(target, target + ".bak")
        os.symlink(source, target)
        print(f"Linked {target} -> {source}")

    # GitHub Copilot root bridge
    copilot_instr = ".github/copilot-instructions.md"
    os.makedirs(".github", exist_ok=True)
    if os.path.islink(copilot_instr):
        os.remove(copilot_instr)
    os.symlink("../AGENTS.md", copilot_instr)
    print(f"Linked {copilot_instr} -> ../AGENTS.md")

    # Vendor Directory Bridges
    vendors = [".claude", ".gemini", ".github", ".copilot"]
    for vendor in vendors:
        os.makedirs(vendor, exist_ok=True)
        
        # Bridge: agents
        agent_target = os.path.join(vendor, "agents")
        if os.path.islink(agent_target):
            os.remove(agent_target)
        elif os.path.isdir(agent_target):
            # If it's a real dir, we need to handle its contents or replace it
            # Standard ACS 2026 says vendor dirs are populated with symlinks.
            # However, for 'agents' subfolder, we might want to link the folder or individual files.
            # The prompt says: "populated exclusively with symlinks that point back to the .agent/ master vault"
            # and ".claude/agents/swarm-engineer.md -> ../../.agent/agents/swarm-engineer.md"
            # This implies individual files.
            pass
        
        os.makedirs(agent_target, exist_ok=True)
        
        agent_vault = os.path.join(".agent", "agents")
        if os.path.exists(agent_vault):
            for agent_file in os.listdir(agent_vault):
                if not agent_file.endswith(".md"): continue
                
                source = os.path.join("../../.agent/agents", agent_file)
                if vendor == ".github":
                    target_name = agent_file.replace(".md", ".agent.md")
                else:
                    target_name = agent_file
                
                target = os.path.join(agent_target, target_name)
                if os.path.islink(target):
                    os.remove(target)
                os.symlink(source, target)
                print(f"Linked {target} -> {source}")

        # Bridge: skills
        skill_target = os.path.join(vendor, "skills")
        if os.path.islink(skill_target):
            os.remove(skill_target)
        # Link the whole skills directory to maintain structure
        os.symlink("../.agent/skills", skill_target)
        print(f"Linked {skill_target} -> ../.agent/skills")

if __name__ == "__main__":
    setup_symlinks()
    print("Nexus Synchronization Complete: Physical Sovereignty Enforced.")
