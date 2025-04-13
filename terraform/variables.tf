# variable "credentials" {
#   description = "Credentials"
#   default = "keys/google_creds.json"
# }

variable "project" {
    description = "Project"
    default = "sandbox-450016"
}

variable "region" {
    description = "Region"
    default = "west-europe"
}

variable "location" {
    description = "Project Location"
    default = "europe-west1"
}

variable "bq_dataset_name" {
  description = "BigQuery Dataset Name"
  default = "ticketmaster_dataset_v2"
}

variable "gcs_bucket_name" {
  description = "Bucket Storage Name"
  default = "ticketmaster_bucket_v2"
}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default = "STANDARD"
}