# Note: This is a high-level scaffolding for AWS-GCP VPN Peering.
# It requires existing AWS Transit Gateway and GCP HA VPN Gateway.

# --- AWS Side: Customer Gateway (representing GCP) ---
resource "aws_customer_gateway" "gcp" {
  bgp_asn    = var.gcp_asn
  ip_address = var.gcp_vpn_ip
  type       = "ipsec.1"
  tags       = { Name = "nit-fabric-gcp-cgw" }
}

resource "aws_vpn_connection" "to_gcp" {
  customer_gateway_id = aws_customer_gateway.gcp.id
  transit_gateway_id  = var.aws_tgw_id
  type                = "ipsec.1"
  static_routes_only  = false
  tags                = { Name = "nit-fabric-to-gcp" }
}

# --- GCP Side: External VPN Gateway (representing AWS) ---
resource "google_compute_external_vpn_gateway" "aws" {
  name            = "nit-fabric-aws-gateway"
  redundancy_type = "SINGLE_IP_INTERNALLY_REDUNDANT"
  interface {
    id         = 0
    ip_address = aws_vpn_connection.to_gcp.tunnel1_address
  }
}

resource "google_compute_vpn_tunnel" "to_aws" {
  name                            = "nit-fabric-to-aws-tunnel"
  vpn_gateway                     = var.gcp_vpn_gateway_id
  peer_external_gateway           = google_compute_external_vpn_gateway.aws.self_link
  peer_external_gateway_interface = 0
  shared_secret                   = aws_vpn_connection.to_gcp.tunnel1_preshared_key
  router                          = var.gcp_router_id
  ike_version                     = 2
}

variable "gcp_asn" { type = number }
variable "gcp_vpn_ip" { type = string }
variable "aws_tgw_id" { type = string }
variable "gcp_vpn_gateway_id" { type = string }
variable "gcp_router_id" { type = string }
