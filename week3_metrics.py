from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "warehouse" / "fleetsense.duckdb"
OUTPUT = ROOT / "data" / "exports" / "week3"

# Analysis period from your Week 2 load. The end date is exclusive.
START = "2025-09-01"
END = "2026-09-01"

METRICS_SQL = """
WITH eligible AS (
    SELECT
        z.zone_id,
        z.zone_name,
        z.borough,
        z.is_airport,
        r.fare_amount,
        r.total_amount,
        COALESCE(r.tolls_amount, 0) AS tolls,
        COALESCE(r.extra, 0)
            + COALESCE(r.improvement_surcharge, 0)
            + COALESCE(r.congestion_surcharge, 0)
            + COALESCE(r.Airport_fee, 0)
            + COALESCE(r.cbd_congestion_fee, 0) AS surcharges,
        DATE_DIFF(
            'second', r.tpep_pickup_datetime, r.tpep_dropoff_datetime
        ) / 60.0 AS trip_minutes
    FROM raw_trips AS r
    JOIN dim_zones AS z ON r.PULocationID = z.zone_id
    WHERE r.tpep_pickup_datetime >= CAST(? AS DATE)
      AND r.tpep_pickup_datetime < CAST(? AS DATE)
      AND r.tpep_dropoff_datetime >= r.tpep_pickup_datetime
      AND r.fare_amount >= 0
      AND r.total_amount >= 0
      AND z.zone_id NOT IN (264, 265)
)
SELECT
    zone_id,
    zone_name,
    borough,
    is_airport,
    COUNT(*) AS trips,
    ROUND(SUM(total_amount), 2) AS revenue_including_charges_usd,
    ROUND(SUM(total_amount - tolls - surcharges), 2)
        AS revenue_excluding_charges_usd,
    ROUND(SUM(tolls), 2) AS tolls_usd,
    ROUND(SUM(surcharges), 2) AS surcharges_usd,
    ROUND(SUM(fare_amount), 2) AS fare_sum_usd,
    ROUND(AVG(fare_amount), 2) AS average_fare_usd,
    ROUND(SUM(trip_minutes), 2) AS total_trip_minutes,
    ROUND(AVG(trip_minutes), 2) AS average_duration_minutes,
    ROUND(
        SUM(trip_minutes) /
        (24.0 * DATE_DIFF('day', CAST(? AS DATE), CAST(? AS DATE))),
        2
    ) AS occupied_minutes_per_calendar_hour
FROM eligible
GROUP BY zone_id, zone_name, borough, is_airport
ORDER BY trips DESC, zone_id
"""


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DATABASE), read_only=True) as db:
        metrics = db.execute(METRICS_SQL, [START, END, START, END]).fetchdf()

    if metrics.empty:
        raise ValueError("No eligible trips found. Check the reporting dates.")

    for label, flag in [("airport", True), ("city", False)]:
        rows = metrics.loc[metrics["is_airport"] == flag].copy()
        path = OUTPUT / f"{label}_zone_metrics.csv"
        rows.to_csv(path, index=False)
        print(f"{label.upper()}: {len(rows)} zones, {rows['trips'].sum():,} trips")
        print(path)


if __name__ == "__main__":
    main()