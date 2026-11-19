-- dim_zones: one row per taxi zone (ID, borough, zone name) plus an airport flag.
-- The is_airport flag separates airport demand from city demand for the client.
CREATE OR REPLACE TABLE dim_zones AS
SELECT
    LocationID AS zone_id,
    Borough AS borough,
    Zone AS zone_name,
    service_zone,
    CASE
    
        WHEN Zone IN ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')  THEN TRUE 
        ELSE FALSE 
    END AS is_airport
FROM dim_location;

-- dim_calendar: one row per day from Sep 2025 to Aug 2026.
-- Provides date attributes (weekday, weekend, week of year) to join with trips.
-- CREATE OR REPLACE TABLE dim_calendar AS
-- SELECT
--     d::DATE AS date_key,
--     YEAR(d) AS year,
--     MONTH(d) AS month,
--     DAY(d) AS day,
--     WEEKOFYEAR(d) AS week_of_year,
--     DAYOFWEEK(d) AS day_of_week,
--     DAYNAME(d) AS day_name,
--     DAYOFWEEK(d) IN (0, 6) AS is_weekend
-- FROM generate_series(DATE '2025-09-01', DATE '2026-08-31', INTERVAL 1 DAY) AS t(d);

CREATE OR REPLACE TABLE dim_calendar AS
WITH distinct_dates AS (
    SELECT DISTINCT CAST(tpep_pickup_datetime AS DATE) AS date_key
    FROM raw_trips
    WHERE tpep_pickup_datetime IS NOT NULL
)
SELECT
    date_key,
    EXTRACT(YEAR FROM date_key) AS year,
    EXTRACT(MONTH FROM date_key) AS month,
    EXTRACT(DAY FROM date_key) AS day,
    EXTRACT(WEEK FROM date_key) AS iso_week,
    DAYNAME(date_key) AS day_of_week,
    CASE
        WHEN EXTRACT(WEEK FROM date_key) IN (1, 27, 47, 52) THEN TRUE
        ELSE FALSE
    END AS is_holiday_week
FROM distinct_dates
ORDER BY date_key;

-- fact_trips: cleaned version of raw_trips, one row per trip.
-- Keeps only trips between Sep 2025 and Aug 2026, and removes trips with
-- a missing pickup zone or a dropoff time earlier than the pickup time.

CREATE OR REPLACE TABLE fact_trips AS
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    CAST(tpep_pickup_datetime AS DATE) AS pickup_date,
    EXTRACT(HOUR FROM tpep_pickup_datetime) AS pickup_hour,
    PULocationID AS pickup_zone_id,
    DOLocationID AS dropoff_zone_id,
    fare_amount,
    total_amount,
    DATE_DIFF('minute', tpep_pickup_datetime, tpep_dropoff_datetime) AS trip_duration_min,
    -- source_file
FROM raw_trips
WHERE tpep_pickup_datetime IS NOT NULL
  AND PULocationID IS NOT NULL;


-- hourly_demand: number of pickups per zone per hour.
-- Every zone has a row for every hour (Sep 2025 - Aug 2026); hours with
-- no pickups are filled with 0 so forecasting and the dashboard see no gaps.
-- CREATE OR REPLACE TABLE hourly_demand AS
-- WITH hours AS (
--     SELECT h AS hour_ts
--     FROM generate_series(
--         TIMESTAMP '2025-09-01 00:00:00',
--         TIMESTAMP '2026-08-31 23:00:00',
--         INTERVAL 1 HOUR
--     ) AS t(h)
-- ),
-- grid AS (
--     SELECT z.zone_id, h.hour_ts
--     FROM dim_zones z
--     CROSS JOIN hours h
-- ),
-- counts AS (
--     SELECT pickup_zone_id AS zone_id, pickup_hour AS hour_ts, COUNT(*) AS pickups
--     FROM fact_trips
--     GROUP BY pickup_zone_id, pickup_hour
-- )
-- SELECT g.zone_id, g.hour_ts, COALESCE(c.pickups, 0) AS pickups
-- FROM grid g
-- LEFT JOIN counts c USING (zone_id, hour_ts);


CREATE OR REPLACE TABLE hourly_demand_per_zone AS
SELECT
    f.pickup_date,
    f.pickup_hour,
    f.pickup_zone_id AS zone_id,
    z.zone_name,
    z.borough,
    z.is_airport,
    c.iso_week,
    c.day_of_week,
    c.is_holiday_week,
    COUNT(*) AS pickup_count,
    ROUND(SUM(f.total_amount), 2) AS total_revenue,
    ROUND(AVG(f.fare_amount), 2) AS avg_fare
FROM fact_trips f
JOIN dim_zones z ON f.pickup_zone_id = z.zone_id
JOIN dim_calendar c ON f.pickup_date = c.date_key
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
ORDER BY f.pickup_date, f.pickup_hour, f.pickup_zone_id;