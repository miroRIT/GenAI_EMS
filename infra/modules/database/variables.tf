variable "name" {
  type        = string
  description = "Cloud SQL instance name prefix."
}

variable "region" {
  type        = string
  description = "GCP region."
}

variable "network_id" {
  type        = string
  description = "VPC network id for private Cloud SQL."
}

variable "database_tier" {
  type        = string
  description = "Cloud SQL machine tier."
}

variable "deletion_protection" {
  type        = bool
  default     = true
}
