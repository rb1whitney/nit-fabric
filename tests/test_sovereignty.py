# TDD: Sovereignty Characterization Tests
import unittest
import sys
import os
import importlib.util

# Ensure local skills are discoverable
skills_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))

def load_skill_logic(skill_name):
    module_path = os.path.join(skills_path, skill_name, "logic.py")
    spec = importlib.util.spec_from_file_location(f"{skill_name}.logic", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sovereignty_logic = load_skill_logic("sovereignty-enforcer")

class TestSovereignty(unittest.TestCase):
    def test_audit_rule_characterization(self):
        """Characterize existing audit_rule behavior."""
        # Unrestricted egress should fail
        self.assertFalse(sovereignty_logic.audit_rule("0.0.0.0/0"))
        
        # Specific CIDR should pass
        self.assertTrue(sovereignty_logic.audit_rule("10.0.0.0/16"))

    def test_graph_validation_requirement(self):
        """Verify graph-based topology validation."""
        # Clean path should pass
        nodes = ["internal", "gateway", "restricted"]
        edges = [("internal", "gateway")]
        self.assertTrue(sovereignty_logic.audit_topology(nodes, edges))
        
        # Direct path to restricted should fail
        edges = [("internal", "restricted")]
        self.assertFalse(sovereignty_logic.audit_topology(nodes, edges))

if __name__ == "__main__":
    unittest.main()
