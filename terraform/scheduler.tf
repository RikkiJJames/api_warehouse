resource "google_service_account" "ingest_dbt_scheduler" {
  project      = local.project
  account_id   = "ingest-dbt-scheduler"
  display_name = "Triggers the hourly ingest-then-dbt Workflow execution"

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_project_iam_member" "scheduler_workflows_invoker" {
  project = local.project
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${google_service_account.ingest_dbt_scheduler.email}"
}

resource "google_cloud_scheduler_job" "ingest_then_dbt_hourly" {
  project     = local.project
  region      = var.region
  name        = "ingest-then-dbt-hourly"
  description = "Hourly trigger for the ingest-then-dbt Workflow"
  schedule    = var.ingest_dbt_schedule
  time_zone   = var.ingest_dbt_schedule_timezone

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/${google_workflows_workflow.ingest_then_dbt.id}/executions"
    headers     = { "Content-Type" = "application/json" }
    body        = base64encode("{}")

    oauth_token {
      service_account_email = google_service_account.ingest_dbt_scheduler.email
    }
  }

  depends_on = [time_sleep.wait_for_apis]
}
