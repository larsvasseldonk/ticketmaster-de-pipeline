terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.19.0"
    }
  }
}

provider "google" {
  project     = var.project
  region      = var.location
}

resource "google_storage_bucket" "ticketmaster-bucket-450016" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true

  # Auto delete bucket after 10 days
  lifecycle_rule {
    condition {
      age = 10
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_bigquery_dataset" "ticketmaster-dataset-450016" {
  dataset_id                  = var.bq_dataset_name
  location                    = var.location
}

resource "google_cloudbuild_trigger" "ticketmaster_trigger" {
  name = "tm-event-extractor-trigger"
  location = var.location
  filename = "tm_event_extractor/cloudbuild.yaml"

  trigger_template {
    branch_name = "^feat/google_cloud_function$"
    invert_regex = false
    push {
      branch = "^feat/google_cloud_function$"
    }
  }
}