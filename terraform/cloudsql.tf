# Replaces Neon: a single-zone Postgres instance sized for a low-traffic
# hourly ingest/dbt warehouse. Cloud Run reaches it via a Cloud SQL Auth Proxy
# sidecar (see cloudrun.tf) rather than a VPC connector, so no networking
# resources are needed here beyond the instance itself.
resource "google_sql_database_instance" "main" {
  project          = local.project
  name             = "api-warehouse-db"
  region           = var.region
  database_version = "POSTGRES_16"

  deletion_protection = var.db_deletion_protection

  settings {
    tier              = var.db_instance_tier
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"
    disk_autoresize   = false

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = false
    }

    ip_configuration {
      ipv4_enabled = true
      # No authorized_networks: Cloud Run has no stable egress IP to
      # allowlist. The Cloud SQL Auth Proxy sidecar authenticates via IAM
      # instead, over an encrypted tunnel, so public IP stays otherwise closed.
    }
  }

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_sql_database" "warehouse" {
  project  = local.project
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

# special=false: the app builds its Postgres DSN with naive string
# interpolation (no URL-encoding), so the password must avoid characters
# like @ : / ? that would break DSN parsing.
resource "random_password" "db_user" {
  length  = 24
  special = false
}

resource "google_sql_user" "app" {
  project  = local.project
  name     = "app"
  instance = google_sql_database_instance.main.name
  password = random_password.db_user.result
}
