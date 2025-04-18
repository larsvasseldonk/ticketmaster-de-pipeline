{{ config(materialized='table') }}

WITH venue_base AS (
  SELECT DISTINCT
    venue,
    city,
    country,
    postal_code,
    latitude,
    longitude,
    address
  FROM {{ source('ticketmaster_dataset_n', 'stg_hist_events') }}
  WHERE is_current = TRUE
    AND venue IS NOT NULL
)

SELECT
  ROW_NUMBER() OVER() AS venue_sk, -- Surrogate key
  venue,
  city,
  country,
  postal_code,
  latitude,
  longitude,
  address
FROM venue_base
