resource "google_artifact_registry_repository" "images" {
  project       = local.project
  location      = var.region
  repository_id = "api-warehouse"
  format        = "DOCKER"
  description   = "Container images for api_warehouse (dbt, ingest, analysis)"

  depends_on = [time_sleep.wait_for_apis]
}
