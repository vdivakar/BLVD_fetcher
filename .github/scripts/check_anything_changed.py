import re

def extract_tables(md_path, num_tables=2):
    with open(md_path, 'r') as f:
        content = f.read()
    # Split by table header
    tables = content.split('| Date & Time | Unit | Price | Available | SQFT |')
    # Remove empty splits and re-add header
    tables = [('| Date & Time | Unit | Price | Available | SQFT |' + t).strip() for t in tables if t.strip()]
    # Get the latest num_tables tables
    return tables[:num_tables]

def parse_table(table):
    rows = []
    for line in table.splitlines():
        if line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.strip('|').split('|')]
            # Skip header or empty lines
            if parts[0] == 'Date & Time' or all(not p for p in parts):
                continue
            # Use Unit as unique key
            row = {
                'unit': parts[1],
                'price': parts[2],
                'available': parts[3],
                'sqft': parts[4]
            }
            rows.append(row)
    return rows

def compare_tables(latest, previous):
    latest_units = {row['unit']: row for row in latest}
    prev_units = {row['unit']: row for row in previous}

    # 1. New additions
    new_units = set(latest_units) - set(prev_units)
    # 2. Removals
    removed_units = set(prev_units) - set(latest_units)
    # 3. Price changes
    price_changes = []
    for unit in set(latest_units) & set(prev_units):
        if latest_units[unit]['price'] != prev_units[unit]['price']:
            price_changes.append({
                'unit': unit,
                'old_price': prev_units[unit]['price'],
                'new_price': latest_units[unit]['price']
            })

    return new_units, removed_units, price_changes

if __name__ == "__main__":
    tables = extract_tables('results.md', 2)
    if len(tables) < 2:
        print("Not enough tables to compare.")
        exit(1)
    latest_rows = parse_table(tables[0])
    prev_rows = parse_table(tables[1])
    new_units, removed_units, price_changes = compare_tables(latest_rows, prev_rows)

    print("New additions:", new_units)
    print("Removals:", removed_units)
    print("Price changes:", price_changes)

    if new_units or removed_units or price_changes:
        with open("change_summary.txt", "w") as f:
            if new_units:
                f.write(f"New additions: {new_units}\n")
            if removed_units:
                f.write(f"Removals: {removed_units}\n")
            if price_changes:
                f.write(f"Price changes: {price_changes}\n")