# FleetSense Core Metric Definitions

All operational metrics are computed in `src/metrics.py` from `fact_trips` joined with `dim_zones` (`fact_trips.pickup_zone_id = dim_zones.zone_id`) inside `data/warehouse/fleetsense.duckdb`.

Per the Airport Desk client requirement (Renata Okonkwo-Hale), every metric is strictly segmented by `dim_zones.is_airport` (`TRUE` for JFK, LaGuardia, and Newark; `FALSE` for all City zones) so Airport and City figures are never mixed.

## Metric Reference Table

| Metric | Business Definition | SQL Formula | Data Quality Filter |
| :--- | :--- | :--- | :--- |
| **Total Trips** | Count of valid completed pickups. | `COUNT(*)` | Non-null pickup timestamp and pickup zone ID (enforced in `fact_trips`). |
| **Total Revenue** | Sum of total passenger charges (metered fare, tips, tolls, surcharges). | `ROUND(SUM(f.total_amount), 2)` | None beyond `fact_trips` validity. |
| **Average Fare** | Mean base metered fare per trip in USD. | `ROUND(AVG(f.fare_amount), 2)` | None beyond `fact_trips` validity. |
| **Average Duration** | Mean trip length in minutes from pickup to dropoff. | `ROUND(AVG(f.trip_duration_min), 2)` | `trip_duration_min > 0 AND trip_duration_min < 360` (excludes negative/zero timestamps and >6-hour outliers). |
| **Utilisation Proxy** | Total active fleet hours per period. Because NYC TLC yellow taxi data does not expose individual vehicle IDs, cumulative active trip-hours serve as the fleet utilisation proxy. | `ROUND(SUM(f.trip_duration_min) / 60.0, 2)` | `trip_duration_min > 0 AND trip_duration_min < 360`. |

## Verified Baseline Output (12-Month Warehouse)

| Segment | Total Trips | Total Revenue ($) | Average Fare ($) | Average Duration (min) | Utilisation Proxy (hrs) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| **Airport** | 3,094,574 | 226,085,287.59 | 53.01 | 38.45 | 1,917,086.03 |
| **City** | 43,774,945 | 1,144,385,083.00 | 18.21 | 16.68 | 11,917,046.60 |