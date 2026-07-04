output "api_url" {
  value = module.compute.service_uri
}

output "artifact_repository" {
  value = google_artifact_registry_repository.api.name
}

output "image_uri" {
  value = local.image_uri
}

output "migration_job_name" {
  value = module.compute.migration_job_name
}
