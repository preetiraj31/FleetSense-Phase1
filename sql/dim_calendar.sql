-- dim_calendar: one row per day from Sep 2025 to Aug 2026.
-- Provides date attributes (weekday, weekend, week of year) to join with trips.
CREATE OR REPLACE TABLE dim_calendar AS
SELECT
    d::DATE AS date_key,
    YEAR(d) AS year,
    MONTH(d) AS month,
    DAY(d) AS day,
    WEEKOFYEAR(d) AS week_of_year,
    DAYOFWEEK(d) AS day_of_week,
    DAYNAME(d) AS day_name,
    DAYOFWEEK(d) IN (0, 6) AS is_weekend
FROM generate_series(DATE '2025-09-01', DATE '2026-08-31', INTERVAL 1 DAY) AS t(d);