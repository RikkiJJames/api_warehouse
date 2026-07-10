# --- GitHub connection -------------------------------------------------------
# Created out-of-band (one-time, interactive — gcloud drives the GitHub App
# install + OAuth via Google's own OAuth client, no PAT needed):
#   gcloud builds connections create github ${var.github_connection_name} \
#     --region=${var.region} --project=${var.project_id}
# The google provider has no data source for this resource type, so we build
# its resource path directly instead of referencing/managing it in Terraform.
# Still used by services.tf; the api_warehouse triggers below moved to 1st-gen.
locals {
  github_connection_path = "projects/${local.project}/locations/${var.region}/connections/${var.github_connection_name}"
}

# The api_warehouse triggers use 1st-gen `github {}` triggers rather than the
# 2nd-gen connection above: manually running 2nd-gen repository triggers
# (RunBuildTrigger) is pre-GA and was failing with an opaque
# PERMISSION_DENIED despite correct IAM, while 1st-gen manual runs are GA.
# 1st-gen needs the repo connected once via the legacy Cloud Build GitHub App
# (Console → Cloud Build → Triggers → Connect repository → GitHub (Cloud
# Build GitHub App)) before these triggers can be created. 1st-gen GitHub
# triggers live in the global location, so `location` is omitted.

resource "google_cloudbuild_trigger" "dbt" {
  project = local.project
  name    = "api-warehouse-dbt"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = var.branch_pattern
    }
  }

  filename        = "cloudbuild-dbt.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = google_artifact_registry_repository.images.repository_id
    _JOB_NAME   = google_cloud_run_v2_job.dbt.name
  }

  included_files = ["dbt/**", "cloudbuild-dbt.yaml", "pyproject.toml", "uv.lock"]
}

resource "google_cloudbuild_trigger" "ingest" {
  project = local.project
  name    = "api-warehouse-ingest"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = var.branch_pattern
    }
  }

  filename        = "cloudbuild-ingest.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = google_artifact_registry_repository.images.repository_id
    _JOB_NAME   = google_cloud_run_v2_job.ingest.name
  }

  included_files = ["ingest/**", "cloudbuild-ingest.yaml", "pyproject.toml", "uv.lock"]
}

resource "google_cloudbuild_trigger" "analysis" {
  project = local.project
  name    = "api-warehouse-analysis"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = var.branch_pattern
    }
  }

  filename        = "cloudbuild-analysis.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION       = var.region
    _REPOSITORY   = google_artifact_registry_repository.images.repository_id
    _SERVICE_NAME = google_cloud_run_v2_service.analysis.name
  }

  # analysis/ imports ingest/src/db directly, so a change to either subfolder
  # (or the shared root pyproject.toml/uv.lock) needs to rebuild this image.
  included_files = ["analysis/**", "ingest/**", "cloudbuild-analysis.yaml", "pyproject.toml", "uv.lock"]
}
