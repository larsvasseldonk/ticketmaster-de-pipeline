terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.34.0"
    }
  }
}

provider "google" {
  project     = "sandbox-450016"
}

locals {
  project = "sandbox-450016" # Google Cloud Platform Project ID
}

resource "google_storage_bucket" "tm_event_extractor-bucket" {
  name          = "ticketmaster-bucket-new"
  location      = "us-central1"
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

resource "google_bigquery_dataset" "tm_event_extractor-dataset" {
  dataset_id                  = "ticketmaster_dataset_new"
  location                    = "us-central1"
}

resource "google_storage_bucket" "bucket" {
  name                        = "${local.project}-gcf-source"  # Every bucket name must be globally unique
  location                    = "US"
  force_destroy                = true
  uniform_bucket_level_access = true
}

data "archive_file" "default" {
  type        = "zip"
  output_path = "/tmp/function-source.zip"
  source_dir  = "../src/"
}

resource "google_storage_bucket_object" "object" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.bucket.name
  source = data.archive_file.default.output_path  # Add path to the zipped function source code
}

resource "google_cloudfunctions2_function" "function" {
  name        = "gcf-tm-event-extractor" # name should use kebab-case so generated Cloud Run service name will be the same
  location    = "us-central1"
  description = "Cloud function to extract data from Ticketmaster API and load it into BigQuery"

  build_config {
    runtime     = "python311"
    entry_point = "run_data_pipeline"  # Set the entry point
    source {
      storage_source {
        bucket = google_storage_bucket.bucket.name
        object = google_storage_bucket_object.object.name
      }
    }
  }

  service_config {
    min_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds       = 60
    environment_variables = {
      "BQ_DATASET_NAME" = google_bigquery_dataset.tm_event_extractor-dataset.dataset_id
      "GCS_BUCKET_NAME" = google_storage_bucket.tm_event_extractor-bucket.name
      "TICKETMASTER_API_KEY" = "xkwIHOr5jYGxFVPOCeIF9JMeP2YPjQzH"
    }
  }
}

resource "google_cloudfunctions2_function_iam_member" "invoker" {
  project        = google_cloudfunctions2_function.function.project
  location       = google_cloudfunctions2_function.function.location
  cloud_function = google_cloudfunctions2_function.function.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

resource "google_cloud_run_service_iam_member" "cloud_run_invoker" {
  project  = google_cloudfunctions2_function.function.project
  location = google_cloudfunctions2_function.function.location
  service  = google_cloudfunctions2_function.function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_scheduler_job" "invoke_cloud_function" {
  name        = "invoke-gcf-function"
  description = "Schedule the HTTPS trigger for cloud function"
  schedule    = "0 0 * * *" # every day at midnight
  project     = google_cloudfunctions2_function.function.project
  region      = google_cloudfunctions2_function.function.location

  http_target {
    uri         = google_cloudfunctions2_function.function.service_config[0].uri
    http_method = "POST"
  }
}