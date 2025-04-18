{{ config(materialized='table') }}

WITH event_base AS (
  SELECT DISTINCT
    id,
    name,
    url,
    date,
    time,
    timezone,
    datetime
  FROM {{ source('ticketmaster_dataset_n', 'stg_hist_events') }}
  WHERE is_current = TRUE
    AND id IS NOT NULL
)

SELECT
  ROW_NUMBER() OVER() AS event_sk, -- Surrogate key
  id,
  name,
  url,
  date,
  time,
  timezone,
  datetime
FROM event_base