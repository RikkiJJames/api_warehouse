resource "google_service_account" "cloudbuild_trigger" {
  project      = local.project
  account_id   = "cloudbuild-trigger"
  display_name = "SA Cloud Build trigger runs as"

  depends_on = [time_sleep.wait_for_apis]
}

locals {
  # Newly-created projects no longer get the legacy default Cloud Build SA
  # (PROJECT_NUMBER@cloudbuild.gserviceaccount.com) auto-provisioned as a
  # usable build identity, so every trigger below runs as our own
  # user-managed SA instead — this is also Google's currently recommended
  # approach (BYOSA), not just a workaround.
  cloudbuild_sa_email = google_service_account.cloudbuild_trigger.email
  cloudbuild_sa       = "serviceAccount:${local.cloudbuild_sa_email}"
  # Repository-based (2nd-gen) triggers require an explicit service_account —
  # the implicit default-SA behavior only applies to legacy 1st-gen GitHub
  # triggers, and omitting it fails trigger creation with a generic 400.
  cloudbuild_sa_resource_name = "projects/${local.project}/serviceAccounts/${local.cloudbuild_sa_email}"
  # Distinct from cloudbuild_sa above: this is Cloud Build's 2nd-gen "P4SA",
  # which `gcloud builds connections create` needs Secret Manager admin
  # rights for — it creates/manages its own internal secret to hold the
  # GitHub App credentials behind the connection.
  cloudbuild_p4sa = "serviceAccount:service-${google_project.this.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_p4sa_secretmanager_admin" {
  project = local.project
  role    = "roles/secretmanager.admin"
  member  = local.cloudbuild_p4sa

  depends_on = [time_sleep.wait_for_apis]
}

# The legacy Cloud Build SA (PROJECT_NUMBER@cloudbuild.gserviceaccount.com).
# New projects don't provision it, but RunBuildTrigger (manual "Run" via
# gcloud/console) still creates the build through it internally — even for
# BYOSA triggers — so without it every manual run fails with an opaque
# "Permission 'cloudbuild.builds.create' denied on projects/<hex>" while the
# caller's own IAM check passes and push-triggered builds work fine. This
# resource provisions the identity; the builder grant below makes it usable.
resource "google_project_service_identity" "cloudbuild" {
  provider = google-beta
  project  = local.project
  service  = "cloudbuild.googleapis.com"

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_project_iam_member" "cloudbuild_legacy_sa_builder" {
  project = local.project
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${google_project_service_identity.cloudbuild.email}"
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

resource "google_secret_manager_secret_iam_member" "run_analysis_db_secrets" {
  for_each = google_secret_manager_secret.db

  project   = local.project
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_analysis.email}"
}

# Needed by the Cloud SQL Auth Proxy sidecar (cloudrun.tf) running under each
# identity to open an authenticated tunnel to the instance.
resource "google_project_iam_member" "run_jobs_cloudsql_client" {
  project = local.project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run_jobs.email}"
}

resource "google_project_iam_member" "run_analysis_cloudsql_client" {
  project = local.project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run_analysis.email}"
}

resource "google_service_account_iam_member" "cloudbuild_act_as_run_analysis" {
  service_account_id = google_service_account.run_analysis.name
  role               = "roles/iam.serviceAccountUser"
  member             = local.cloudbuild_sa
}

# Public per explicit choice — this is a personal read-only dashboard (no
# write endpoints), so it's exposed without an IAM/token gate in front of it.
resource "google_cloud_run_v2_service_iam_member" "analysis_public" {
  project  = local.project
  location = var.region
  name     = google_cloud_run_v2_service.analysis.name
  role     = "roles/run.invoker"
  member   = "allUsers"
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
  role               = "roles/iam.serviceAccountUser"
  member             = local.cloudbuild_sa
}

# When a trigger's service_account is set explicitly (required for 2nd-gen
# repository triggers), Cloud Build no longer auto-grants these — they're
# otherwise implicit for the legacy default-SA behavior.
resource "google_project_iam_member" "cloudbuild_builder" {
  project = local.project
  role    = "roles/cloudbuild.builds.builder"
  member  = local.cloudbuild_sa

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_project_iam_member" "cloudbuild_log_writer" {
  project = local.project
  role    = "roles/logging.logWriter"
  member  = local.cloudbuild_sa

  depends_on = [time_sleep.wait_for_apis]
}

# Lets var.operator_email manually run/retry triggers via `gcloud builds
# triggers run` or the console "Run" button — distinct from the cloudbuild_sa
# grants above, which govern what the *build itself* can do once running.
resource "google_project_iam_member" "operator_cloudbuild_editor" {
  project = local.project
  role    = "roles/cloudbuild.builds.editor"
  member  = "user:${var.operator_email}"

  depends_on = [time_sleep.wait_for_apis]
}

# builds.editor alone isn't enough to manually run a trigger that has an
# explicit service_account (as all 2nd-gen repository triggers must): the
# caller also needs iam.serviceAccounts.actAs on that SA, or the run is
# rejected with PERMISSION_DENIED. Push-triggered builds are unaffected.
resource "google_service_account_iam_member" "operator_act_as_cloudbuild_sa" {
  service_account_id = google_service_account.cloudbuild_trigger.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:${var.operator_email}"
}

# Lets var.operator_email log into the Cloud SQL instance directly (e.g. via
# `gcloud sql connect`) using their Google identity — see
# google_sql_user.operator in cloudsql.tf for the matching DB-side IAM user.
resource "google_project_iam_member" "operator_cloudsql_client" {
  project = local.project
  role    = "roles/cloudsql.client"
  member  = "user:${var.operator_email}"

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_project_iam_member" "operator_cloudsql_instance_user" {
  project = local.project
  role    = "roles/cloudsql.instanceUser"
  member  = "user:${var.operator_email}"

  depends_on = [time_sleep.wait_for_apis]
}
