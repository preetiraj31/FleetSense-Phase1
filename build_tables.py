import duckdb

conn = duckdb.connect("data/warehouse/fleetsense.duckdb")

# Order matters: hourly_demand depends on fact_trips
for name in ["dim_zones", "dim_calendar", "fact_trips", "hourly_demand"]:
    print(f"Building {name}...")
    conn.execute(open(f"sql/{name}.sql").read())

conn.close()
print("All tables built successfully!")