terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.34.0"
    }
  }
}

provider "google" {
  project = local.project
}

resource "google_storage_bucket" "tm_event_extractor_bucket" {
  name          = "ticketmaster-bucket_n"
  location      = local.location
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

resource "google_bigquery_dataset" "tm_event_extractor_dataset" {
  dataset_id = "ticketmaster_dataset_n"
  location   = local.location
}

resource "google_storage_bucket" "source_bucket" {
  name                        = "${local.project}-gcf-source"  # Every bucket name must be globally unique
  location                    = "US"
  force_destroy               = true
  uniform_bucket_level_access = true
}

data "archive_file" "default" {
  type        = "zip"
  output_path = "/tmp/function-source.zip"
  source_dir  = "../src/"
}

resource "google_storage_bucket_object" "function_object" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.source_bucket.name
  source = data.archive_file.default.output_path # Path to the zipped function source code
}

resource "google_cloudfunctions2_function" "gcf_tm_event_extractor" {
  name        = "gcf-tm-event-extractor" # Use kebab-case for readability and consistency with Cloud Run
  location    = local.location
  description = "Cloud function to extract data from Ticketmaster API and load it into BigQuery"

  build_config {
    runtime     = "python311"
    entry_point = "run_data_pipeline"  # Set the entry point for the function
    source {
      storage_source {
        bucket = google_storage_bucket.source_bucket.name
        object = google_storage_bucket_object.function_object.name
      }
    }
  }

  service_config {
    min_instance_count      = 1
    available_memory        = "256M"
    timeout_seconds         = 60
    environment_variables = {
      BQ_DATASET_NAME         = google_bigquery_dataset.tm_event_extractor_dataset.dataset_id
      GCS_BUCKET_NAME         = google_storage_bucket.tm_event_extractor_bucket.name
      TICKETMASTER_API_KEY    = "your_api_key_here"  # Make sure this is secured
    }
  }
}

resource "google_cloudfunctions2_function_iam_member" "invoker" {
  project        = google_cloudfunctions2_function.gcf_tm_event_extractor.project
  location       = google_cloudfunctions2_function.gcf_tm_event_extractor.location
  cloud_function = google_cloudfunctions2_function.gcf_tm_event_extractor.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"  # Consider restrictions for security
}

resource "google_cloud_run_service_iam_member" "run_invoker" {
  project  = google_cloudfunctions2_function.gcf_tm_event_extractor.project
  location = google_cloudfunctions2_function.gcf_tm_event_extractor.location
  service  = google_cloudfunctions2_function.gcf_tm_event_extractor.name
  role     = "roles/run.invoker"
  member   = "allUsers"  # Consider restrictions for security
}

resource "google_cloud_scheduler_job" "invoke_cloud_function" {
  name        = "invoke-gcf-function"
  description = "Schedule the HTTPS trigger for cloud function"
  schedule    = "0 0 * * *"  # every day at midnight
  project     = google_cloudfunctions2_function.gcf_tm_event_extractor.project
  region      = google_cloudfunctions2_function.gcf_tm_event_extractor.location

  http_target {
    uri         = google_cloudfunctions2_function.gcf_tm_event_extractor.service_config[0].uri
    http_method = "POST"
  }
}
