output "instance_connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}

output "database_url_secret_id" {
  value = google_secret_manager_secret.database_url.secret_id
}

output "database_url_secret_resource" {
  value = google_secret_manager_secret.database_url.id
}
