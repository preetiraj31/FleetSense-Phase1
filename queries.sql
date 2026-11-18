-- Airport Query
SELECT 
    EXTRACT(HOUR FROM tpep_pickup_datetime) AS hour_of_day,
    COUNT(*) AS total_pickups
FROM raw_trips
JOIN dim_location ON raw_trips.PULocationID = dim_location.LocationID
WHERE dim_location.Zone IN ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- City Query
SELECT 
    EXTRACT(HOUR FROM tpep_pickup_datetime) AS hour_of_day,
    COUNT(*) AS total_pickups
FROM raw_trips
JOIN dim_location ON raw_trips.PULocationID = dim_location.LocationID
WHERE dim_location.Zone NOT IN ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')
GROUP BY hour_of_day
ORDER BY hour_of_day;