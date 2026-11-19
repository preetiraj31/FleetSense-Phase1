-- hourly_demand: number of pickups per zone per hour.
-- Every zone has a row for every hour (Sep 2025 - Aug 2026); hours with
-- no pickups are filled with 0 so forecasting and the dashboard see no gaps.
CREATE OR REPLACE TABLE hourly_demand AS
WITH hours AS (
    SELECT h AS hour_ts
    FROM generate_series(
        TIMESTAMP '2025-09-01 00:00:00',
        TIMESTAMP '2026-08-31 23:00:00',
        INTERVAL 1 HOUR
    ) AS t(h)
),
grid AS (
    SELECT z.zone_id, h.hour_ts
    FROM dim_zones z
    CROSS JOIN hours h
),
counts AS (
    SELECT pickup_zone_id AS zone_id, pickup_hour AS hour_ts, COUNT(*) AS pickups
    FROM fact_trips
    GROUP BY pickup_zone_id, pickup_hour
)
SELECT g.zone_id, g.hour_ts, COALESCE(c.pickups, 0) AS pickups
FROM grid g
LEFT JOIN counts c USING (zone_id, hour_ts);