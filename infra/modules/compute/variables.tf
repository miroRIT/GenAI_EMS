variable "name" {
  type        = string
  description = "Cloud Run service name."
}

variable "project_id" {
  type        = string
  description = "GCP project id."
}

variable "region" {
  type        = string
  description = "GCP region."
}

variable "image" {
  type        = string
  description = "Container image."
}

variable "environment" {
  type        = string
  description = "Runtime environment name."
}

variable "database_url_secret_resource" {
  type        = string
  description = "Secret Manager resource id containing DATABASE_URL."
}

variable "database_url_secret_id" {
  type        = string
  description = "Secret Manager secret id containing DATABASE_URL."
}

variable "jwt_secret_resource" {
  type        = string
  description = "Secret Manager resource id containing JWT_SECRET."
}

variable "jwt_secret_id" {
  type        = string
  description = "Secret Manager secret id containing JWT_SECRET."
}

variable "admin_password_hash_secret_resource" {
  type        = string
  description = "Secret Manager resource id containing ADMIN_PASSWORD_HASH."
}

variable "admin_password_hash_secret_id" {
  type        = string
  description = "Secret Manager secret id containing ADMIN_PASSWORD_HASH."
}

variable "cloud_sql_connection_name" {
  type        = string
  description = "Cloud SQL connection name."
}

variable "min_instances" {
  type    = number
  default = 1
}

variable "max_instances" {
  type    = number
  default = 20
}
