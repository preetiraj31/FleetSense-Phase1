import duckdb

con = duckdb.connect("data/warehouse/fleetsense.duckdb", read_only=True)


def _airport_filter(is_airport: bool | None) -> str:
    if is_airport is True:
        return "AND z.is_airport = TRUE"
    if is_airport is False:
        return "AND z.is_airport = FALSE"
    return ""


def total_trips(is_airport: bool | None = None):
    return con.execute(f"""
        SELECT COUNT(*)
        FROM fact_trips f
        JOIN dim_zones z ON f.pickup_zone_id = z.zone_id
        WHERE 1=1 {_airport_filter(is_airport)}
    """).fetchone()[0]


def total_revenue(is_airport: bool | None = None):
    return con.execute(f"""
        SELECT ROUND(SUM(f.total_amount), 2)
        FROM fact_trips f
        JOIN dim_zones z ON f.pickup_zone_id = z.zone_id
        WHERE 1=1 {_airport_filter(is_airport)}
    """).fetchone()[0]


def average_fare(is_airport: bool | None = None):
    return con.execute(f"""
        SELECT ROUND(AVG(f.fare_amount), 2)
        FROM fact_trips f
        JOIN dim_zones z ON f.pickup_zone_id = z.zone_id
        WHERE 1=1 {_airport_filter(is_airport)}
    """).fetchone()[0]


def average_duration(is_airport: bool | None = None):
    return con.execute(f"""
        SELECT ROUND(AVG(f.trip_duration_min), 2)
        FROM fact_trips f
        JOIN dim_zones z ON f.pickup_zone_id = z.zone_id
        WHERE f.trip_duration_min > 0 AND f.trip_duration_min < 360
        {_airport_filter(is_airport)}
    """).fetchone()[0]


def utilisation_proxy(is_airport: bool | None = None):
    """Total active fleet hours (sum of trip durations in hours)."""
    return con.execute(f"""
        SELECT ROUND(SUM(f.trip_duration_min) / 60.0, 2)
        FROM fact_trips f
        JOIN dim_zones z ON f.pickup_zone_id = z.zone_id
        WHERE f.trip_duration_min > 0 AND f.trip_duration_min < 360
        {_airport_filter(is_airport)}
    """).fetchone()[0]


if __name__ == "__main__":
    for label, flag in [("Airport", True), ("City", False)]:
        print(f"--- {label} ---")
        print("Total Trips:", total_trips(flag))
        print("Total Revenue:", total_revenue(flag))
        print("Average Fare:", average_fare(flag))
        print("Average Duration (min):", average_duration(flag))
        print("Utilisation Proxy (hrs):", utilisation_proxy(flag))