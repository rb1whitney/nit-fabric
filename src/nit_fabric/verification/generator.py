from typing import Union
from nit_fabric.verification.models import FirewallAction, SecurityGroupAction, RouteAction

class RemediationGenerator:
    """
    Type-safe HCL Patch Generator. Bypasses Jinja2 string-bashing in favor
    of structured Parameterized Remediation DSL schemas.
    """
    
    def generate_hcl(self, action: Union[FirewallAction, SecurityGroupAction, RouteAction]) -> str:
        """
        Translates a structured action schema object into syntax-compliant HCL code blocks.

        Purpose:
            Convert intermediate action models (Pydantic objects) into valid Terraform resource declarations.
        Inputs:
            action (Union[FirewallAction, SecurityGroupAction, RouteAction]): Verifiable action schema instance.
        Outputs:
            str: Generated HCL configuration string representing the remediation resource.
        """
        if isinstance(action, FirewallAction):
            return self._generate_firewall_hcl(action)
        elif isinstance(action, SecurityGroupAction):
            return self._generate_security_group_hcl(action)
        elif isinstance(action, RouteAction):
            return self._generate_route_hcl(action)
        else:
            raise TypeError(f"Unsupported action type: {type(action)}")

    def _generate_firewall_hcl(self, action: FirewallAction) -> str:
        # GCP Firewall Rules format
        allowed_block = ""
        if action.allowed_protocols:
            ports_str = ", ".join(f'"{p}"' for p in action.ports)
            ports_line = f"ports    = [{ports_str}]" if action.ports else ""
            allowed_block = f"""
  {action.action} {{
    protocol = "{action.allowed_protocols[0]}"
    {ports_line}
  }}"""
        
        sources_str = ", ".join(f'"{r}"' for r in action.source_ranges)
        dests_str = ", ".join(f'"{r}"' for r in action.destination_ranges)
        
        source_ranges_line = f'  source_ranges      = [{sources_str}]' if action.source_ranges else ""
        dest_ranges_line = f'  destination_ranges = [{dests_str}]' if action.destination_ranges else ""

        hcl = f"""resource "google_compute_firewall" "{action.name}" {{
  name      = "{action.name}"
  network   = "{action.network}"
  direction = "{action.direction}"
  priority  = {action.priority}
{allowed_block}
{source_ranges_line}
{dest_ranges_line}
}}"""
        # Strip empty lines
        return "\n".join(line for line in hcl.splitlines() if line.strip())

    def _generate_security_group_hcl(self, action: SecurityGroupAction) -> str:
        # AWS Security Group rules format
        cidrs_str = ", ".join(f'"{c}"' for c in action.cidr_blocks)
        
        return f"""resource "aws_security_group_rule" "remediation_{action.security_group_id}" {{
  type              = "{action.rule_type}"
  from_port         = {action.from_port}
  to_port           = {action.to_port}
  protocol          = "{action.protocol}"
  cidr_blocks       = [{cidrs_str}]
  security_group_id = "{action.security_group_id}"
}}"""

    def _generate_route_hcl(self, action: RouteAction) -> str:
        # Route Table Entry HCL format
        target_attr = "gateway_id"
        if action.target_type == "nat_gateway":
            target_attr = "nat_gateway_id"
        elif action.target_type == "transit_gateway":
            target_attr = "transit_gateway_id"
        elif action.target_type == "vpc_peering":
            target_attr = "vpc_peering_connection_id"
        elif action.target_type == "vpc_endpoint":
            target_attr = "vpc_endpoint_id"

        if action.provider == "aws":
            return f"""resource "aws_route" "remediation_{action.route_table_id}" {{
  route_table_id         = "{action.route_table_id}"
  destination_cidr_block = "{action.destination_cidr}"
  {target_attr}             = "{action.target_id}"
}}"""
        else:
            return f"""resource "google_compute_route" "remediation_{action.route_table_id}" {{
  name             = "remediation-route-{action.route_table_id}"
  dest_range       = "{action.destination_cidr}"
  network          = "{action.route_table_id}"
  next_hop_gateway = "{action.target_id}"
}}"""
