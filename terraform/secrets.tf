# Secret *containers* only — no values are set here. Populate real values out-of-band, e.g.:
#   gcloud secrets versions add DB_PASSWORD --project=<project_id> --data-file=-
resource "google_secret_manager_secret" "db" {
  for_each = toset(var.db_secret_names)

  project   = local.project
  secret_id = each.key

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "ingest" {
  for_each = toset(var.ingest_secret_names)

  project   = local.project
  secret_id = each.key

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}
