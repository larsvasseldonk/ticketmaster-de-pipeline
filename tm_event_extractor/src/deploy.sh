#!/bin/bash

gcloud run deploy tmp-ticketmaster-data-pipeline \
    --source . \
    --function run_data_pipeline \
    --base-image python312 \
    --region europe-west4 \
    --allow-unauthenticated