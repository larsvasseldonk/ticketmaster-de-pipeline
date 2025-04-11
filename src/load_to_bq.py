from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError, NotFound, BadRequest

import logging

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
        logging.info(f"Starting data load from {source_uri} to BigQuery table {table_ref}.")

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


def load_to_bq():
    """Main function to run the data loader."""

    # Set example parameters
    project_id = "sandbox-450016"
    dataset_id = "ticketmaster_dataset"
    table_id = "stg_hist_events"
    source_uri = "gs://ticketmaster_bucket/2025041114H_events.csv"
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
    write_disposition = "WRITE_APPEND"

    # Instantiate loader and load data
    loader = BigQueryLoader(project_id)
    loader.load_data(dataset_id, table_id, source_uri, schema, write_disposition)

if __name__ == "__main__":
    load_to_bq()