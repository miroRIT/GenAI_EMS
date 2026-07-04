terraform {
  required_version = ">= 1.7.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.35"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  name = "emergencypulse-staging"
}

module "network" {
  source = "../../modules/network"
  name   = local.name
  region = var.region
}

module "database" {
  source              = "../../modules/database"
  name                = local.name
  region              = var.region
  network_id          = module.network.network_id
  database_tier       = var.database_tier
  deletion_protection = true
  depends_on          = [module.network]
}

module "compute" {
  source                       = "../../modules/compute"
  name                         = "${local.name}-api"
  project_id                   = var.project_id
  region                       = var.region
  image                        = var.image
  environment                  = "staging"
  database_url_secret_resource = module.database.database_url_secret_resource
  cloud_sql_connection_name    = module.database.instance_connection_name
  min_instances                = 1
  max_instances                = 20
}
