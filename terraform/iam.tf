locals {
  cloudbuild_sa = "serviceAccount:${google_project.this.number}@cloudbuild.gserviceaccount.com"
}

resource "google_service_account" "run_jobs" {
  project      = local.project
  account_id   = "cloud-run-jobs"
  display_name = "Runtime SA for dbt/ingest Cloud Run Jobs"

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_secret_manager_secret_iam_member" "run_jobs_db_secrets" {
  for_each = google_secret_manager_secret.db

  project   = local.project
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_jobs.email}"
}

resource "google_secret_manager_secret_iam_member" "run_jobs_ingest_secrets" {
  for_each = google_secret_manager_secret.ingest

  project   = local.project
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_jobs.email}"
}

# Cloud Build needs to push images and deploy/update the Cloud Run Jobs it built.
resource "google_project_iam_member" "cloudbuild_artifact_writer" {
  project = local.project
  role    = "roles/artifactregistry.writer"
  member  = local.cloudbuild_sa

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_project_iam_member" "cloudbuild_run_developer" {
  project = local.project
  role    = "roles/run.developer"
  member  = local.cloudbuild_sa

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_service_account_iam_member" "cloudbuild_act_as_run_jobs" {
  service_account_id = google_service_account.run_jobs.name
  role                = "roles/iam.serviceAccountUser"
  member              = local.cloudbuild_sa
}
