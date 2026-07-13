# Terraform only creates the "app" container with a placeholder image. Cloud
# Build (see cloudbuild.tf) owns the real image after the first push via
# `gcloud run jobs update --image=... --container=app`, so only that
# container's image is excluded from drift detection below. The
# cloudsql-proxy sidecar (giving "app" a local Postgres endpoint at
# 127.0.0.1:5432 backed by google_sql_database_instance.main — see
# cloudsql.tf) stays fully Terraform-managed.
resource "google_cloud_run_v2_job" "dbt" {
  project  = local.project
  name     = "api-warehouse-dbt"
  location = var.region

  deletion_protection = var.job_deletion_protection

  template {
    template {
      service_account = google_service_account.run_jobs.email

      containers {
        name       = "app"
        image      = "us-docker.pkg.dev/cloudrun/container/job:latest"
        depends_on = ["cloudsql-proxy"]

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

      containers {
        name  = "cloudsql-proxy"
        image = "gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.23.0"
        args = [
          "--structured-logs",
          "--port=5432",
          "--health-check",
          "--http-port=8090",
          "--http-address=0.0.0.0",
          google_sql_database_instance.main.connection_name,
        ]

        # tcp_socket on 5432 is unreliable here: the proxy logs "ready" almost
        # immediately, but Cloud Run's own TCP probe against a sidecar's port
        # can still report failure regardless — the dedicated health-check
        # HTTP server (--health-check) is the pattern Google's own docs use
        # for this instead.
        startup_probe {
          http_get {
            path = "/startup"
            port = 8090
          }
          period_seconds    = 1
          failure_threshold = 20
          timeout_seconds   = 1
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image]
  }

  # Cloud Run validates secret access at update time using the runtime SA's
  # grant — waiting on time_sleep.wait_for_secret_iam (not just the grant
  # resource directly) covers both correct ordering and the IAM propagation
  # gap; see the comment on that resource in iam.tf.
  depends_on = [time_sleep.wait_for_apis, time_sleep.wait_for_secret_iam]
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
      # via `gcloud run services update --image=... --container=app`.
      name       = "app"
      image      = "us-docker.pkg.dev/cloudrun/container/hello"
      depends_on = ["cloudsql-proxy"]

      # A multi-container service has no default ingress port — exactly one
      # container must declare it explicitly, and only one may.
      ports {
        container_port = 8080
      }

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

    containers {
      name  = "cloudsql-proxy"
      image = "gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.23.0"
      args = [
        "--structured-logs",
        "--port=5432",
        "--health-check",
        "--http-port=8090",
        "--http-address=0.0.0.0",
        google_sql_database_instance.main.connection_name,
      ]

      # tcp_socket on 5432 is unreliable here: the proxy logs "ready" almost
      # immediately, but Cloud Run's own TCP probe against a sidecar's port
      # can still report failure regardless — the dedicated health-check
      # HTTP server (--health-check) is the pattern Google's own docs use
      # for this instead.
      startup_probe {
        http_get {
          path = "/startup"
          port = 8090
        }
        period_seconds    = 1
        failure_threshold = 20
        timeout_seconds   = 1
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }

  # See the matching comment on google_cloud_run_v2_job.dbt above.
  depends_on = [time_sleep.wait_for_apis, time_sleep.wait_for_secret_iam]
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
        name       = "app"
        image      = "us-docker.pkg.dev/cloudrun/container/job:latest"
        depends_on = ["cloudsql-proxy"]

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

      containers {
        name  = "cloudsql-proxy"
        image = "gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.23.0"
        args = [
          "--structured-logs",
          "--port=5432",
          "--health-check",
          "--http-port=8090",
          "--http-address=0.0.0.0",
          google_sql_database_instance.main.connection_name,
        ]

        # tcp_socket on 5432 is unreliable here: the proxy logs "ready" almost
        # immediately, but Cloud Run's own TCP probe against a sidecar's port
        # can still report failure regardless — the dedicated health-check
        # HTTP server (--health-check) is the pattern Google's own docs use
        # for this instead.
        startup_probe {
          http_get {
            path = "/startup"
            port = 8090
          }
          period_seconds    = 1
          failure_threshold = 20
          timeout_seconds   = 1
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image]
  }

  # See the matching comment on google_cloud_run_v2_job.dbt above.
  depends_on = [time_sleep.wait_for_apis, time_sleep.wait_for_secret_iam]
}
