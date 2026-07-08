variable "project_id" {
  description = "GCP project ID to create (must be globally unique, 6-30 chars, lowercase/digits/hyphens)."
  type        = string
}

variable "project_name" {
  description = "Human-readable project display name."
  type        = string
  default     = null
}

variable "billing_account_id" {
  description = "Billing account ID to attach the new project to (format XXXXXX-XXXXXX-XXXXXX)."
  type        = string
  sensitive   = true
}

variable "job_deletion_protection" {
  description = "Whether the Cloud Run Jobs block terraform destroy/apply from deleting them. Defaults to false since Cloud Build owns the real image/config after the first deploy anyway."
  type        = bool
  default     = false
}

variable "region" {
  description = "Default region for Artifact Registry, Cloud Run and Cloud Build resources."
  type        = string
  default     = "us-central1"
}

variable "github_owner" {
  description = "GitHub org/user that owns the repo (e.g. rikkijames)."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name."
  type        = string
  default     = "api_warehouse"
}

variable "branch_pattern" {
  description = "Regex of branches that trigger a build/deploy."
  type        = string
  default     = "^main$"
}

variable "github_connection_name" {
  description = <<-EOT
    Name of the Cloud Build GitHub connection, created out-of-band via:
      gcloud builds connections create github <name> --region=<region> --project=<project_id>
    Terraform only reads this connection (data source), it doesn't create it.
  EOT
  type        = string
  default     = "github-connection"
}

variable "db_secret_names" {
  description = "Secret Manager secret names for dbt/ingest DB connection env vars (values populated out-of-band)."
  type        = list(string)
  default     = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
}

variable "ingest_secret_names" {
  description = "Secret Manager secret names for ingest-only API credentials (values populated out-of-band)."
  type        = list(string)
  default = [
    "SPORTS_API_KEY",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REFRESH_TOKEN",
    "SPOTIFY_REDIRECT_URL",
    "HARDCOVER_API_TOKEN",
    "TRAKT_CLIENT_ID",
    "TRAKT_CLIENT_SECRET",
    "TRAKT_REFRESH_TOKEN",
    "TRAKT_REDIRECT_URL",
  ]
}
