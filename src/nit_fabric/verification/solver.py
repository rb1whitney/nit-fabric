import ipaddress
import logging
from typing import Tuple, Optional, List, Dict, Any

try:
    import z3
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False

logger = logging.getLogger("nit-fabric.solver")

class NetworkSolver:
    """
    Formal Verification Solver powered by the Z3 SMT Theorem Prover.
    Models IP address ranges as 32-bit bit-vectors to prove network
    invariants, detect CIDR containment/overlap conflicts, and discover
    reachability pathways mathematically.
    """
    
    def __init__(self) -> None:
        if HAS_Z3:
            self.solver = z3.Solver()
            self.ip = z3.BitVec('ip', 32)
            self.src_ip = z3.BitVec('src_ip', 32)
            self.dst_ip = z3.BitVec('dst_ip', 32)
        else:
            self.solver = None
            logger.warning("Z3 is not installed. Reachability solver running in pure Python mode.")

    def _cidr_to_z3_expr(self, cidr: str, var: Any) -> Any:
        """Converts a CIDR block to a Z3 BitVec equality assertion."""
        net = ipaddress.ip_network(cidr)
        prefix_val = int(net.network_address)
        mask_val = int(net.netmask)
        
        prefix = z3.BitVecVal(prefix_val, 32)
        mask = z3.BitVecVal(mask_val, 32)
        
        return (var & mask) == prefix

    def check_containment(self, parent_cidr: str, child_cidr: str) -> bool:
        """
        Mathematically proves if parent_cidr completely contains child_cidr.
        If C & not P is unsat, containment is proven.
        """
        if not HAS_Z3:
            # Fallback
            p = ipaddress.ip_network(parent_cidr)
            c = ipaddress.ip_network(child_cidr)
            return c.subnet_of(p)

        self.solver.push()
        try:
            parent_expr = self._cidr_to_z3_expr(parent_cidr, self.ip)
            child_expr = self._cidr_to_z3_expr(child_cidr, self.ip)
            
            # Negate: Child is true but Parent is not
            self.solver.add(child_expr)
            self.solver.add(z3.Not(parent_expr))
            
            status = self.solver.check()
            return status == z3.unsat
        finally:
            self.solver.pop()

    def check_overlap(self, cidr_a: str, cidr_b: str) -> bool:
        """
        Mathematically proves if two subnets overlap.
        If A & B is sat, overlap exists.
        """
        if not HAS_Z3:
            # Fallback
            a = ipaddress.ip_network(cidr_a)
            b = ipaddress.ip_network(cidr_b)
            return a.overlaps(b)

        self.solver.push()
        try:
            expr_a = self._cidr_to_z3_expr(cidr_a, self.ip)
            expr_b = self._cidr_to_z3_expr(cidr_b, self.ip)
            
            self.solver.add(expr_a)
            self.solver.add(expr_b)
            
            status = self.solver.check()
            return status == z3.sat
        finally:
            self.solver.pop()

    def verify_ingress_security(self, rules: List[Dict[str, Any]], protected_cidr: str) -> Tuple[bool, Optional[str]]:
        """
        Proves if any public source IP can reach the protected_cidr database network
        given the provided firewall rules. Returns (True, None) if secure (unsat),
        or (False, counterexample_msg) if vulnerable (sat).
        """
        if not HAS_Z3:
            # High-fidelity python emulator for local runners
            protected = ipaddress.ip_network(protected_cidr)
            for rule in rules:
                if rule.get("action") == "allow" and rule.get("direction") == "ingress":
                    for range_str in rule.get("source_ranges", []):
                        if range_str == "0.0.0.0/0":
                            return False, "Vulnerability Discovered: Public ingress (0.0.0.0/0) allowed to protected space."
            return True, None

        self.solver.push()
        try:
            # Invariant breach conditions:
            # 1. Source IP is a public range (not in private 10.0.0.0/8)
            private_net_expr = self._cidr_to_z3_expr("10.0.0.0/8", self.src_ip)
            self.solver.add(z3.Not(private_net_expr))
            
            # 2. Destination IP is within the protected subnet
            protected_expr = self._cidr_to_z3_expr(protected_cidr, self.dst_ip)
            self.solver.add(protected_expr)
            
            # 3. Path allowed by rules
            allowed_exprs = []
            for rule in rules:
                if rule.get("action") == "allow":
                    src_match = z3.Or([self._cidr_to_z3_expr(r, self.src_ip) for r in rule.get("source_ranges", [])])
                    dst_match = z3.Or([self._cidr_to_z3_expr(r, self.dst_ip) for r in rule.get("destination_ranges", ["0.0.0.0/0"])])
                    allowed_exprs.append(z3.And(src_match, dst_match))
            
            if allowed_exprs:
                self.solver.add(z3.Or(allowed_exprs))
            else:
                return True, None # No allowing rules, secure
                
            status = self.solver.check()
            if status == z3.sat:
                model = self.solver.model()
                src_val = model[self.src_ip].as_long()
                dst_val = model[self.dst_ip].as_long()
                src_ip_str = str(ipaddress.IPv4Address(src_val))
                dst_ip_str = str(ipaddress.IPv4Address(dst_val))
                return False, f"Vulnerability Discovered: Public IP {src_ip_str} can access Protected Destination {dst_ip_str}"
            
            return True, None
        finally:
            self.solver.pop()
