variable "project_id" {
  type        = string
  description = "GCP project id."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP region."
}

variable "image" {
  type        = string
  description = "Container image URI."
}

variable "database_tier" {
  type    = string
  default = "db-f1-micro"
}
