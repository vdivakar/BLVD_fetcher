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
date_stamp = dt.strftime('%Y-%m-%d %H:%M:%S')

# Read CSV content
with open(latest_csv, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Prepare markdown table rows for the new results
header = "| Date & Time | Unit | Price | Available | SQFT |\n|---|---|---|---|---|"

table_rows = []
m2_divider_inserted = False
first_row = True
for r in rows:
    # Insert divider before first M2 unit
    if not m2_divider_inserted and r['Unit'].startswith('M2'):
        table_rows.append('|---|---|---|---|---|')
        m2_divider_inserted = True
    date_cell = date_stamp if first_row else ''
    table_rows.append(f"| {date_cell} | {r['Unit']} | {r['Price']} | {r['Available']} | {r['SQFT']} |")
    first_row = False

new_result_block = header + '\n' + '\n'.join(table_rows)

results_path = 'results.md'

# Read existing content and split into blocks
if os.path.exists(results_path):
    with open(results_path, 'r') as f:
        content = f.read()
    # Split into blocks by header line
    blocks = content.split(header)
    # Remove any blocks that contain the current timestamp (to avoid duplicates)
    blocks = [b for b in blocks if date_stamp not in b]
    # Remove empty blocks
    blocks = [b.strip('\n') for b in blocks if b.strip('\n')]
else:
    blocks = []

# Compose new content: new results first, then previous blocks
all_blocks = [new_result_block] + [header + '\n' + b for b in blocks]
final_content = '\n\n'.join(all_blocks) + '\n'

with open(results_path, 'w') as f:
    f.write(final_content)
