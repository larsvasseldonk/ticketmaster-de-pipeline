{{ config(materialized='table') }}

SELECT
  ROW_NUMBER() OVER() AS fct_event_sk, -- Surrogate key
  de.event_sk,  -- Reference to dim_event
  dv.venue_sk,  -- Reference to dim_venue
  promotor_id AS promotor_name
FROM {{ source('ticketmaster_dataset', 'stg_hist_events') }} e
LEFT JOIN {{ ref('dim_event') }} de ON e.id = de.id
LEFT JOIN {{ ref('dim_venue') }} dv ON e.venue = dv.venue
WHERE e.is_current = TRUE