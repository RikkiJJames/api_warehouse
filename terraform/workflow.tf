# Orchestrates the hourly refresh: run the ingest Cloud Run Job, then the dbt
# Cloud Run Job once ingest has actually finished. Cloud Run Jobs' `run` API
# surfaces as a long-running operation that only completes when the job
# execution itself reaches a terminal state (not merely when it starts), and
# Workflows connectors block on that automatically — so no manual polling
# loop is needed, and a failed ingest run raises here, which stops the
# workflow before dbt runs on stale/incomplete data.
resource "google_service_account" "ingest_dbt_workflow" {
  project      = local.project
  account_id   = "ingest-dbt-workflow"
  display_name = "Runs ingest -> dbt Cloud Run Jobs from the Workflow"

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_project_iam_member" "workflow_run_developer" {
  project = local.project
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.ingest_dbt_workflow.email}"
}

# The Cloud Run Jobs execute using their own runtime SA (run_jobs) — whatever
# triggers .run() on them must be allowed to act as that SA.
resource "google_service_account_iam_member" "workflow_act_as_run_jobs" {
  service_account_id = google_service_account.run_jobs.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.ingest_dbt_workflow.email}"
}

resource "google_workflows_workflow" "ingest_then_dbt" {
  project         = local.project
  region          = var.region
  name            = "ingest-then-dbt"
  description     = "Runs the ingest Cloud Run Job, then the dbt Cloud Run Job once ingest completes"
  service_account = google_service_account.ingest_dbt_workflow.id

  source_contents = <<-EOT
    main:
      steps:
        - runIngest:
            call: googleapis.run.v2.projects.locations.jobs.run
            args:
              name: projects/${local.project}/locations/${var.region}/jobs/${google_cloud_run_v2_job.ingest.name}
            result: ingestExecution
        - runDbt:
            call: googleapis.run.v2.projects.locations.jobs.run
            args:
              name: projects/${local.project}/locations/${var.region}/jobs/${google_cloud_run_v2_job.dbt.name}
            result: dbtExecution
        - done:
            return:
              ingest: $${ingestExecution}
              dbt: $${dbtExecution}
  EOT

  depends_on = [time_sleep.wait_for_apis]
}
