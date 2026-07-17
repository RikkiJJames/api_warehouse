# Generic backend services, one per entry in var.services (see variables.tf).
# Each is a private Cloud Run *service* (not a Job — these are long-running
# HTTP backends) built from its own GitHub repo under the same connection
# used for api_warehouse. Only the Astro frontend can invoke them; there's no
# public IAM binding here.

resource "google_service_account" "backend_services" {
  project      = local.project
  account_id   = "backend-services"
  display_name = "Shared runtime SA for services.tf Cloud Run services"

  depends_on = [time_sleep.wait_for_apis]
}

# Identity for whatever eventually calls these — point the Astro app's own
# Cloud Run service at this same service account when you build it, and it
# inherits invoker access to everything in var.services automatically.
resource "google_service_account" "astro_frontend" {
  project      = local.project
  account_id   = "astro-frontend"
  display_name = "Identity for the Astro frontend that calls backend services"

  depends_on = [time_sleep.wait_for_apis]
}

# Cloud Build deploys these services running as backend_services, same as it
# does for run_jobs in iam.tf.
resource "google_service_account_iam_member" "cloudbuild_act_as_backend_services" {
  service_account_id = google_service_account.backend_services.name
  role               = "roles/iam.serviceAccountUser"
  member             = local.cloudbuild_sa
}

resource "google_cloud_run_v2_service" "services" {
  for_each = var.services

  project  = local.project
  name     = each.key
  location = var.region

  deletion_protection = var.job_deletion_protection

  template {
    service_account = google_service_account.backend_services.email

    containers {
      # Placeholder — Cloud Build owns the real image after the first push
      # via `gcloud run services update --image=...`, matching cloudrun.tf's
      # Job pattern.
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      ports {
        container_port = each.value.port
      }

      resources {
        limits = {
          cpu    = each.value.cpu
          memory = each.value.memory
        }
      }

      dynamic "env" {
        for_each = each.value.env
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers]
  }

  depends_on = [time_sleep.wait_for_apis]
}

# Private by default — only the Astro frontend's identity can invoke —
# unless a service opts into `public = true` (allUsers instead, no
# astro_frontend grant; see the `services` variable for why).
locals {
  public_services  = { for k, v in var.services : k => v if v.public }
  private_services = { for k, v in var.services : k => v if !v.public }
}

resource "google_cloud_run_v2_service_iam_member" "services_public" {
  for_each = local.public_services

  project  = local.project
  location = var.region
  name     = google_cloud_run_v2_service.services[each.key].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "astro_can_invoke" {
  for_each = local.private_services

  project  = local.project
  location = var.region
  name     = google_cloud_run_v2_service.services[each.key].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.astro_frontend.email}"
}

# 1st-gen (github {}), not 2nd-gen repository_event_config — see the matching
# comment on google_cloudbuild_trigger.website in website.tf for why. Each
# repo in var.services needs the same one-time legacy GitHub App connection
# (Console → Cloud Build → Triggers → Connect repository) before its trigger
# can be created.
resource "google_cloudbuild_trigger" "services" {
  for_each = var.services

  project = local.project
  name    = "${each.key}-deploy"

  github {
    owner = var.github_owner
    name  = each.value.github_repo
    push {
      branch = var.branch_pattern
    }
  }

  filename        = "cloudbuild.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION       = var.region
    _REPOSITORY   = google_artifact_registry_repository.images.repository_id
    _SERVICE_NAME = google_cloud_run_v2_service.services[each.key].name
  }
}
