# Secret *containers* only — no values are set here. Populate real values out-of-band, e.g.:
#   gcloud secrets versions add DB_PASSWORD --project=<project_id> --data-file=-
resource "google_secret_manager_secret" "db" {
  for_each = toset(var.db_secret_names)

  project   = local.project
  secret_id = each.key

  replication {
    auto {}
  }

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_secret_manager_secret" "ingest" {
  for_each = toset(var.ingest_secret_names)

  project   = local.project
  secret_id = each.key

  replication {
    auto {}
  }

  depends_on = [time_sleep.wait_for_apis]
}

# Unlike the ingest secrets above (populated out-of-band from third-party
# APIs), these DB values are entirely generated/owned by this Terraform
# config (see cloudsql.tf) and the Cloud SQL Auth Proxy sidecar in
# cloudrun.tf, so Terraform populates them directly instead of requiring a
# manual `gcloud secrets versions add` step.
resource "google_secret_manager_secret_version" "db_host" {
  secret = google_secret_manager_secret.db["DB_HOST"].id
  # The Cloud SQL Auth Proxy sidecar always listens on localhost inside the
  # same Cloud Run container — the app never talks to Cloud SQL directly.
  secret_data = "127.0.0.1"
}

resource "google_secret_manager_secret_version" "db_port" {
  secret      = google_secret_manager_secret.db["DB_PORT"].id
  secret_data = "5432"
}

resource "google_secret_manager_secret_version" "db_name" {
  secret      = google_secret_manager_secret.db["DB_NAME"].id
  secret_data = google_sql_database.warehouse.name
}

resource "google_secret_manager_secret_version" "db_user" {
  secret      = google_secret_manager_secret.db["DB_USER"].id
  secret_data = google_sql_user.app.name
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db["DB_PASSWORD"].id
  secret_data = random_password.db_user.result
}
