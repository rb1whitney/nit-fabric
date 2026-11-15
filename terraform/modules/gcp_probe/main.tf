terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

resource "google_cloud_run_v2_service" "probe" {
  name     = "nit-fabric-probe"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  labels   = { "nit-fabric-type" = "probe" }

  template {
    containers {
      image = var.image_url
      ports {
        container_port = 8080
      }
    }
    vpc_access {
      connector = var.vpc_connector_id
      egress    = "ALL_TRAFFIC"
    }
  }
}

# Removed public IAM binding. 
# Explicitly authorize specific service accounts or IAM identities instead.

variable "region" { type = string }
variable "image_url" { type = string }
variable "vpc_connector_id" { type = string }

output "url" {
  value = google_cloud_run_v2_service.probe.uri
}
