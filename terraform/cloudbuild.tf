# --- One-time GitHub App authorization -------------------------------------
# Prerequisite (manual, can't be scripted by Google):
#   1. Install https://github.com/apps/google-cloud-build on this repo/org.
#   2. Create a classic GitHub PAT with `repo` scope, pass it as var.github_token.
# After `terraform apply`, check the connection status:
#   gcloud builds connections describe github-connection --region=<region> --project=<project_id>
# If it shows PENDING_USER_OAUTH, open the actionUri it prints and finish the
# OAuth handshake in the browser once.

resource "google_secret_manager_secret" "github_token" {
  project   = local.project
  secret_id = "github-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "github_token" {
  secret      = google_secret_manager_secret.github_token.id
  secret_data = var.github_token
}

# Cloud Build's 2nd-gen robot SA needs to read the PAT.
resource "google_secret_manager_secret_iam_member" "github_token_accessor" {
  project   = local.project
  secret_id = google_secret_manager_secret.github_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${google_project.this.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

resource "google_cloudbuildv2_connection" "github" {
  project  = local.project
  location = var.region
  name     = "github-connection"

  github_config {
    app_installation_id = var.github_app_installation_id
    authorizer_credential {
      oauth_token_secret_version = google_secret_manager_secret_version.github_token.id
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.github_token_accessor]
}

resource "google_cloudbuildv2_repository" "api_warehouse" {
  project           = local.project
  location          = var.region
  name              = var.github_repo
  parent_connection = google_cloudbuildv2_connection.github.name
  remote_uri        = "https://github.com/${var.github_owner}/${var.github_repo}.git"
}

resource "google_cloudbuild_trigger" "dbt" {
  project  = local.project
  location = var.region
  name     = "api-warehouse-dbt"

  repository_event_config {
    repository = google_cloudbuildv2_repository.api_warehouse.id
    push {
      branch = var.branch_pattern
    }
  }

  filename = "cloudbuild-dbt.yaml"

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = google_artifact_registry_repository.images.repository_id
    _JOB_NAME   = google_cloud_run_v2_job.dbt.name
  }

  included_files = ["dbt/**", "cloudbuild-dbt.yaml", "pyproject.toml", "uv.lock"]
}

resource "google_cloudbuild_trigger" "ingest" {
  project  = local.project
  location = var.region
  name     = "api-warehouse-ingest"

  repository_event_config {
    repository = google_cloudbuildv2_repository.api_warehouse.id
    push {
      branch = var.branch_pattern
    }
  }

  filename = "cloudbuild-ingest.yaml"

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = google_artifact_registry_repository.images.repository_id
    _JOB_NAME   = google_cloud_run_v2_job.ingest.name
  }

  included_files = ["ingest/**", "cloudbuild-ingest.yaml", "pyproject.toml", "uv.lock"]
}
