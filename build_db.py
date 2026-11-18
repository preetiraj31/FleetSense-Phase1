import duckdb

conn = duckdb.connect("data/warehouse/fleetsense.duckdb")

conn.execute("""
CREATE OR REPLACE TABLE dim_location AS
SELECT *
FROM read_csv_auto('data/warehouse/taxi_zone_lookup.csv');
""")

conn.execute("""
CREATE OR REPLACE TABLE raw_trips AS
SELECT *
FROM read_parquet('data/warehouse/yellow_tripdata_*.parquet');
""")

conn.close()

print("Database created successfully!")