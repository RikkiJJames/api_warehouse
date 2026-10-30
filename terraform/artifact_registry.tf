resource "google_artifact_registry_repository" "images" {
  project       = local.project
  location      = var.region
  repository_id = "api-warehouse"
  format        = "DOCKER"
  description   = "Container images for api_warehouse (dbt, ingest, analysis)"

  # Every push adds a new :$COMMIT_SHA image and nothing ever removed the old
  # ones, so storage grew without bound. Keep the 5 most recent versions of
  # each image (current deploy plus a few to roll back to) and delete
  # anything else once it's a week old — KEEP policies win over DELETE.
  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "604800s"
    }
  }

  depends_on = [time_sleep.wait_for_apis]
}
