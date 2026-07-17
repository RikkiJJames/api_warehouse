output "project_id" {
  value = google_project.this.project_id
}

output "artifact_registry_repository" {
  value = "${var.region}-docker.pkg.dev/${local.project}/${google_artifact_registry_repository.images.repository_id}"
}

output "website_artifact_registry_repository" {
  value = "${local.website_region}-docker.pkg.dev/${local.project}/${google_artifact_registry_repository.website_images.repository_id}"
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

# The exact A/AAAA/CNAME records to create at your registrar for each
# domain — Google only knows these once the mapping resource exists, so
# they can't be hardcoded here.
output "website_dns_records" {
  value = {
    for domain, mapping in google_cloud_run_domain_mapping.website :
    domain => [
      for rr in mapping.status[0].resource_records : {
        type   = rr.type
        name   = rr.name
        rrdata = rr.rrdata
      }
    ]
  }
}
