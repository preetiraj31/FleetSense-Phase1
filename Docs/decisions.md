# FleetSense Analytical Decision Log

This log tracks all major analytical decisions, metric definitions, and filters applied by the Analyst, as required by the FleetSense engineering standards.

## Decision 001: Defining "Holiday Weeks" for Airport Desk Client
* **Context:** The Airport Desk client (Renata Okonkwo-Hale) requested accuracy reporting for "holiday weeks on their own," separated from normal weeks.
* **Decision:** A "holiday week" is analytically defined as the Monday through Sunday (ISO week) that contains a major US public holiday (e.g., Thanksgiving, Christmas, New Year's Day, Independence Day).
* **Impact:** Any forecasting metrics falling within these specific ISO weeks will be filtered into a separate evaluation bucket and displayed on the dedicated Holiday Week tab in the dashboard.

## Decision 002: Categorizing Airport vs. City Zones
* **Context:** The client requires airport and city numbers to be kept apart in every chart and table.
* **Decision:** We will use the official NYC TLC Taxi Zone Lookup CSV to categorize zones. Any `PULocationID` (Pickup Location ID) mapped to the `zone_name` of 'JFK Airport', 'LaGuardia Airport', or 'Newark Airport' will be strictly flagged as `is_airport = True`. All other valid zones will be `is_airport = False`.
* **Impact:** This boolean flag will be used in DuckDB SQL queries to partition the data for the Streamlit dashboard views.