import functions_framework
import requests
import logging

from extract_data import extract_data
from load_to_gcs import load_to_gcs
from load_to_bq import load_to_bq 

from google.cloud.logging import Client as CloudLoggingClient

logging_client = CloudLoggingClient()
logging_client.setup_logging()

@functions_framework.http
def run_data_pipeline(request):
    """HTTP Cloud Function to run the ETL pipeline.
    Args:
        request (flask.Request): The request object.
    
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
    """

    try:

        # Extract data from Ticketmaster API and save to CSV
        extract_data()

        # Load CSV files to GCS
        load_to_gcs()

        # Load CSV files from GCS to BigQuery
        load_to_bq()

        return "ETL pipeline executed successfully", 200

    except Exception as e:
        logging.error(f"Error during ETL pipeline execution: {e}")
        return f"ETL pipeline failed: {e}", 500
