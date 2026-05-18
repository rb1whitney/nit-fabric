import logging
import sys
from typing import Dict, Any, List

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    # Allow running in mocked/limited envs without crashing on imports
    boto3 = None
    ClientError = Exception

logger = logging.getLogger("nit-fabric.discovery.aws")

class AWSDiscoverer:
    def __init__(self):
        if boto3 is not None:
            try:
                self.ec2 = boto3.client("ec2")
                self.dx = boto3.client("directconnect")
            except Exception as e:
                logger.warning(f"Failed to initialize Boto3 clients: {e}. Live AWS discovery will be unavailable.")
                self.ec2 = None
                self.dx = None
        else:
            logger.warning("boto3 package not installed. Live AWS discovery is disabled.")
            self.ec2 = None
            self.dx = None

    def _is_managed(self, tags: List[Dict[str, str]]) -> bool:
        if not tags:
            return False
        for tag in tags:
            if tag.get("Key") == "nit-fabric:managed" and tag.get("Value") == "true":
                return True
        return False

    def get_vpcs(self) -> List[Dict[str, Any]]:
        if not self.ec2:
            return []
        try:
            paginator = self.ec2.get_paginator("describe-vpcs")
            vpcs = []
            for page in paginator.paginate():
                for vpc in page.get("Vpcs", []):
                    # Filter based on tags
                    if self._is_managed(vpc.get("Tags", [])):
                        vpcs.append(vpc)
            return vpcs
        except ClientError as e:
            logger.error(f"Error describing VPCs: {e}")
            return []

    def get_transit_gateways(self) -> List[Dict[str, Any]]:
        if not self.ec2:
            return []
        try:
            tgws = []
            # TGW paginators
            paginator = self.ec2.get_paginator("describe-transit-gateways")
            for page in paginator.paginate():
                for tgw in page.get("TransitGateways", []):
                    if self._is_managed(tgw.get("Tags", [])):
                        tgw_id = tgw["TransitGatewayId"]
                        
                        # Get attachments
                        attachments = []
                        attach_paginator = self.ec2.get_paginator("describe-transit-gateway-vpc-attachments")
                        for attach_page in attach_paginator.paginate(Filters=[{"Name": "transit-gateway-id", "Values": [tgw_id]}]):
                            for attach in attach_page.get("TransitGatewayVpcAttachments", []):
                                attachments.append({
                                    "attachment_id": attach["TransitGatewayAttachmentId"],
                                    "vpc_id": attach["VpcId"],
                                    "subnet_ids": attach.get("SubnetIds", [])
                                })
                        
                        tgws.append({
                            "id": tgw_id,
                            "state": tgw["State"],
                            "attachments": attachments
                        })
            return tgws
        except ClientError as e:
            logger.error(f"Error describing Transit Gateways: {e}")
            return []

    def get_direct_connect_gateways(self) -> List[Dict[str, Any]]:
        if not self.dx:
            return []
        try:
            dxgws = []
            response = self.dx.describe_direct_connect_gateways()
            for dxgw in response.get("directConnectGateways", []):
                dxgw_id = dxgw["directConnectGatewayId"]
                
                # Fetch associations
                assoc_resp = self.dx.describe_direct_connect_gateway_associations(directConnectGatewayId=dxgw_id)
                associations = []
                for assoc in assoc_resp.get("directConnectGatewayAssociations", []):
                    associations.append({
                        "associated_gateway_id": assoc.get("associatedGatewayId"),
                        "association_state": assoc.get("associationState")
                    })
                
                dxgws.append({
                    "id": dxgw_id,
                    "name": dxgw.get("directConnectGatewayName"),
                    "associations": associations
                })
            return dxgws
        except ClientError as e:
            logger.error(f"Error describing DX Gateways: {e}")
            return []

    def get_route_tables_detailed(self) -> List[Dict[str, Any]]:
        if not self.ec2:
            return []
        try:
            paginator = self.ec2.get_paginator("describe-route-tables")
            route_tables = []
            for page in paginator.paginate():
                for rt in page.get("RouteTables", []):
                    if self._is_managed(rt.get("Tags", [])):
                        associations = []
                        for assoc in rt.get("Associations", []):
                            associations.append({
                                "subnet_id": assoc.get("SubnetId"),
                                "main": assoc.get("Main", False),
                                "route_table_association_id": assoc.get("RouteTableAssociationId")
                            })
                        
                        routes = []
                        for route in rt.get("Routes", []):
                            target = (
                                route.get("GatewayId") or 
                                route.get("TransitGatewayId") or 
                                route.get("VpcPeeringConnectionId") or 
                                route.get("NatGatewayId") or 
                                route.get("NetworkInterfaceId")
                            )
                            routes.append({
                                "destination_cidr": route.get("DestinationCidrBlock"),
                                "target": target,
                                "state": route.get("State"),
                                "origin": route.get("Origin")
                            })
                        
                        route_tables.append({
                            "id": rt["RouteTableId"],
                            "vpc_id": rt["VpcId"],
                            "associations": associations,
                            "routes": routes
                        })
            return route_tables
        except ClientError as e:
            logger.error(f"Error describing Route Tables: {e}")
            return []

    def get_vpc_endpoints_detailed(self) -> List[Dict[str, Any]]:
        if not self.ec2:
            return []
        try:
            paginator = self.ec2.get_paginator("describe-vpc-endpoints")
            endpoints = []
            for page in paginator.paginate():
                for vpce in page.get("VpcEndpoints", []):
                    if self._is_managed(vpce.get("Tags", [])):
                        endpoints.append({
                            "id": vpce["VpcEndpointId"],
                            "vpc_id": vpce["VpcId"],
                            "service_name": vpce["ServiceName"],
                            "type": vpce["VpcEndpointType"],
                            "private_dns_enabled": vpce.get("PrivateDnsEnabled", False)
                        })
            return endpoints
        except ClientError as e:
            logger.error(f"Error describing VPC Endpoints: {e}")
            return []

    def discover_all(self) -> Dict[str, Any]:
        return {
            "vpcs": self.get_vpcs(),
            "transit_gateways": self.get_transit_gateways(),
            "direct_connect_gateways": self.get_direct_connect_gateways(),
            "route_tables": self.get_route_tables_detailed(),
            "vpc_endpoints": self.get_vpc_endpoints_detailed()
        }
