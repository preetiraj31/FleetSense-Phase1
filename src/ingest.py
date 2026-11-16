import hashlib
from pathlib import Path

import duckdb


PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "data" / "raw"
DATABASE = PROJECT / "data" / "warehouse" / "fleetsense.duckdb"

MONTHS = [
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
]

TRIP_COLUMNS = {
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "pulocationid",
    "dolocationid",
}


def file_checksum(path):
    # Read in chunks so a large file does not have to fit in memory.
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def check_trip_columns(db, path):
    columns = db.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)",
        [str(path)],
    ).fetchall()
    missing = TRIP_COLUMNS - {row[0].lower() for row in columns}
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")


def main():
    zone_file = RAW / "taxi_zone_lookup.csv"
    trip_files = [
        RAW / f"yellow_tripdata_{month}.parquet" for month in MONTHS
    ]
    sources = [zone_file, *trip_files]
    missing = [str(path) for path in sources if not path.is_file()]

    if missing:
        raise SystemExit("Missing input files:\n" + "\n".join(missing))

    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(DATABASE))
    added_trips = 0
    added_zones = 0
    skipped = 0

    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_manifest (
                filename VARCHAR PRIMARY KEY,
                checksum VARCHAR NOT NULL,
                rows_loaded BIGINT NOT NULL
            )
            """
        )

        pending = []
        for path in sources:
            checksum = file_checksum(path)
            previous = db.execute(
                "SELECT checksum FROM ingestion_manifest WHERE filename = ?",
                [path.name],
            ).fetchone()

            if previous is None:
                pending.append((path, checksum))
            elif previous[0] == checksum:
                print(f"SKIPPED: {path.name}")
                skipped += 1
            else:
                raise ValueError(
                    f"{path.name} changed after it was loaded. "
                    "Check the file before reloading it."
                )

        # Check the columns in each month before loading any new files.
        for path, _ in pending:
            if path != zone_file:
                check_trip_columns(db, path)

        for path, checksum in pending:
            db.execute("BEGIN TRANSACTION")
            try:
                if path == zone_file:
                    db.execute(
                        """
                        CREATE TABLE IF NOT EXISTS dim_location (
                            LocationID INTEGER PRIMARY KEY,
                            Borough VARCHAR,
                            Zone VARCHAR,
                            service_zone VARCHAR
                        )
                        """
                    )
                    db.execute(
                        """
                        INSERT INTO dim_location
                        SELECT CAST(LocationID AS INTEGER),
                               Borough, Zone, service_zone
                        FROM read_csv_auto(?, header = true)
                        """,
                        [str(path)],
                    )
                    rows = db.execute(
                        "SELECT COUNT(*) FROM dim_location"
                    ).fetchone()[0]
                else:
                    # Set up the table using the columns across all 12 months.
                    db.execute(
                        """
                        CREATE TABLE IF NOT EXISTS raw_trips AS
                        SELECT *, CAST(NULL AS VARCHAR) AS source_file
                        FROM read_parquet(?, union_by_name = true)
                        LIMIT 0
                        """,
                        [[str(file) for file in trip_files]],
                    )
                    db.execute(
                        """
                        INSERT INTO raw_trips BY NAME
                        SELECT *, CAST(? AS VARCHAR) AS source_file
                        FROM read_parquet(?)
                        """,
                        [path.name, str(path)],
                    )
                    rows = db.execute(
                        """
                        SELECT COUNT(*)
                        FROM raw_trips
                        WHERE source_file = ?
                        """,
                        [path.name],
                    ).fetchone()[0]

                db.execute(
                    """
                    INSERT INTO ingestion_manifest
                    VALUES (?, ?, ?)
                    """,
                    [path.name, checksum, rows],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

            if path == zone_file:
                added_zones += rows
            else:
                added_trips += rows

            print(f"LOADED: {path.name} ({rows:,} rows)")

        print(f"\nTrip rows added: {added_trips:,}")
        print(f"Zone rows added: {added_zones:,}")
        print(f"Files skipped: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
