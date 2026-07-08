# --- GitHub connection -------------------------------------------------------
# Created out-of-band (one-time, interactive — gcloud drives the GitHub App
# install + OAuth via Google's own OAuth client, no PAT needed):
#   gcloud builds connections create github ${var.github_connection_name} \
#     --region=${var.region} --project=${var.project_id}
# The google provider has no data source for this resource type, so we build
# its resource path directly instead of referencing/managing it in Terraform.
locals {
  github_connection_path = "projects/${local.project}/locations/${var.region}/connections/${var.github_connection_name}"
}

resource "google_cloudbuildv2_repository" "api_warehouse" {
  project           = local.project
  location          = var.region
  name              = var.github_repo
  parent_connection = local.github_connection_path
  remote_uri        = "https://github.com/${var.github_owner}/${var.github_repo}.git"

  depends_on = [google_project_service.apis]
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
