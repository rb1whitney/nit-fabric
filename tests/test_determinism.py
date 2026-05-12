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

ipam_logic = load_skill_logic("ipam-expert")
RadixTrie = ipam_logic.RadixTrie

class TestIPAMDeterminism(unittest.TestCase):
    def test_radix_trie_overlap_detection(self):
        """Characterize existing overlap detection behavior."""
        trie = RadixTrie()
        trie.insert("10.0.0.0/16")
        
        # Direct match
        self.assertTrue(trie.check_overlap("10.0.0.0/16"))
        
        # Subnet match
        self.assertTrue(trie.check_overlap("10.0.1.0/24"))
        
        # Non-overlap
        self.assertFalse(trie.check_overlap("10.1.0.0/16"))

    def test_deterministic_assignment_requirement(self):
        """Verify new next_available functionality."""
        trie = RadixTrie()
        trie.insert("10.0.0.0/24") # Occupy first subnet
        
        # Should return 10.0.1.0/24 as next available in 10.0.0.0/16
        next_cidr = trie.next_available(parent="10.0.0.0/16", prefix_len=24)
        self.assertEqual(next_cidr, "10.0.1.0/24")

        # After inserting 10.0.1.0/24, next should be 10.0.2.0/24
        trie.insert("10.0.1.0/24")
        next_cidr = trie.next_available(parent="10.0.0.0/16", prefix_len=24)
        self.assertEqual(next_cidr, "10.0.2.0/24")

if __name__ == "__main__":
    unittest.main()
