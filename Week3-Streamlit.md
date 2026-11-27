# FleetSense | Week 3 dispatch dashboard
**Implementation and review handoff · 27 November 2026**

## 1. Git submission scope
Base the contribution on main. Commit the active Week 3 metrics exporter, hourly aggregation, anomaly analysis, dashboard, dependency pins and project documentation. Include a compatibility entry point only if used. Exclude raw Parquet, warehouse files, generated CSVs, virtual environments, backups and secrets. The remote main at 94bde6e contains the baseline metrics module from PR #5. Its total_trips, total_revenue, average_fare, average_duration and utilisation_proxy functions are existing interfaces. Review their callers before replacing the module. If the local Week 3 exporter is still week3_metrics.py, it can be submitted alongside the baseline without renaming.

## 2. Purpose and scope
Renata’s dispatch desk needs hourly pickup patterns for airport and city zones. The Week 3 dashboard implements historical seasonality, revenue, active-zone rankings and anomaly review. Each selection reads data for one desk. Hourly forecasts and holiday-week backtesting are subsequent deliverables.

## 3. What changed after the baseline
| Component | Responsibility |
|---|---|
| src/week3_metrics.py, or src/metrics.py after local integration | Opens the warehouse read-only. Joins raw_trips.PULocationID to dim_zones.zone_id to access the airport flag and individual trip charges. Exports one zone metrics CSV per desk. |
| src/weekly_hourly.py | Uses the same eligibility rules. Counts by pickup zone and local clock hour, fills the reporting grid with zeros and reconciles hourly sums against each zone export. |
| src/week3_anomalies.py | Sums zone pickups to desk-hour, computes weekday/hour medians, flags spikes and drops, and exports one hourly review file per desk. |
| dashboard.py | Adds desk and report selectors, seasonal profiles, CR-1 comparison, rankings and anomaly review. |
| requirements.txt | Uses the existing Streamlit and DuckDB stack. The Windows environment fix pins numpy==1.26.4 and pyarrow==15.0.2. The dashboard also imports pandas and Altair. |
| Docs/decisions.md | Records the review method, observed events, handling and any unresolved causes. |

## 4. How the connection works
1. The exporter resolves the project root from the script location and opens data/warehouse/fleetsense.duckdb with duckdb.connect(str(database), read_only=True).
2. It writes airport_zone_metrics.csv and city_zone_metrics.csv into data/exports/week3. The hourly job writes airport_hourly_pickups.csv and city_hourly_pickups.csv there. The anomaly job reads those hourly files and writes airport_hourly_review.csv and city_hourly_review.csv.
3. Streamlit maps the selected desk to an airport or city filename prefix. The seasonality page uses an in-memory DuckDB connection to query the selected CSV with read_csv_auto and passes the summary into charts. Pandas reads the smaller revenue and anomaly exports. Altair draws the actual, typical and flagged observations.
4. The browser connects to the local Streamlit server. The dashboard reads exported snapshots; rerun the relevant exporters after a warehouse update. File modification time is an input to the cached seasonal query.

## 5. Metric definitions and changes in meaning
Period: 1 September 2025 through 31 August 2026. Eligible pickups have a mapped pickup zone, a valid trip chronology, nonnegative fare and total, and a zone ID other than 264 or 265.

| Measure | Week 3 definition |
|---|---|
| Trips | Count eligible rows by pickup zone. |
| Inclusive revenue | Sum TLC total_amount in USD. |
| CR-1 exclusive revenue | At trip level subtract tolls_amount, extra, improvement_surcharge, congestion_surcharge, Airport_fee and cbd_congestion_fee. Null charge components contribute zero. Tips and MTA tax remain included. |
| Average fare | Sum base fare divided by eligible trips. |
| Average duration | Average trip elapsed seconds divided by 60. |
| Utilisation proxy | Total occupied trip-minutes divided by 8,760 calendar hours. The baseline module used cumulative active hours with a duration filter; the two measures have different units. |

## 6. Running in VS Code on Windows
Use the project folder containing dashboard.py as the terminal working directory. With an existing environment:
~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\src\week3_metrics.py
.\.venv\Scripts\python.exe .\src\weekly_hourly.py
.\.venv\Scripts\python.exe .\src\week3_anomalies.py
.\.venv\Scripts\python.exe -m streamlit run .\dashboard.py
~~~
If the active exporter has moved to src/metrics.py and there is no compatibility wrapper, substitute that filename in the second command. The original baseline module on main is not the exporter. If all six CSVs exist, start at the Streamlit launch command. Open the Local URL printed by Streamlit.

## 7. What reviewers should see
- Seasonality: hour-of-day bars, weekday bars in calendar order, and chronological monthly demand.
- Revenue and rankings: inclusive/exclusive charge comparison per selected zone, all-zone detail and busiest/quietest active-zone rankings. Zone eligibility determines which zones can appear in the bottom ranking.
- Anomalies: monthly review of actual desk-hour totals against the full-period median for that desk, weekday and hour. Flag an absolute deviation greater than max(1 pickup, 3 × 1.4826 × median absolute deviation). Retain the observed pickups. The method is retrospective.
- CR-1 impact: new trip-level expressions, per-zone exports, dashboard comparison and documentation. Prior planning estimate: 1–2 engineer days including review. Main risk is disagreement over excluded charges. Reconcile inclusive minus exclusive against tolls plus surcharges per zone with up to USD 0.02 rounding tolerance.

## 8. Evidence and outstanding review
Airport export: 3 active zones and 3,010,262 eligible trips. City export: 257 active zones and 42,596,015 eligible trips. The local hourly exporter reported matching per-zone counts for both desks. The user confirmed both anomaly views worked. The City September 2025 screenshot showed six spikes and four drops. Record actual event timestamps, actual/typical counts and handling separately for Airport and City in the decision log. Neither a warehouse rerun here nor a completed CR-1 reconciliation is claimed. No live deployment or forecast-accuracy result is claimed.
