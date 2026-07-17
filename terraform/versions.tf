terraform {
  required_version = ">= 1.7"

  # Bucket/prefix deliberately omitted here — a backend block can't reference
  # vars/locals (it's evaluated before the rest of the config), and the
  # bucket name is project-specific. Set via, e.g.:
  #   terraform init -backend-config="bucket=<project_id>-tfstate" \
  #                   -backend-config="prefix=terraform/state"
  # See README/bootstrap notes for the one-time `gcloud storage buckets
  # create` step this depends on.
  backend "gcs" {}

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.13"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  region = var.region
}

provider "google-beta" {
  region = var.region
}
