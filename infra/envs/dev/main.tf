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
  name      = "emergencypulse-dev"
  image_uri = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}/api:${var.image_tag}"
}

resource "google_project_service" "required" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "api" {
  repository_id = var.artifact_repository
  location      = var.region
  format        = "DOCKER"
  description   = "EmergencyPulse API container images"

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${local.name}-jwt-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret" "admin_password_hash" {
  secret_id = "${local.name}-admin-password-hash"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

module "network" {
  source = "../../modules/network"
  name   = local.name
  region = var.region

  depends_on = [google_project_service.required]
}

module "database" {
  source              = "../../modules/database"
  name                = local.name
  region              = var.region
  network_id          = module.network.network_id
  database_tier       = var.database_tier
  deletion_protection = false

  depends_on = [module.network]
}

module "compute" {
  source                              = "../../modules/compute"
  name                                = "${local.name}-api"
  project_id                          = var.project_id
  region                              = var.region
  image                               = local.image_uri
  environment                         = "dev"
  database_url_secret_id              = module.database.database_url_secret_id
  database_url_secret_resource        = module.database.database_url_secret_resource
  jwt_secret_id                       = google_secret_manager_secret.jwt_secret.secret_id
  jwt_secret_resource                 = google_secret_manager_secret.jwt_secret.id
  admin_password_hash_secret_id       = google_secret_manager_secret.admin_password_hash.secret_id
  admin_password_hash_secret_resource = google_secret_manager_secret.admin_password_hash.id
  cloud_sql_connection_name           = module.database.instance_connection_name
  min_instances                       = 0
  max_instances                       = 5
}
