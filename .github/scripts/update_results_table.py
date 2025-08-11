import os
import glob
import datetime
import csv

# Find the latest processed_1_beds_*.csv file
csv_files = glob.glob("processed_1_beds_*.csv")
if not csv_files:
    raise FileNotFoundError("No processed_1_beds_*.csv files found.")
latest_csv = max(csv_files, key=os.path.getmtime)

# Extract timestamp from filename
basename = os.path.basename(latest_csv)
date_str = basename.replace("processed_1_beds_", "").replace(".csv", "")
dt = datetime.datetime.strptime(date_str, "%Y%m%d_%H%M%S")

# Read CSV content
with open(latest_csv, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Prepare improved markdown table rows
header = "| Date & Time | Unit | Price | Available | SQFT |\n|---|---|---|---|---|\n"
results_path = 'results.md'

# Sort rows by Unit to ensure M1s come before M2s
rows_sorted = sorted(rows, key=lambda r: r['Unit'])


# Only show Date & Time in the first row, blank for the rest
table_rows = []
m2_divider_inserted = False
first_row = True
for r in rows_sorted:
    # Insert divider before first M2 unit
    if not m2_divider_inserted and r['Unit'].startswith('M2'):
        table_rows.append('|---|---|---|---|---|')
        m2_divider_inserted = True
    date_cell = dt.strftime('%Y-%m-%d %H:%M:%S') if first_row else ''
    table_rows.append(f"| {date_cell} | {r['Unit']} | {r['Price']} | {r['Available']} | {r['SQFT']} |")
    first_row = False

# Read existing content (if any), but remove old table rows for this timestamp
if os.path.exists(results_path):
    with open(results_path, 'r') as f:
        content = f.read()
    # Remove any rows with this timestamp to avoid duplicates
    lines = content.split('\n')
    lines = [line for line in lines if dt.strftime('%Y-%m-%d %H:%M:%S') not in line and not (line.strip() == '|---|---|---|---|---|')]
    # Remove old header if present
    if lines and lines[0].startswith('| Date & Time'):
        lines = lines[2:]  # remove header and divider
else:
    lines = []

# Compose new content
content = header + '\n'.join(table_rows) + '\n'
if lines:
    content += '\n' + '\n'.join(lines).strip() + '\n'

with open(results_path, 'w') as f:
    f.write(content)
