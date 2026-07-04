output "service_uri" {
  value = google_cloud_run_v2_service.api.uri
}

output "runtime_service_account" {
  value = google_service_account.runtime.email
}
