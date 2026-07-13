resource "google_project" "this" {
  project_id      = var.project_id
  name            = coalesce(var.project_name, var.project_id)
  billing_account = var.billing_account_id
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
  ])

  project            = local.project
  service            = each.key
  disable_on_destroy = false

  depends_on = [google_project.this]
}
