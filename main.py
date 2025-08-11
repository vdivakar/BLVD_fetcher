from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import shutil

web = "https://verisresidential.com/jersey-city-nj-apartments/the-blvd-collection/"
chromedriver_path = shutil.which("chromedriver")  # Use chromedriver from PATH

# Add headless Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")  # Use new headless mode (Chrome 109+)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(web)
wait = WebDriverWait(driver, 10)


# Wait for and scroll to the "View All" button next to Availability
view_all_btn = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//p[contains(@class, 'prop-details-search-view-all') and contains(., 'View All')]")
    )
)
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_all_btn)
import time; time.sleep(0.5)  # Give time for overlays/animations to finish

try:
    view_all_btn.click()
except Exception:
    # Fallback: use JS click if intercepted
    driver.execute_script("arguments[0].click();", view_all_btn)


# Wait for the modal to appear
time.sleep(1)  # Adjust as necessary for the modal to load

All_1_BEDS = []
PROCESSED_1_BEDS = []
# Extract all rows in the overlay table
rows = driver.find_elements(By.CSS_SELECTOR, ".omg-results-card.bg-white")
for row in rows:
    try:
        # For mobile view, all info is in the first .omg-results-card-body-element with md:hidden
        mobile_info = row.find_elements(By.CSS_SELECTOR, ".omg-results-card-body-element.md\\:hidden")
        if False:
            # Extract text from each sub-element
            sub_elems = mobile_info[0].find_elements(By.CSS_SELECTOR, ".omg-results-card-body-element")
            floor_plan = sub_elems[0].text.replace("Floor Plan", "").strip() if len(sub_elems) > 0 else ""
            bed_bath = sub_elems[1].text.replace("Bedrooms", "").strip() if len(sub_elems) > 1 else ""
            price = sub_elems[2].text.replace("Price", "").strip() if len(sub_elems) > 2 else ""
            available = sub_elems[3].text.replace("Available", "").strip() if len(sub_elems) > 3 else ""
        else:
            # Desktop view: each field is in a separate .omg-results-card-body-element with md:block
            elems = row.find_elements(By.CSS_SELECTOR, ".omg-results-card-body-element.md\\:block")
            floor_plan = elems[0].text.strip() if len(elems) > 0 else ""
            bed_bath = elems[1].text.strip() if len(elems) > 1 else ""
            price = elems[2].text.strip() if len(elems) > 2 else ""
            # Available is sometimes in a nested element
            available = ""
            if len(elems) > 3:
                avail_elem = elems[3].find_elements(By.CSS_SELECTOR, ".omg-results-card-body-element")
                if avail_elem:
                    available = avail_elem[0].text.strip()
                else:
                    available = elems[3].text.strip()
        
        if "1 Bed / 1 Bath" in bed_bath:
            All_1_BEDS.append({
                "Floor Plan": floor_plan,
                "Bedrooms/Bath": bed_bath,
                "Price": price,
                "Available": available
            })

            # Click "View Details" button for this row
            try:
                view_details_btn = row.find_element(
                    By.CSS_SELECTOR,
                    ".display-floorplan-details"
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_details_btn)
                time.sleep(0.2)
                try:
                    view_details_btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", view_details_btn)
                # Wait for the new overlay/modal to appear
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, ".p-5.border-b-half.border-l-half.border-r-half.border-t-half")
                    )
                )
                time.sleep(1)  # Let animation finish
                
                ## Before extracting unit rows, let's extract the sq.ft. area of the layout
                sqft = ""
                try:
                    sqft_elem = driver.find_element(By.CSS_SELECTOR, ".takeover-sqft")
                    sqft = sqft_elem.text.strip()
                    print("SQFT:", sqft)
                except Exception:
                    print("SQFT not found")

                # Extract all unit rows in the overlay
                unit_rows = driver.find_elements(
                    By.CSS_SELECTOR,
                    ".p-5.border-b-half.border-l-half.border-r-half.border-t-half"
                )
                for unit in unit_rows:
                    try:
                        unit_labels = unit.find_elements(By.CSS_SELECTOR, ".basis-1\\/2 > div")
                        # The structure is: [Unit label, Unit value, Price label, Price value, Available label, Available value]
                        unit_val = unit_labels[1].text.strip() if len(unit_labels) > 1 else ""
                        price_val = unit_labels[3].text.strip() if len(unit_labels) > 3 else ""
                        avail_val = unit_labels[5].text.strip() if len(unit_labels) > 5 else ""
                        # Remove 'From $' prefix and commas from price
                        price_val = re.sub(r'^From \$|,', '', price_val).strip()

                        print({
                            "UNIT": unit_val,
                            "PRICE": price_val,
                            "AVAILABLE": avail_val,
                            "SQFT": sqft
                        })
                        PROCESSED_1_BEDS.append({
                            "Unit": unit_val,
                            "Price": price_val,
                            "Available": avail_val,
                            "SQFT": sqft
                        })
                        All_1_BEDS[-1].update({
                            "more_info": {
                                "Unit": unit_val,
                                "Price": price_val,
                                "Available": avail_val,
                                "SQFT": sqft
                            }
                        })
                    except Exception as e:
                        print("Error parsing unit row:", e)

                # Close the overlay/modal (only the current/topmost one)
                try:
                    # Find the close button inside the details modal only
                    close_btn = driver.find_element(By.CSS_SELECTOR, ".paoc-pro-close-popup.paoc-popup-close")
                    driver.execute_script("arguments[0].click();", close_btn)
                except Exception:
                    # Try pressing ESC as a fallback
                    from selenium.webdriver.common.keys import Keys
                    driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except Exception as e:
                print("Error clicking View Details or extracting unit info:", e)

        print({
            "Floor Plan": floor_plan,
            "Bedrooms/Bath": bed_bath,
            "Price": price,
            "Available": available
        })
    except Exception as e:
        print("Error parsing row:", e)

driver.quit()

print("All 1 Bed / 1 Bath entries:")
for entry in All_1_BEDS:
    print(entry)

for entry in PROCESSED_1_BEDS:
    print(entry)    

# Filter out units with "MN-" and "MS-" prefixes
PROCESSED_1_BEDS = [
    entry for entry in PROCESSED_1_BEDS
    if entry.get("Unit", "").startswith("M1-") or entry.get("Unit", "").startswith("M2-")
]

def unit_prefix_key(unit):
    if unit.startswith("M1-"):
        return 0
    elif unit.startswith("M2-"):
        return 1
    elif unit.startswith("MN-"):
        return 2
    elif unit.startswith("MS-"):
        return 3
    else:
        return 4

def parse_price(price):
    # Remove any non-digit or non-dot characters (e.g., '$', ',', 'From ')
    if not price:
        return float('inf')
    price = re.sub(r'[^\d.]', '', price)
    try:
        return float(price)
    except Exception:
        return float('inf')

# Sort by unit prefix, then by price (ascending)
PROCESSED_1_BEDS_SORTED = sorted(
    PROCESSED_1_BEDS,
    key=lambda x: (
        unit_prefix_key(x["Unit"]),
        parse_price(x["Price"])
    )
)

print("Sorted 1 Bed / 1 Bath entries:")
for entry in PROCESSED_1_BEDS_SORTED:
    print(entry)

# Save to .txt and .csv with datetime in filename
import csv
now_str = datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%d_%H%M%S")
txt_filename = f"processed_1_beds_{now_str}.txt"
csv_filename = f"processed_1_beds_{now_str}.csv"
with open(txt_filename, "w") as f:
    for entry in PROCESSED_1_BEDS_SORTED:
        f.write(str(entry) + "\n")

csv_fields = ["Unit", "Price", "Available", "SQFT"]
with open(csv_filename, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    for entry in PROCESSED_1_BEDS_SORTED:
        writer.writerow({field: entry.get(field, "") for field in csv_fields})


## TODO: clean the Price column - remove 'From $' prefix and commas
## TODO: sort by Price in ascending order