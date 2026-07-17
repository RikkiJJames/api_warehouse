# The Astro portfolio site (github.com/${var.github_owner}/home-app) —
# public Cloud Run service + Cloud Build, with a custom domain mapped to it.
#
# Deployed in europe-west1, not var.region (europe-west2), because Cloud
# Run's classic domain-mapping resource — the simplest way to attach a
# custom domain without standing up a full Global External Application
# Load Balancer (Serverless NEG + backend service + URL map + managed cert
# + forwarding rule) — only supports a fixed list of regions, and
# europe-west2 isn't one of them. europe-west1 (Belgium) is, and is close
# enough that it doesn't matter for a personal site's latency.
locals {
  website_region = "europe-west1"
}

resource "google_service_account" "website" {
  project      = local.project
  account_id   = "astro-website"
  display_name = "Runtime SA for the home-app Astro portfolio site"

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_service_account_iam_member" "cloudbuild_act_as_website" {
  service_account_id = google_service_account.website.name
  role               = "roles/iam.serviceAccountUser"
  member             = local.cloudbuild_sa
}

resource "google_cloudbuildv2_repository" "website" {
  project           = local.project
  location          = var.region
  name              = "home-app"
  parent_connection = local.github_connection_path
  remote_uri        = "https://github.com/${var.github_owner}/home-app.git"

  depends_on = [time_sleep.wait_for_apis]
}

resource "google_cloud_run_v2_service" "website" {
  project  = local.project
  name     = "home-app"
  location = local.website_region

  deletion_protection = var.job_deletion_protection

  template {
    service_account = google_service_account.website.email

    containers {
      # Placeholder — Cloud Build owns the real image after the first push
      # via `gcloud run services update --image=...`, matching services.tf.
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      # Dockerfile's runtime stage serves dist/ via nginx on port 80.
      ports {
        container_port = 80
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers]
  }

  depends_on = [time_sleep.wait_for_apis]
}

# Public — this is the site itself, not a private backend API.
resource "google_cloud_run_v2_service_iam_member" "website_public" {
  project  = local.project
  location = local.website_region
  name     = google_cloud_run_v2_service.website.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloudbuild_trigger" "website" {
  project  = local.project
  location = var.region
  name     = "home-app-deploy"

  repository_event_config {
    repository = google_cloudbuildv2_repository.website.id
    push {
      branch = var.branch_pattern
    }
  }

  filename        = "terraform/cloudbuild.yaml"
  service_account = local.cloudbuild_sa_resource_name

  substitutions = {
    _REGION       = local.website_region
    _REPOSITORY   = google_artifact_registry_repository.images.repository_id
    _SERVICE_NAME = google_cloud_run_v2_service.website.name
  }
}

# The base domain (rikkijtech.com) must already be verified for this GCP
# account in Search Console before this applies successfully — see
# https://docs.cloud.google.com/run/docs/mapping-custom-domains. Run
# `gcloud domains verify rikkijtech.com` first if `terraform apply` fails
# here with a verification error.
#
# Maps both the apex (rikkijtech.com) and www — without the apex mapping,
# visitors who leave off "www." get nothing. The apex needs A/AAAA records
# at your registrar instead of a CNAME; `terraform apply`'s output (or
# `gcloud run domain-mappings describe`) will show the exact records once
# this is created.
resource "google_cloud_run_domain_mapping" "website" {
  for_each = toset(["www.rikkijtech.com", "rikkijtech.com"])

  project  = local.project
  location = local.website_region
  name     = each.value

  metadata {
    namespace = local.project
  }

  spec {
    route_name = google_cloud_run_v2_service.website.name
  }

  depends_on = [google_cloud_run_v2_service.website]
}
