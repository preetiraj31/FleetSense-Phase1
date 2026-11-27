# FleetSense Metric Definitions

The operational metrics are computed from `fact_trips` joined to
`dim_zones` using `fact_trips.pickup_zone_id = dim_zones.zone_id`.

Airport and City values are separated by `dim_zones.is_airport`: `TRUE`
is airport demand and `FALSE` is city demand.

| Metric | Definition | Filter |
|---|---|---|
| Total Trips | Number of trips in the segment | Valid pickup zone and pickup time |
| Total Revenue | Sum of `total_amount` in USD | No extra filter |
| Average Fare | Mean `fare_amount` in USD | No extra filter |
| Average Duration | Mean trip duration in minutes | Duration greater than 0 and less than 360 minutes |
| Utilisation Proxy | Sum of valid trip durations converted to hours | Duration greater than 0 and less than 360 minutes |
