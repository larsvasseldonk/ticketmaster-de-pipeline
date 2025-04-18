# Terrafrom

The Terraform scripts in this folder set up the required infrastructure for the Ticketmaster Event Extractor project. Below, you will find a brief overview of the components that are being created.

- **Google Storage Bucket `tm_event_extractor_bucket`**
  - **Purpose:** Stores and manages files required by the Ticketmaster event extraction process. Ensures lifecycle management by automatically deleting objects older than 10 days.

- **Google BigQuery Dataset `tm_event_extractor_dataset`**
  - **Purpose:** Serves as a datawarehouse for storing the extracted data from Ticketmaster API, allowing for easy data analysis and querying.

- **Google Storage Bucket `source_bucket`**
  - **Purpose:** Holds source code and assets needed to deploy and run the Google Cloud Function. Also uses uniform access control for simplified permissions management.

- **Data Archive `default`**
  - **Purpose:** Packages the source code directory into a ZIP archive, preparing it for deployment to Google Cloud Functions.

- **Google Storage Bucket Object `function_object`**
  - **Purpose:** Represents the archived function source code uploaded to the `source_bucket`, enabling the function's deployment from cloud storage.

- **Google Cloud Functions `gcf_tm_event_extractor`**
  - **Purpose:** Executes serverless computing to extract data from Ticketmaster API and load it into BigQuery. Configured with environment-specific setups and resource specifications.

- **IAM Member for Google Cloud Functions `invoker`**
  - **Purpose:** Grants public access permissions to invoke the deployed Cloud Function.

- **IAM Member for Google Cloud Run Service `run_invoker`**
  - **Purpose:** Provides public access permissions to invoke the associated Cloud Run service.

- **Google Cloud Scheduler Job `invoke_cloud_function`**
  - **Purpose:** Automates the periodic invocation of the cloud function, scheduling it to run daily at midnight using an HTTP POST request.