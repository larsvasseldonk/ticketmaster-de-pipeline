terraform {
  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "6.19.0"
    }
  }
}

provider "google" {
#   credentials = file(var.credentials)
  project     = var.project
  region      = "europe-west1"
}

resource "google_storage_bucket" "ticketmaster-bucket-450016" {
  name          = "${var.project}-ticketmaster-bucket"
  location      =  "europe-west1"
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

resource "google_storage_bucket" "function_bucket" {
    name     = "${var.project}-function-bucket"
    location =  "europe-west1"
}

resource "google_bigquery_dataset" "ticketmaster-dataset-450016" {
  dataset_id                  = var.bq_dataset_name
  location                    = "europe-west1"
}