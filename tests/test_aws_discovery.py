import sys
from unittest.mock import MagicMock

# Mock boto3 and botocore before importing anything else to bypass missing package errors
boto3_mock = MagicMock()
sys.modules['boto3'] = boto3_mock
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.exceptions'] = MagicMock()

import unittest
from unittest.mock import patch
import os

# Adjust path to import nit_fabric modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from nit_fabric.aws_discoverer import AWSDiscoverer

class TestAWSDiscovery(unittest.TestCase):
    def setUp(self):
        self.mock_ec2 = MagicMock()
        self.mock_dx = MagicMock()
        
        def client_side_effect(service_name, *args, **kwargs):
            if service_name == "ec2":
                return self.mock_ec2
            elif service_name == "directconnect":
                return self.mock_dx
            return MagicMock()
            
        boto3_mock.client.side_effect = client_side_effect
        boto3_mock.client.return_value = self.mock_ec2 # default fallback

    def tearDown(self):
        pass

    def test_tag_based_filtering(self):
        """Verify only resources with nit-fabric:managed=true tag are processed."""
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{
            "Vpcs": [
                {
                    "VpcId": "vpc-managed",
                    "CidrBlock": "10.0.0.0/16",
                    "Tags": [{"Key": "nit-fabric:managed", "Value": "true"}]
                },
                {
                    "VpcId": "vpc-unmanaged",
                    "CidrBlock": "192.168.0.0/16",
                    "Tags": [{"Key": "nit-fabric:managed", "Value": "false"}]
                },
                {
                    "VpcId": "vpc-notag",
                    "CidrBlock": "172.16.0.0/16"
                }
            ]
        }]
        self.mock_ec2.get_paginator.return_value = mock_paginator
        
        discoverer = AWSDiscoverer()
        vpcs = discoverer.get_vpcs()
        self.assertEqual(len(vpcs), 1)
        self.assertEqual(vpcs[0]["VpcId"], "vpc-managed")

    def test_discover_transit_gateways(self):
        """Verify Transit Gateway attachments and propagations are resolved."""
        mock_tgw_paginator = MagicMock()
        mock_tgw_paginator.paginate.return_value = [{
            "TransitGateways": [
                {
                    "TransitGatewayId": "tgw-001",
                    "State": "available",
                    "Tags": [{"Key": "nit-fabric:managed", "Value": "true"}]
                }
            ]
        }]
        
        mock_attach_paginator = MagicMock()
        mock_attach_paginator.paginate.return_value = [{
            "TransitGatewayVpcAttachments": [
                {
                    "TransitGatewayAttachmentId": "tgw-attach-001",
                    "TransitGatewayId": "tgw-001",
                    "VpcId": "vpc-001",
                    "SubnetIds": ["subnet-001"]
                }
            ]
        }]

        def paginator_side_effect(service_operation, *args, **kwargs):
            if service_operation == "describe-transit-gateways":
                return mock_tgw_paginator
            elif service_operation == "describe-transit-gateway-vpc-attachments":
                return mock_attach_paginator
            return MagicMock()

        self.mock_ec2.get_paginator.side_effect = paginator_side_effect
        
        discoverer = AWSDiscoverer()
        tgws = discoverer.get_transit_gateways()
        self.assertEqual(len(tgws), 1)
        self.assertEqual(tgws[0]["id"], "tgw-001")
        self.assertEqual(len(tgws[0]["attachments"]), 1)
        self.assertEqual(tgws[0]["attachments"][0]["vpc_id"], "vpc-001")

    def test_discover_direct_connect(self):
        """Verify Direct Connect Gateways and associations are retrieved."""
        self.mock_dx.confirm_connection.return_value = {} # DX mock
        self.mock_dx.describe_direct_connect_gateways.return_value = {
            "directConnectGateways": [
                {
                    "directConnectGatewayId": "dxgw-001",
                    "directConnectGatewayName": "prod-dxgw"
                }
            ]
        }
        self.mock_dx.describe_direct_connect_gateway_associations.return_value = {
            "directConnectGatewayAssociations": [
                {
                    "directConnectGatewayId": "dxgw-001",
                    "associatedGatewayId": "tgw-001",
                    "associationState": "associated"
                }
            ]
        }
        
        discoverer = AWSDiscoverer()
        dxgws = discoverer.get_direct_connect_gateways()
        self.assertEqual(len(dxgws), 1)
        self.assertEqual(dxgws[0]["id"], "dxgw-001")
        self.assertEqual(dxgws[0]["associations"][0]["associated_gateway_id"], "tgw-001")

if __name__ == "__main__":
    unittest.main()
