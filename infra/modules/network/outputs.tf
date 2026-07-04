output "network_id" {
  value = google_compute_network.main.id
}

output "subnet_id" {
  value = google_compute_subnetwork.main.id
}

output "private_service_connection" {
  value = google_service_networking_connection.private_vpc_connection.id
}
