resource "google_sql_database_instance" "postgres" {
  name                = "${var.name}-postgres"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.database_tier
    availability_type = var.deletion_protection ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
    }
  }
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_database" "app" {
  name     = "emergencypulse"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = "emergencypulse"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.name}-database-url"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = format(
    "postgresql+asyncpg://%s:%s@/%s?host=/cloudsql/%s",
    google_sql_user.app.name,
    urlencode(random_password.db_password.result),
    google_sql_database.app.name,
    google_sql_database_instance.postgres.connection_name
  )
}
