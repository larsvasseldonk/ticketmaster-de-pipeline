from google.cloud import bigquery, storage
from google.api_core.exceptions import GoogleAPICallError, NotFound, BadRequest

from os.path import basename
import os

import logging
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

BQ_DATASET_NAME = os.environ.get("BQ_DATASET_NAME")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")


class BigQueryLoader:
    """A class to handle loading data into BigQuery from Google Cloud Storage."""

    def __init__(self, project_id: str):
        """Initialize the BigQuery client."""
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id

    def load_data(self, dataset_id: str, table_name: str, source_uri: str, schema: list, write_disposition: str = "WRITE_APPEND"):
        """
        Load data from a CSV file in Google Cloud Storage to BigQuery.

        :param dataset_id: The BigQuery dataset ID.
        :param table_id: The BigQuery table ID.
        :param source_uri: The GCS URI of the CSV file.
        :param schema: The schema of the BigQuery table.
        :param write_disposition: Write disposition for the load job (default is WRITE_APPEND).
        """

        # Add SCD2 fields to schema
        scd2_schema = schema + [
            bigquery.SchemaField("effective_start_date", "TIMESTAMP"),
            bigquery.SchemaField("effective_end_date", "TIMESTAMP"),
            bigquery.SchemaField("is_current", "BOOLEAN")
        ]

        table_ref = f"{self.project_id}.{dataset_id}.stg_hist_{table_name}"
        stg_table_ref = f"{self.project_id}.{dataset_id}.stg_{table_name}"
        logging.info(f"Starting data load from {source_uri} to BigQuery table {table_ref}...")

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,
            write_disposition=write_disposition,
            schema=schema
        )

        try:
            # Check if historical table exists, if not create it
            try:
                self.client.get_table(table_ref)
            except NotFound:
                logging.info(f"Creating table {table_ref}...")
                table = bigquery.Table(table_ref, schema=scd2_schema)
                self.client.create_table(table)

            # 1. Load to stg table
            load_job = self.client.load_table_from_uri(
                source_uri, stg_table_ref, job_config=job_config
            )
            load_job.result()
            logging.info(f"Successfully loaded {load_job.output_rows} rows into {stg_table_ref}")

            # 2. Execute merge statement
            merge_query = f"""
            MERGE INTO `{table_ref}` T
            USING (
                SELECT *, 
                CURRENT_TIMESTAMP() as effective_start_date,
                CAST(NULL AS TIMESTAMP) as effective_end_date,
                TRUE as is_current
                FROM `{stg_table_ref}`
            ) S
            ON T.id = S.id AND T.is_current = TRUE
            WHEN MATCHED AND (
                T.name != S.name OR 
                T.url != S.url OR
                T.date != S.date OR
                T.time != S.time OR
                T.timezone != S.timezone OR
                T.datetime != S.datetime OR
                T.venue != S.venue OR 
                T.city != S.city OR
                T.country != S.country OR
                T.postal_code != S.postal_code OR
                T.latitude != S.latitude OR
                T.longitude != S.longitude OR
                T.address != S.address OR
                T.promotor_id != S.promotor_id
            ) THEN
                UPDATE SET 
                    is_current = FALSE,
                    effective_end_date = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN
                INSERT (
                    id, name, url, date, time, timezone, datetime,
                    venue, city, country, postal_code, latitude, longitude,
                    address, promotor_id, effective_start_date, 
                    effective_end_date, is_current
                )
                VALUES (
                    S.id, S.name, S.url, S.date, S.time, S.timezone, S.datetime,
                    S.venue, S.city, S.country, S.postal_code, S.latitude, S.longitude,
                    S.address, S.promotor_id, S.effective_start_date,
                    S.effective_end_date, S.is_current
                )
            """
            
            query_job = self.client.query(merge_query)
            query_job.result()

            logging.info(f"Successfully processed SCD2 load for table {table_ref}")

        except NotFound as e:
            logging.error(f"Resource not found: {e}")
        except BadRequest as e:
            logging.error(f"Bad request: {e}")
        except GoogleAPICallError as e:
            logging.error(f"API call error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")


def list_csv_files(bucket_name: str) -> list:
    """List all CSV files in the specified GCS bucket."""

    datetime_today = datetime.datetime.now().strftime("%Y%m%d")

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()

    file_paths = [
        f"gs://{bucket_name}/{blob.name}" 
        for blob in blobs if (blob.name.endswith(".csv")) & (blob.name.startswith(datetime_today))
    ]
    logging.info(f"Found {len(file_paths)} CSV files in bucket {bucket_name}.")

    return file_paths


def move_file_to_archive(bucket_name: str, source_uri: str):
    """Move the file to an archive location after processing."""

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob_name = basename(source_uri.replace(f"gs://{bucket_name}/", ""))
    
    source_blob = bucket.blob(blob_name)
    destination_blob_name = f"archive/{blob_name}"

    try:
        logging.info(f"Moving {blob_name} to {destination_blob_name}...")

        # Copy the blob to the new location
        bucket.copy_blob(source_blob, bucket, destination_blob_name)

        # Delete the original blob
        source_blob.delete()

    except Exception as e:
        logging.error(f"Failed to move {source_blob} to archive: {e}")

    logging.info(f"Moved {blob_name} to archive.")


def load_to_bq():
    """Main function to run the data loader."""

    # Set example parameters
    project_id = "sandbox-450016"
    dataset_id = BQ_DATASET_NAME
    table_name = "events"
    bucket_name = GCS_BUCKET_NAME
    schema = [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("url", "STRING"),
        bigquery.SchemaField("date", "DATE"),
        bigquery.SchemaField("time", "TIME"),
        bigquery.SchemaField("timezone", "STRING"),
        bigquery.SchemaField("datetime", "TIMESTAMP"),
        bigquery.SchemaField("venue", "STRING"),
        bigquery.SchemaField("city", "STRING"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("postal_code", "STRING"),
        bigquery.SchemaField("latitude", "FLOAT"),
        bigquery.SchemaField("longitude", "FLOAT"),
        bigquery.SchemaField("address", "STRING"),
        bigquery.SchemaField("promotor_id", "STRING")
    ]
    write_disposition = "WRITE_TRUNCATE"  # Options: WRITE_APPEND, WRITE_TRUNCATE, WRITE_EMPTY

    # Instantiate loader and load data
    loader = BigQueryLoader(project_id)

    file_paths = list_csv_files(bucket_name)

    for source_uri in file_paths:
        try:
            # Load CSV file to BigQuery
            loader.load_data(dataset_id, table_name, source_uri, schema, write_disposition)
            # Only move to archive if load was successful
            move_file_to_archive(bucket_name, source_uri)
        except Exception as e:
            logging.error(f"Failed to process {source_uri}: {e}")
            continue


if __name__ == "__main__":
    load_to_bq()