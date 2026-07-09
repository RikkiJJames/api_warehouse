# Terraform only creates the job skeleton with a placeholder image. Cloud Build
# (see cloudbuild.tf) owns the real image after the first push via
# `gcloud run jobs update --image=...`, so `template` is excluded from drift
# detection below.
resource "google_cloud_run_v2_job" "dbt" {
  project  = local.project
  name     = "api-warehouse-dbt"
  location = var.region

  deletion_protection = var.job_deletion_protection

  template {
    template {
      service_account = google_service_account.run_jobs.email

      containers {
        image = "us-docker.pkg.dev/cloudrun/container/job:latest"

        dynamic "env" {
          for_each = google_secret_manager_secret.db
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value.secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers]
  }

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_service_account" "run_analysis" {
  project      = local.project
  account_id   = "cloud-run-analysis"
  display_name = "Runtime SA for the marimo analysis dashboard Cloud Run service"

  depends_on = [time_sleep.wait_for_apis]
}

# A Service, not a Job, like dbt/ingest above — marimo serves a long-running
# interactive dashboard rather than running once to completion.
resource "google_cloud_run_v2_service" "analysis" {
  project  = local.project
  name     = "api-warehouse-analysis"
  location = var.region

  deletion_protection = var.job_deletion_protection

  template {
    service_account = google_service_account.run_analysis.email

    containers {
      # Placeholder — Cloud Build owns the real image after the first push
      # via `gcloud run services update --image=...`.
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      dynamic "env" {
        for_each = google_secret_manager_secret.db
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers]
  }

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_cloud_run_v2_job" "ingest" {
  project  = local.project
  name     = "api-warehouse-ingest"
  location = var.region

  deletion_protection = var.job_deletion_protection

  template {
    template {
      service_account = google_service_account.run_jobs.email

      containers {
        image = "us-docker.pkg.dev/cloudrun/container/job:latest"

        dynamic "env" {
          for_each = merge(google_secret_manager_secret.db, google_secret_manager_secret.ingest)
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value.secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers]
  }

  depends_on = [time_sleep.wait_for_apis]
}
