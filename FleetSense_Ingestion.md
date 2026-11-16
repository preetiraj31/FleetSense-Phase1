# FleetSense Data Ingestion Workflow

Phase 1 | Windows and VS Code

Load 12 consecutive months of NYC Yellow Taxi trips and the taxi zone lookup into DuckDB. On the second run, the same inputs must add zero rows. Verify this by comparing the stored counts for each of the 12 months.

## 1 Check Python 3.11

Open the FleetSense folder in VS Code and choose Terminal → New Terminal. Run this command to confirm that Python 3.11 is available.

```powershell
py -3.11 --version
```

## 2 Create the project environment

Run the first command separately. If it prints True, the terminal is in the folder containing requirements.txt. Then run the next two commands. The last command should print Python 3.11.x.

```powershell
Test-Path .\requirements.txt
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe --version
```

## 3 Install the packages and check DuckDB

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -c "import duckdb; print(duckdb.__version__)"
```

The import check should print 0.10.0 for the project’s pinned DuckDB version.

## 4 Verify that DuckDB can run SQL

```powershell
# Replace this example with your local repository path.
Set-Location 'C:\path\to\FleetSense-Phase1'
.\.venv\Scripts\python.exe -c "import duckdb; print(duckdb.__version__); print(duckdb.connect().execute('SELECT 42').fetchone())"
```

Expected output on separate lines is 0.10.0 followed by (42,). The query confirms DuckDB can execute SQL. Use your own project path if yours differs.

## 5 Download and store the input files

Download Yellow Taxi Trip Records (PARQUET) for September–December 2025 and January–August 2026. Download the Taxi Zone Lookup Table (CSV) from the same NYC TLC page. Keep the original filenames.

[Official NYC TLC trip data downloads](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

| **Project path**                 | **Contents**                                       |
|----------------------------------|----------------------------------------------------|
| data/raw/                        | 12 monthly .parquet files and taxi_zone_lookup.csv |
| src/ingest.py                    | The Python ingestion script                        |
| data/warehouse/fleetsense.duckdb | Database created when ingestion runs               |

Place `data/raw` at the project root alongside `requirements.txt`. If the files are under .venv/Data/raw, copy them into the project’s data/raw folder.

## 6 Check that all 13 files are visible

```powershell
Get-ChildItem .\data\raw -File | Select-Object Name
```

If the files are still inside .venv/Data/raw, create the project folder and copy them from there using the commands below. If you saved the files elsewhere, copy them from that location into data/raw.

```powershell
New-Item -ItemType Directory -Force .\data\raw
Copy-Item -Path .\.venv\Data\raw\*.parquet, `
    .\.venv\Data\raw\taxi_zone_lookup.csv -Destination .\data\raw
Get-ChildItem .\data\raw -File | Select-Object Name
```

Look for 12 Parquet filenames and taxi_zone_lookup.csv. Keep the exact names, for example yellow_tripdata_2025-09.parquet.

## Run and Check the Ingestion

### 7 Run the ingestion script

Save your ingestion script as src/ingest.py. List the inputs and run the script from the project folder.

```powershell
Get-ChildItem .\data\raw -File | Select-Object Name
.\.venv\Scripts\python.exe .\src\ingest.py
```

On a fresh database, confirm 13 LOADED messages, one for each month and the lookup. Save the terminal output. The script writes trip rows to raw_trips and lookup rows to dim_location.

### How duplicate loading is prevented

The ingestion_manifest table records each successfully loaded filename and a checksum, which is a fingerprint of its contents. The script commits the data and manifest entry in the same transaction. When it sees the same filename and checksum again, it skips that file. A changed checksum requires review before reloading.

### Record the first counts

Connect to the database and run the SQL below. Save the 12 filename and count pairs. The source_file column identifies the monthly file each trip came from.

```sql
SELECT source_file, COUNT(*) AS trip_rows
FROM raw_trips
GROUP BY source_file
ORDER BY source_file;

SELECT COUNT(*) AS zone_rows FROM dim_location;
SELECT COUNT(*) AS loaded_files FROM ingestion_manifest;
```

### Repeat the load and compare

Leave the source files and the database in place. Run the same ingestion command again. The expected summary is zero trip rows added, zero zone rows added, and 13 files skipped.

Run the same SQL and compare each filename and its count with the first result. The check passes when the same 12 expected filenames appear, every monthly trip count is unchanged, the zone count is unchanged, and the manifest still contains 13 entries.

## Terminal Output Examples

These examples are abridged. The monthly counts appear in the verification results below.

### First run on a fresh database

```text
LOADED: taxi_zone_lookup.csv (265 rows)
LOADED: yellow_tripdata_2025-09.parquet (4,251,015 rows)
...
Trip rows added: 46,869,519
Zone rows added: 265
Files skipped: 0
```

### Second run with unchanged files

```text
Trip rows added: 0
Zone rows added: 0
Files skipped: 13
```

### Client reporting requirements

The raw load preserves pickup timestamps and zone IDs. Later reporting must show airport and city figures separately in every chart and table, with holiday-week forecast accuracy reported separately from normal-week accuracy.

## Record the Verification Results

Stored rows after each run. First-run counts come from the ingestion log. Second-run counts are inferred from the unchanged files and zero rows added.

| **Month or table** | **First run rows** | **Second run rows** | **Change** |
|--------------------|--------------------|---------------------|------------|
| 2025-09            | 4,251,015          | 4,251,015           | 0          |
| 2025-10            | 4,428,699          | 4,428,699           | 0          |
| 2025-11            | 4,181,444          | 4,181,444           | 0          |
| 2025-12            | 4,305,006          | 4,305,006           | 0          |
| 2026-01            | 3,724,889          | 3,724,889           | 0          |
| 2026-02            | 3,399,866          | 3,399,866           | 0          |
| 2026-03            | 3,952,451          | 3,952,451           | 0          |
| 2026-04            | 3,831,240          | 3,831,240           | 0          |
| 2026-05            | 4,090,836\*        | 4,090,836\*         | 0          |
| 2026-06            | 3,837,248          | 3,837,248           | 0          |
| 2026-07            | 3,530,109          | 3,530,109           | 0          |
| 2026-08            | 3,336,716          | 3,336,716           | 0          |
| Zone lookup        | 265                | 265                 | 0          |
| Manifest entries   | 13                 | 13                  | 0          |

\* May 2026 was missing from the pasted first-run lines. Its count is the reported trip total minus the other 11 monthly counts.

All months combined: 46,869,519 trip rows after the first run. The second run added zero trip and zone rows and skipped all 13 files.

Run the direct DuckDB check in the [PowerShell verification section](#verification-commands-for-powershell) to confirm the stored counts. The terminal log alone does not include that check.

## Verification Commands for PowerShell

After the first load, paste this block into the VS Code PowerShell terminal. It reads the stored counts, runs ingestion again, and compares the results. The PASS line is generated only after all checks succeed.

```powershell
$query = @'
import duckdb

with duckdb.connect("data/warehouse/fleetsense.duckdb", read_only=True) as db:
    trips = db.execute("""
        SELECT source_file, COUNT(*)
        FROM raw_trips
        GROUP BY source_file
        ORDER BY source_file
    """).fetchall()
    months = [f"2025-{m:02}" for m in range(9, 13)]
    months += [f"2026-{m:02}" for m in range(1, 9)]
    assert [name for name, count in trips] == [
        f"yellow_tripdata_{month}.parquet" for month in months
    ], "Expected all 12 monthly files"
    for name, count in trips:
        print(f"{name}: {count}")
    zones = db.execute("SELECT COUNT(*) FROM dim_location").fetchone()[0]
    files = db.execute("SELECT COUNT(*) FROM ingestion_manifest").fetchone()[0]
    assert zones > 0 and files == 13, "Expected zones and 13 loaded files"
    print(f"Zone rows: {zones}")
    print(f"Manifest entries: {files}")
'@
$before = $query | .\.venv\Scripts\python.exe -
if ($LASTEXITCODE -ne 0) { throw "First count check failed" }
$before
.\.venv\Scripts\python.exe .\src\ingest.py
if ($LASTEXITCODE -ne 0) { throw "Repeat ingestion failed" }
$after = $query | .\.venv\Scripts\python.exe -
if ($LASTEXITCODE -ne 0) { throw "Second count check failed" }
$after
if (Compare-Object $before $after) { throw "Stored counts changed" }
Write-Host "PASS: All 12 monthly counts and lookup count are unchanged."
```

### If a step fails

For a missing file, check its exact name and location in data/raw. For a DuckDB DLL error on 64-bit Python, install or repair the Microsoft Visual C++ x64 Redistributable, then rerun the import check. If ingestion fails partway through, fix the reported issue and retry with the same database.
