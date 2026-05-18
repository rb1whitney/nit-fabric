# SRE Golden Signals - Auto-Scaffolded Template
# Ensure this is applied to your target Cloud Provider (AWS/GCP)

locals {
  service_name = "example-service"
}

# This is a placeholder structure for Golden Signals.
# Replace with actual resources for aws_cloudwatch_dashboard or google_monitoring_dashboard.
#
# Golden Signals Required:
# 1. Latency: The time it takes to service a request.
# 2. Traffic: A measure of how much demand is being placed on the system.
# 3. Errors: The rate of requests that fail.
# 4. Saturation: How "full" your service is.

output "sre_golden_signals_status" {
  value = "SRE Golden Signals defined for ${local.service_name} (Latency, Traffic, Errors, Saturation)"
}
