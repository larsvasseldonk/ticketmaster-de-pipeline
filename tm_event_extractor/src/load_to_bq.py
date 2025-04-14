from google.cloud import bigquery, storage
from google.api_core.exceptions import GoogleAPICallError, NotFound, BadRequest, Conflict
from concurrent.futures import ThreadPoolExecutor

import logging
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)


class BigQueryLoader:
    """A class to handle loading data into BigQuery from Google Cloud Storage."""

    def __init__(self, project_id: str):
        """Initialize the BigQuery client."""
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id

    def load_data(self, dataset_id: str, table_id: str, source_uri: str, schema: list, write_disposition: str = "WRITE_APPEND"):
        """
        Load data from a CSV file in Google Cloud Storage to BigQuery.

        :param dataset_id: The BigQuery dataset ID.
        :param table_id: The BigQuery table ID.
        :param source_uri: The GCS URI of the CSV file.
        :param schema: The schema of the BigQuery table.
        :param write_disposition: Write disposition for the load job (default is WRITE_APPEND).
        """

        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        logging.info(f"Starting data load from {source_uri} to BigQuery table {table_ref}...")

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,
            write_disposition=write_disposition,
            schema=schema
        )

        try:
            load_job = self.client.load_table_from_uri(
                source_uri, table_ref, job_config=job_config
            )
            load_job.result()  # Wait for the job to complete
            logging.info(f"Successfully loaded {load_job.output_rows} rows into {table_ref}.")
        except NotFound as e:
            logging.error(f"Resource not found: {e}")
        except BadRequest as e:
            logging.error(f"Bad request: {e}")
        except GoogleAPICallError as e:
            logging.error(f"API call error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")

    
    def update_existing_records(self, dataset_id: str, table_id: str):
        """
        Execute a SQL query in BigQuery.

        :param query: The SQL query to execute.
        """

        query = f"""
            MERGE `{self.project_id}.{dataset_id}.{table_id}` T
            USING `{self.project_id}.{dataset_id}.stg_events` S
            ON T.id = S.id
            WHEN MATCHED AND 
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
            THEN UPDATE SET
                T.name = S.name,
                T.url = S.url,
                T.date = S.date,
                T.time = S.time,
                T.timezone = S.timezone,
                T.datetime = S.datetime,
                T.venue = S.venue,
                T.city = S.city,
                T.country = S.country,
                T.postal_code = S.postal_code,
                T.latitude = S.latitude,
                T.longitude = S.longitude,
                T.address = S.address,
                T.promotor_id = S.promotor_id
            WHEN NOT MATCHED THEN
            INSERT (
                id, name, url, date, time, timezone, datetime, venue, city, country,
                postal_code, latitude, longitude, address, promotor_id
            ) VALUES (
                S.id, S.name, S.url, S.date, S.time, S.timezone, S.datetime, S.venue,
                S.city, S.country, S.postal_code, S.latitude, S.longitude, S.address,
                S.promotor_id
            );        
        """


        try:
            query_job = self.client.query(query)
            query_job.result()  # Wait for the job to complete
            logging.info(f"Query executed successfully.")
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
        for blob in blobs if blob.name.endswith(".csv")
    ]
    logging.info(f"Found {len(file_paths)} CSV files in bucket {bucket_name}.")

    return file_paths


def move_file_to_archive(bucket_name: str, blob_name: str):
    """Move the file to an archive location after processing."""

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    source_blob = bucket.blob(blob_name)
    destination_blob_name = f"archive/{blob_name}"

    try:
        print(f"Moving {blob_name} to {destination_blob_name}...")

        # Copy the blob to the new location
        bucket.copy_blob(source_blob, bucket, destination_blob_name)

        # Delete the original blob
        source_blob.delete()

    except Exception as e:
        print(f"Failed to move {source_blob} to archive: {e}")

    logging.info(f"Moved {blob_name} to archive.")


def create_table(schema, project_id, dataset_id, table_id):
    # Initialize the BigQuery client
    client = bigquery.Client(project=project_id)
    
    # Specify the dataset and table reference
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)

    # Define the schema for the table
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
        bigquery.SchemaField("promotor_id", "STRING"),
        bigquery.SchemaField("hash_key", "STRING"),
        bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("start_datetime", "TIMESTAMP"),
        bigquery.SchemaField("end_datetime", "TIMESTAMP"),
    ]

    # Create the table object
    table = bigquery.Table(table_ref, schema=schema)

    try:
        # Create the table in BigQuery
        table = client.create_table(table) 
    except Conflict:
        print(f"Table {table_id} already exists in dataset {dataset_id}.")

    print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")


def load_data():
    """Main function to run the data loader."""

    # Set example parameters
    project_id = "sandbox-450016"
    dataset_id = "ticketmaster_dataset"
    stg_table_id = "stg_events"
    stg_hist_table_id = "stg_hist_events_new"
    bucket_name = "ticketmaster_bucket"

    schema_stg = [
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
        bigquery.SchemaField("promotor_id", "STRING"),
    ]
    schema_stg_hist = schema_stg + [
        bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("start_datetime", "TIMESTAMP"),
        bigquery.SchemaField("end_datetime", "TIMESTAMP"),
    ]
    write_disposition = "WRITE_APPEND"  # Options: WRITE_APPEND, WRITE_TRUNCATE, WRITE_EMPTY

    create_table(schema_stg_hist, project_id, dataset_id, stg_hist_table_id)

    # Instantiate loader and load data
    loader = BigQueryLoader(project_id)

    file_paths = list_csv_files(bucket_name)

    max_threads = 5
    with ThreadPoolExecutor(max_threads) as executor:
        for source_uri in file_paths:
            # Load each CSV file to BigQuery
            executor.submit(loader.load_data, dataset_id, stg_table_id, source_uri, schema_stg, write_disposition)
            
            # Execute a merge to handle SCD
            # loader.update_existing_records(dataset_id, stg_hist_table_id,)


if __name__ == "__main__":
    load_data()