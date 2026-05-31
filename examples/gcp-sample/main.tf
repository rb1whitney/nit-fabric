terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = "nit-fabric-sample-project"
  region  = "us-central1"
}

resource "google_compute_network" "main" {
  name                    = "nit-fabric-sample-vpc"
  auto_create_subnetworks = false
}

# VIOLATION: Subnet without Private Google Access
resource "google_compute_subnetwork" "insecure" {
  name                     = "insecure-subnet"
  ip_cidr_range            = "10.1.0.0/24"
  network                  = google_compute_network.main.id
  private_ip_google_access = false
}

# VIOLATION: GCE Instance with External IP
resource "google_compute_instance" "insecure" {
  name         = "insecure-instance"
  machine_type = "n1-standard-1"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network    = google_compute_network.main.id
    subnetwork = google_compute_subnetwork.insecure.id
    access_config {
      # Presence of this block assigns an external IP
    }
  }
}

# VIOLATION: Firewall Rule allowing 0.0.0.0/0 on Port 22
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh-insecure"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# VIOLATION: GKE Cluster without Workload Identity
resource "google_container_cluster" "legacy" {
  name     = "legacy-cluster"
  location = "us-central1"

  # Missing workload_identity_config
  remove_default_node_pool = true
  initial_node_count       = 1
}

# VIOLATION: Cloud SQL with Public IP
resource "google_sql_database_instance" "public" {
  name             = "public-db"
  database_version = "POSTGRES_13"
  region           = "us-central1"

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true # This enables public IP
    }
  }
}
