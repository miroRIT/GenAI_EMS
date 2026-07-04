variable "project_id" {
  type        = string
  description = "GCP project id."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP region."
}

variable "artifact_repository" {
  type        = string
  default     = "emergencypulse"
  description = "Artifact Registry repository id."
}

variable "image_tag" {
  type        = string
  default     = "staging"
  description = "Container image tag."
}

variable "database_tier" {
  type    = string
  default = "db-custom-2-7680"
}
