terraform {
  required_version = ">= 1.7"

  required_providers {
    google      = {
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
  }
}

provider "google" {
  region = var.region
}

provider "google-beta" {
  region = var.region
}
