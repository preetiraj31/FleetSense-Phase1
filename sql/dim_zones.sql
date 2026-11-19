-- dim_zones: one row per taxi zone (ID, borough, zone name) plus an airport flag.
-- The is_airport flag separates airport demand from city demand for the client.
CREATE OR REPLACE TABLE dim_zones AS
SELECT
    LocationID AS zone_id,
    Borough AS borough,
    Zone AS zone_name,
    service_zone,
    Zone IN ('JFK Airport', 'LaGuardia Airport', 'Newark Airport') AS is_airport
FROM dim_location;