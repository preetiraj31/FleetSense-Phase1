from pathlib import Path

import duckdb

from week3_metrics import DATABASE, END, OUTPUT, START


def sql_path(path: Path) -> str:
    return "'" + path.as_posix().replace("'", "''") + "'"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DATABASE), read_only=True) as db:
        # Use the same trip eligibility rules as week3_metrics.py.
        db.execute("""
            CREATE TEMP TABLE pickup_counts AS
            SELECT
                z.zone_id,
                DATE_TRUNC('hour', r.tpep_pickup_datetime) AS pickup_time,
                COUNT(*) AS pickups
            FROM raw_trips AS r
            JOIN dim_zones AS z ON r.PULocationID = z.zone_id
            WHERE r.tpep_pickup_datetime >= CAST(? AS DATE)
              AND r.tpep_pickup_datetime < CAST(? AS DATE)
              AND r.tpep_dropoff_datetime >= r.tpep_pickup_datetime
              AND r.fare_amount >= 0
              AND r.total_amount >= 0
              AND z.zone_id NOT IN (264, 265)
            GROUP BY z.zone_id, DATE_TRUNC('hour', r.tpep_pickup_datetime)
        """, [START, END])

        db.execute("""
            CREATE TEMP TABLE reporting_hours AS
            SELECT pickup_time
            FROM generate_series(
                CAST(? AS TIMESTAMP),
                CAST(? AS TIMESTAMP) - INTERVAL '1 hour',
                INTERVAL '1 hour'
            ) AS hours(pickup_time)
        """, [START, END])

        for segment, is_airport in [("airport", True), ("city", False)]:
            # Reconcile every zone against the CSV you already generated.
            previous = sql_path(OUTPUT / f"{segment}_zone_metrics.csv")
            mismatches = db.execute(f"""
                WITH hourly_totals AS (
                    SELECT c.zone_id, SUM(c.pickups) AS trips
                    FROM pickup_counts AS c
                    JOIN dim_zones AS z USING (zone_id)
                    WHERE z.is_airport = ?
                    GROUP BY c.zone_id
                )
                SELECT COUNT(*)
                FROM hourly_totals AS h
                FULL OUTER JOIN read_csv_auto({previous}, header=true) AS p
                    ON h.zone_id = p.zone_id
                WHERE h.trips IS DISTINCT FROM p.trips
            """, [is_airport]).fetchone()[0]

            if mismatches:
                raise ValueError(f"{segment}: {mismatches} zone totals differ.")

            # Include every mapped zone, even one with zero trips all year.
            flag = "TRUE" if is_airport else "FALSE"
            output = OUTPUT / f"{segment}_hourly_pickups.csv"
            db.execute(f"""
                COPY (
                    SELECT
                        z.zone_id,
                        z.zone_name,
                        h.pickup_time,
                        CAST(h.pickup_time AS DATE) AS pickup_date,
                        HOUR(h.pickup_time) AS hour_of_day,
                        ISODOW(h.pickup_time) AS weekday_number,
                        DAYNAME(h.pickup_time) AS weekday_name,
                        CAST(DATE_TRUNC('month', h.pickup_time) AS DATE)
                            AS month_start,
                        COALESCE(c.pickups, 0) AS pickups
                    FROM dim_zones AS z
                    CROSS JOIN reporting_hours AS h
                    LEFT JOIN pickup_counts AS c
                        ON c.zone_id = z.zone_id
                       AND c.pickup_time = h.pickup_time
                    WHERE z.is_airport = {flag}
                      AND z.zone_id NOT IN (264, 265)
                    ORDER BY z.zone_id, h.pickup_time
                ) TO {sql_path(output)} (HEADER, DELIMITER ',')
            """)
            print(f"{segment.upper()}: zone totals match. Created {output.name}")


if __name__ == "__main__":
    main()