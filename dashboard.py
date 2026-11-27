from pathlib import Path

import duckdb
import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
EXPORTS = ROOT / "data" / "exports" / "week3"

st.set_page_config(page_title="FleetSense Operations", layout="wide")
st.title("FleetSense | Dispatch Operations")

desk = st.sidebar.radio("Dispatch desk", ["Airport", "City"])
view = st.sidebar.radio("Report", ["Seasonality", "Revenue and rankings", "Hourly anomalies"])
prefix = desk.lower()

st.header(f"{desk} — {view}")
st.caption("September 2025 through August 2026")


def export_file(suffix):
    path = EXPORTS / f"{prefix}_{suffix}.csv"
    if not path.is_file():
        st.error(f"Missing file: {path}")
        st.stop()
    return path


@st.cache_data
def load_profile(filename, modified_time):
    # DuckDB summarises the hourly CSV before the data reaches the browser.
    # The modification time refreshes the cache when you rebuild an export.
    with duckdb.connect() as db:
        return db.execute("""
            SELECT hour_of_day, weekday_number, month_start,
                   SUM(pickups) AS pickups
            FROM read_csv_auto(?)
            GROUP BY hour_of_day, weekday_number, month_start
        """, [filename]).fetchdf()


if view == "Seasonality":
    path = export_file("hourly_pickups")
    data = load_profile(str(path), path.stat().st_mtime_ns)

    st.metric("Total pickups", f"{int(data['pickups'].sum()):,}")

    left, right = st.columns(2)

    with left:
        st.subheader("Pickups by hour")
        hourly = data.groupby("hour_of_day")["pickups"].sum().sort_index()
        st.bar_chart(hourly)

    with right:
        st.subheader("Pickups by weekday")
        weekday = data.groupby("weekday_number")["pickups"].sum()
        weekday = weekday.reindex(range(1, 8), fill_value=0)
        weekday.index = [
            "1 Mon", "2 Tue", "3 Wed", "4 Thu", "5 Fri", "6 Sat", "7 Sun"
        ]
        st.bar_chart(weekday)

    st.subheader("Monthly pickup trend")
    monthly = data.groupby("month_start")["pickups"].sum().sort_index()
    st.line_chart(monthly)

elif view == "Hourly anomalies":
    path = export_file("hourly_review")
    review = pd.read_csv(path, parse_dates=["pickup_time"])
    review["month"] = review["pickup_time"].dt.strftime("%Y-%m")

    month = st.selectbox("Review month", sorted(review["month"].unique()))
    selected = review[review["month"] == month]
    flagged = selected[selected["finding"] != "Typical"]

    left, right = st.columns(2)
    left.metric("Flagged spikes", int((flagged["finding"] == "Spike").sum()))
    right.metric("Flagged drops", int((flagged["finding"] == "Drop").sum()))

    st.subheader(f"{desk} hourly pickups — {month}")
    st.caption("Blue shows actual pickups. The dashed line shows typical pickups "
               "for the same weekday and hour. Hover over a flagged point for details.")

    base = alt.Chart(selected).encode(
        x=alt.X("pickup_time:T", title="Pickup time")
    )
    actual = base.mark_line(color="#2563eb").encode(
        y=alt.Y("actual_pickups:Q", title="Pickups")
    )
    typical = base.mark_line(color="#666666", strokeDash=[5, 4]).encode(
        y="typical_pickups:Q"
    )
    points = alt.Chart(flagged).mark_circle(size=75).encode(
        x="pickup_time:T",
        y="actual_pickups:Q",
        color=alt.Color("finding:N", title="Finding"),
        tooltip=[
            alt.Tooltip("pickup_time:T", title="Hour", format="%Y-%m-%d %H:%M"),
            "finding:N",
            "actual_pickups:Q",
            "typical_pickups:Q",
            "difference:Q",
        ],
    )
    st.altair_chart(actual + typical + points, use_container_width=True)

    st.subheader("Flagged hours for the decision log")
    st.dataframe(
        flagged[["pickup_time", "finding", "actual_pickups",
                 "typical_pickups", "difference"]],
        hide_index=True,
        use_container_width=True,
    )
else:
    path = export_file("zone_metrics")
    zones = pd.read_csv(path)
    trips = int(zones["trips"].sum())

    if trips == 0:
        st.info("No eligible trips for this desk.")
        st.stop()

    included = "revenue_including_charges_usd"
    excluded = "revenue_excluding_charges_usd"

    first, second, third = st.columns(3)
    first.metric("Eligible trips", f"{trips:,}")
    second.metric("Revenue including charges", f"${zones[included].sum():,.2f}")
    third.metric("Revenue excluding charges", f"${zones[excluded].sum():,.2f}")

    first, second, third = st.columns(3)
    first.metric("Average fare", f"${zones['fare_sum_usd'].sum() / trips:,.2f}")
    second.metric(
        "Average duration",
        f"{zones['total_trip_minutes'].sum() / trips:,.1f} min",
    )
    # The exports cover 365 calendar days from Sep 2025 through Aug 2026.
    third.metric(
        "Occupied minutes per calendar hour",
        f"{zones['total_trip_minutes'].sum() / (365 * 24):,.1f}",
    )

    st.subheader("CR-1 | Revenue by pickup zone")
    zone_names = zones.set_index("zone_id")["zone_name"].to_dict()
    selected_id = st.selectbox(
        "Choose a pickup zone",
        options=zones["zone_id"].tolist(),
        format_func=lambda zone_id: f"{zone_names[zone_id]} ({zone_id})",
    )
    selected = zones.loc[zones["zone_id"] == selected_id].iloc[0]

    comparison = pd.Series({
        "Including tolls and surcharges": selected[included],
        "Excluding tolls and surcharges": selected[excluded],
    }, name="Revenue (USD)")
    st.bar_chart(comparison)

    st.subheader("Zone rankings by pickups")
    direction = st.radio("Show zones", ["Busiest", "Quietest"], horizontal=True)
    ranked = zones.sort_values(
        ["trips", "zone_id"],
        ascending=[direction == "Quietest", True],
    ).head(10)

    # Number the labels so the chart preserves the ranking order.
    chart = ranked.copy()
    chart["ranked_zone"] = [
        f"{rank:02d}  {name}"
        for rank, name in enumerate(chart["zone_name"], start=1)
    ]
    st.bar_chart(chart.set_index("ranked_zone")["trips"])
    st.caption("Rankings include zones with at least one eligible pickup.")

    with st.expander(f"View revenue and trips for all {desk.lower()} zones"):
        st.dataframe(
            zones[["zone_id", "zone_name", "trips", included, excluded]],
            hide_index=True,
            use_container_width=True,
        )