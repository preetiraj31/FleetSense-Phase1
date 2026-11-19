-- fact_trips: cleaned version of raw_trips, one row per trip.
-- Keeps only trips between Sep 2025 and Aug 2026, and removes trips with
-- a missing pickup zone or a dropoff time earlier than the pickup time.
CREATE OR REPLACE TABLE fact_trips AS
SELECT
    ROW_NUMBER() OVER () AS trip_id,
    tpep_pickup_datetime AS pickup_ts,
    tpep_dropoff_datetime AS dropoff_ts,
    DATE_TRUNC('hour', tpep_pickup_datetime) AS pickup_hour,
    CAST(tpep_pickup_datetime AS DATE) AS pickup_date,
    PULocationID AS pickup_zone_id,
    DOLocationID AS dropoff_zone_id,
    passenger_count,
    trip_distance,
    fare_amount,
    total_amount,
    payment_type
FROM raw_trips
WHERE tpep_pickup_datetime >= TIMESTAMP '2025-09-01'
  AND tpep_pickup_datetime <  TIMESTAMP '2026-09-01'
  AND tpep_dropoff_datetime >= tpep_pickup_datetime
  AND PULocationID IS NOT NULL;