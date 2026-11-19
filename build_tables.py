import duckdb

# conn = duckdb.connect("data/warehouse/fleetsense.duckdb")
DB_PATH = "data/warehouse/fleetsense.duckdb"
SQL_PATH = "sql/build_warehouse.sql"
with open(SQL_PATH, "r") as f:
    sql_script = f.read()
with duckdb.connect(DB_PATH) as conn:
    conn.execute(sql_script)
    tables = conn.execute("SHOW TABLES").fetchall()
    print("Tables in warehouse:", [t[0] for t in tables])
    # Order matters: hourly_demand depends on fact_trips
# for name in ["dim_zones", "dim_calendar", "fact_trips", "hourly_demand"]:
#     print(f"Building {name}...")
#     conn.execute(open(f"sql/{name}.sql").read())

# conn.close()
# print("All tables built successfully!")
