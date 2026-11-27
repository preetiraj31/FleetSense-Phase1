from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports" / "week3"

ANOMALY_SQL = """
WITH desk_hours AS (
    SELECT
        CAST(pickup_time AS TIMESTAMP) AS pickup_time,
        SUM(pickups)::BIGINT AS actual_pickups
    FROM read_csv_auto(?, header=true)
    GROUP BY 1
),
typical AS (
    SELECT
        *,
        MEDIAN(actual_pickups) OVER (
            PARTITION BY ISODOW(pickup_time), HOUR(pickup_time)
        ) AS typical_pickups
    FROM desk_hours
),
spread AS (
    SELECT
        *,
        MEDIAN(ABS(actual_pickups - typical_pickups)) OVER (
            PARTITION BY ISODOW(pickup_time), HOUR(pickup_time)
        ) AS mad
    FROM typical
),
limits AS (
    SELECT
        *,
        GREATEST(1.0, 3 * 1.4826 * mad) AS allowed_difference
    FROM spread
)
SELECT
    pickup_time,
    actual_pickups,
    typical_pickups,
    actual_pickups - typical_pickups AS difference,
    CASE
        WHEN actual_pickups > typical_pickups + allowed_difference THEN 'Spike'
        WHEN actual_pickups < typical_pickups - allowed_difference THEN 'Drop'
        ELSE 'Typical'
    END AS finding
FROM limits
ORDER BY pickup_time
"""


def main():
    with duckdb.connect() as db:
        for desk in ("airport", "city"):
            source = EXPORTS / f"{desk}_hourly_pickups.csv"
            target = EXPORTS / f"{desk}_hourly_review.csv"

            if not source.is_file():
                raise FileNotFoundError(f"Missing hourly export: {source}")

            review = db.execute(ANOMALY_SQL, [str(source)]).fetchdf()
            review.to_csv(target, index=False)

            spikes = int((review["finding"] == "Spike").sum())
            drops = int((review["finding"] == "Drop").sum())

            print(f"{desk.upper()}: {len(review):,} hours reviewed")
            print(f"  Spikes: {spikes} | Drops: {drops}")
            print(f"  Saved: {target}")


if __name__ == "__main__":
    main()