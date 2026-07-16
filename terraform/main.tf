resource "google_project" "this" {
  project_id      = var.project_id
  name            = coalesce(var.project_name, var.project_id)
  billing_account = var.billing_account_id
  deletion_policy = "DELETE"
}

locals {
  project = google_project.this.project_id
}

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "workflows.googleapis.com",
    "workflowexecutions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "sqladmin.googleapis.com",
    "health.googleapis.com",
  ])

  project            = local.project
  service            = each.key
  disable_on_destroy = false

  depends_on = [google_project.this]
}

# Newly enabled APIs can take up to ~a minute to actually be usable for
# resource creation, even though the enable call itself returns immediately —
# this avoids a race where e.g. Artifact Registry / Cloud Run creation fails
# with a PERMISSION_DENIED that's really just propagation lag.
resource "time_sleep" "wait_for_apis" {
  create_duration = "60s"

  depends_on = [google_project_service.apis]
}
