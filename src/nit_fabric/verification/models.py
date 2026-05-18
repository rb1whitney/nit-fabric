from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class BaseAction(BaseModel):
    """Base class for all verifiable remediation actions."""
    provider: Literal["aws", "gcp"]
    resource_type: str

class FirewallAction(BaseAction):
    """Type-safe schema representing a Google Cloud firewall rule change."""
    provider: Literal["aws", "gcp"] = "gcp"
    resource_type: str = "google_compute_firewall"
    name: str
    network: str
    action: Literal["allow", "deny"]
    direction: Literal["INGRESS", "EGRESS"]
    priority: int = Field(default=1000, ge=0, le=65535)
    source_ranges: List[str] = Field(default_factory=list)
    destination_ranges: List[str] = Field(default_factory=list)
    allowed_protocols: List[str] = Field(default_factory=list)
    ports: List[str] = Field(default_factory=list)

class RouteAction(BaseAction):
    """Type-safe schema representing an AWS or GCP route table entry."""
    provider: Literal["aws", "gcp"]
    resource_type: Literal["aws_route", "google_compute_route"]
    route_table_id: str
    destination_cidr: str
    target_type: Literal["internet_gateway", "nat_gateway", "transit_gateway", "vpc_peering", "vpc_endpoint"]
    target_id: str

class SecurityGroupAction(BaseAction):
    """Type-safe schema representing an AWS security group rule."""
    provider: Literal["aws", "gcp"] = "aws"
    resource_type: str = "aws_security_group_rule"
    security_group_id: str
    rule_type: Literal["ingress", "egress"]
    from_port: int = Field(ge=0, le=65535)
    to_port: int = Field(ge=0, le=65535)
    protocol: Literal["tcp", "udp", "icmp", "-1"]
    cidr_blocks: List[str] = Field(default_factory=list)
