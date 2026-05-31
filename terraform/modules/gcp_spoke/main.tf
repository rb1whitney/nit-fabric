terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

resource "google_compute_network" "main" {
  name                    = "nit-fabric-gcp-spoke"
  auto_create_subnetworks = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_compute_subnetwork" "primary" {
  # checkov:skip=CKV_GCP_76: Private Google Access for IPv6 is configured but the pipeline's Checkov version fails to parse the string value.
  name                       = "nit-fabric-spoke-primary"
  ip_cidr_range              = var.subnet_cidr
  region                     = var.region
  network                    = google_compute_network.main.id
  private_ip_google_access   = true
  private_ipv6_google_access = "ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE"

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_router" "hub_router" {
  name    = "nit-fabric-router"
  network = google_compute_network.main.name
  bgp {
    asn = var.asn
  }
}

resource "google_compute_vpn_gateway" "hub_vpn" {
  name    = "nit-fabric-ha-vpn"
  network = google_compute_network.main.name
}

variable "subnet_cidr" { type = string }
variable "region" { type = string }
variable "asn" { type = number }
