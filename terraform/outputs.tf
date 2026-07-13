output "project_id" {
  value = google_project.this.project_id
}

output "artifact_registry_repository" {
  value = "${var.region}-docker.pkg.dev/${local.project}/${google_artifact_registry_repository.images.repository_id}"
}

output "cloud_run_jobs" {
  value = {
    dbt    = google_cloud_run_v2_job.dbt.name
    ingest = google_cloud_run_v2_job.ingest.name
  }
}

output "cloudbuild_connection_status_check" {
  value = "gcloud builds connections describe ${var.github_connection_name} --region=${var.region} --project=${local.project}"
}

output "runtime_service_account" {
  value = google_service_account.run_jobs.email
}

output "cloudsql_connection_name" {
  value = google_sql_database_instance.main.connection_name
}
