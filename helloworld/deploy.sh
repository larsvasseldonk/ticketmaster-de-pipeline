#!/bin/bash

gcloud run deploy python-http-function \
      --source . \
      --function hello_get \
      --base-image python312 \
      --region europe-west4 \
      --allow-unauthenticated