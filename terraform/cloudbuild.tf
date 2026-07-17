# All triggers in this config (dbt/ingest/analysis here, plus website.tf and
# services.tf) are 1st-gen `github {}` triggers: manually running a 2nd-gen
# repository_event_config trigger (RunBuildTrigger) is pre-GA and fails with
# an opaque PERMISSION_DENIED despite correct IAM, while 1st-gen manual runs
# are GA. Each repo needs a one-time connection via the legacy Cloud Build
# GitHub App (Console → Cloud Build → Triggers → Connect repository → GitHub
# (Cloud Build GitHub App)) before its trigger can be created. 1st-gen GitHub
# triggers live in the global location, so `location` is omitted throughout.
#
# The separate 2nd-gen `gcloud builds connections create github ...`
# connection (see bootstrap.sh and var.github_connection_name) predates this
# and is no longer read by any resource here — nothing currently needs it,
# but it's harmless to leave in place if you want 2nd-gen repository
# resources again later.

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

  filename        = "terraform/cloudbuild-dbt.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = google_artifact_registry_repository.images.repository_id
    _JOB_NAME   = google_cloud_run_v2_job.dbt.name
  }

  included_files = ["dbt/**", "terraform/cloudbuild-dbt.yaml", "pyproject.toml", "uv.lock"]
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

  filename        = "terraform/cloudbuild-ingest.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = google_artifact_registry_repository.images.repository_id
    _JOB_NAME   = google_cloud_run_v2_job.ingest.name
  }

  included_files = ["ingest/**", "terraform/cloudbuild-ingest.yaml", "pyproject.toml", "uv.lock"]
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

  filename        = "terraform/cloudbuild-analysis.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION       = var.region
    _REPOSITORY   = google_artifact_registry_repository.images.repository_id
    _SERVICE_NAME = google_cloud_run_v2_service.analysis.name
  }

  # analysis/ imports ingest/src/db directly, so a change to either subfolder
  # (or the shared root pyproject.toml/uv.lock) needs to rebuild this image.
  included_files = ["analysis/**", "ingest/**", "terraform/cloudbuild-analysis.yaml", "pyproject.toml", "uv.lock"]
}
