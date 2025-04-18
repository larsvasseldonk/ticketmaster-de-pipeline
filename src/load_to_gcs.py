import os
import sys
import time
import glob
import logging

from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from google.api_core.exceptions import NotFound, Forbidden

BQ_DATASET_NAME = os.environ.get("BQ_DATASET_NAME")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")

class GCSUploader:
    """A class to handle file uploads to Google Cloud Storage."""
    
    def __init__(self, bucket_name: str, credentials_file: str = None):
        self.bucket_name = bucket_name
        
        # Initialize the GCS client based on the provided credentials or default authentication
        self.client = (
            storage.Client.from_service_account_json(credentials_file) 
            if credentials_file else storage.Client()
        )
        
        try:
            self.bucket = self.client.get_bucket(bucket_name)
            self._check_bucket_ownership()
        except NotFound:
            self.bucket = self._create_bucket()
    

    def _check_bucket_ownership(self):
        """Check whether the bucket belongs to the current project."""

        project_bucket_ids = [bucket.id for bucket in self.client.list_buckets()]
        if self.bucket_name not in project_bucket_ids:
            logging.error(f"Bucket '{self.bucket_name}' exists but does not belong to your project.")
            sys.exit(1)
        else:
            logging.info(f"Bucket '{self.bucket_name}' exists and belongs to your project.")
    

    def _create_bucket(self):
        """Create a new bucket if it doesn't exist."""

        try:
            bucket = self.client.create_bucket(self.bucket_name)
            logging.info(f"Created bucket '{self.bucket_name}'")
            return bucket
        except Forbidden:
            logging.info(f"Cannot create the bucket '{self.bucket_name}'. Ensure you have permission.")
            sys.exit(1)


    def verify_gcs_upload(self, blob_name: str) -> bool:
        """Verify if the blob exists in GCS."""
        blob = storage.Blob(bucket=self.bucket, name=blob_name)
        return blob.exists(self.client)


    def upload_file(self, file_path: str, max_retries: int = 3):
        """Upload a single file to GCS, retrying if necessary."""

        blob_name = os.path.basename(file_path)
        blob = self.bucket.blob(blob_name)

        for attempt in range(max_retries):
            try:
                logging.info(f"Uploading {file_path} to {self.bucket_name} (Attempt {attempt + 1})...")
                blob.upload_from_filename(file_path)
                logging.info(f"Uploaded: gs://{self.bucket_name}/{blob_name}")

                if self.verify_gcs_upload(blob_name):
                    logging.info(f"Verification successful for {blob_name}")
                    return
                else:
                    logging.error(f"Verification failed for {blob_name}, retrying...")
            except Exception as e:
                logging.error(f"Failed to upload {file_path} to GCS: {e}")

            time.sleep(5)

        logging.info(f"Giving up on {file_path} after {max_retries} attempts.")


def upload_files(file_paths, bucket_name, credentials_file=None, max_retries=3, max_threads=5):
    """Upload multiple files to GCS using multithreading."""

    uploader = GCSUploader(bucket_name, credentials_file)

    with ThreadPoolExecutor(max_threads) as executor:
        executor.map(uploader.upload_file, file_paths, [max_retries]*len(file_paths))


def get_file_paths(directory: str, pattern: str = "*.csv") -> list:
    """Get a list of file paths matching the given pattern in the specified directory."""

    return glob.glob(os.path.join(directory, pattern))


def delete_local_files(file_paths: list):
    """Delete local files after uploading to GCS."""

    logging.info("Deleting local files...")

    for file_path in file_paths:
        try:
            os.remove(file_path)
            logging.info(f"Deleted local file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to delete {file_path}: {e}")


def load_to_gcs():

    file_paths = get_file_paths("", "*.csv")
    bucket_name = GCS_BUCKET_NAME

    if file_paths:
        # Upload files to GCS and delete local files
        upload_files(file_paths, bucket_name, max_threads=5)
        delete_local_files(file_paths)
    else:
        logging.info("No CSV files found to upload.")


if __name__ == '__main__':
    load_to_gcs()