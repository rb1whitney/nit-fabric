# nit-fabric | Modular Industrial Hub
# Status: [GOLD STANDARD] | Structure: [MODULAR]

module "aws_hub" {
  source   = "./modules/aws_hub"
  vpc_cidr = var.vpc_cidr_aws
  asn      = 64512
}

module "gcp_spoke" {
  source      = "./modules/gcp_spoke"
  asn         = var.gcp_asn
  region      = var.gcp_region_secondary
  subnet_cidr = var.vpc_cidr_gcp
}
