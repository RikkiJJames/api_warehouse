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

variable "operator_email" {
  description = "Google account that manually triggers builds / operates this project via gcloud CLI (needs cloudbuild.builds.editor to run triggers) — separate from whatever identity terraform apply itself runs as."
  type        = string
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

  ]
}

variable "ingest_dbt_schedule" {
  description = "Cron schedule (unix-cron) for the hourly ingest-then-dbt Workflow run."
  type        = string
  default     = "0 * * * *"
}

variable "ingest_dbt_schedule_timezone" {
  description = "Time zone for ingest_dbt_schedule."
  type        = string
  default     = "Europe/London"
}

variable "services" {
  description = <<-EOT
    Backend Cloud Run services, one per GitHub repo under github_owner, built
    and deployed via their own push-triggered Cloud Build. Private by default
    (no allow_unauthenticated binding) — only the Astro frontend's service
    account (astro_frontend below) can invoke them. Each repo must have its
    own `cloudbuild.yaml` at its root; see services.tf for the substitutions
    it can use (_REGION, _REPOSITORY, _SERVICE_NAME).
  EOT
  type = map(object({
    github_repo = string
    port        = optional(number, 8080)
    cpu         = optional(string, "2")
    memory      = optional(string, "1Gb")
    env         = optional(map(string), {})
  }))
  default = {
    pokemon-dash = {
      github_repo = "Pokemon-Dash"
    }
  }
}
