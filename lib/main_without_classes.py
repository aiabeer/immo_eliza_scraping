import requests
import csv
import re
import os
from bs4 import BeautifulSoup

base_url = "https://immovlan.be/en/real-estate?transactiontypes=for-sale,for-rent&propertytypes=apartment,house&propertysubtypes=apartment,ground-floor,duplex,penthouse,studio,loft,triplex,residence,villa,mixed-building,master-house,cottage,bungalow,chalet,mansion&sortdirection=ascending&sortby=price&noindex=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)

PRICE_FROM_PARAM = "minprice"
PRICE_TO_PARAM   = "maxprice"
SORT_PARAM = "sortby"
SORT_DIRECTION_PARAM = "sortdirection"
SORT_VALUE = "price"
SORT_DIRECTION_VALUE = "ascending"
CARD_SELECTOR        = ".list-view-item"
LINK_ATTR            = "data-url"
PRICE_SELECTOR       = ".list-item-price"
PROJECT_EXCLUDE      = "/projectdetail/"

# CSV file names
LINKS_CSV = "property_links.csv"
DETAILS_CSV = "property_details.csv"

# Fields for details CSV
DETAILS_FIELDS = [
    "Link", "Locality", "Type of property", "Subtype of property",
    "Price", "Type of sale", "Number of rooms", "Livable surface",
    "Fully equipped kitchen", "Furnished", "Fireplace", "Terrace",
    "Garden", "Total land surface", "Number of facades", "Swimming pool",
    "State of the property"
]


def fetch_batch(min_price, max_pages=50):
    all_links = []
    last_price = None
    page = 1

    while True:
        if page > max_pages:
            break

        # Build URL with current min_price and page
        url = f"{base_url}&{PRICE_FROM_PARAM}={min_price}&{SORT_PARAM}={SORT_VALUE}&{SORT_DIRECTION_PARAM}={SORT_DIRECTION_VALUE}"
        if page > 1:
            url += f"&page={page}"

        try:
            resp = session.get(url)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(CARD_SELECTOR)

        if not cards:
            break

        page_links = []
        for card in cards:
            link = card.get(LINK_ATTR)
            if link and PROJECT_EXCLUDE not in link:
                price_elem = card.select_one(PRICE_SELECTOR)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    digits = re.sub(r'[^\d]', '', price_text)
                    if digits:
                        price = int(digits)
                        last_price = price
                if link not in page_links:       
                    page_links.append(link)

        all_links.extend(page_links)

        next_btn = (soup.find("a", string=re.compile(r"Next", re.I)) or
                    soup.find("a", attrs={"rel": "next"}))
        if not next_btn:
            break

        page += 1

    return all_links, last_price


def fetch_all_links_dynamic():
    """
    Repeatedly fetch batches using the last price from the previous batch as the new minimum.
    Continues until a batch returns no links.
    """
    all_links = []
    min_price = 0
    batch_num = 1

    while True:
        print(f"\n=== Batch {batch_num}: min_price = {min_price} ===")
        links, last_price = fetch_batch(min_price)

        if not links:
            print("No links found in this batch. Stopping.")
            break

        all_links.extend(links)
        print(f"Batch {batch_num} collected {len(links)} links. Total so far: {len(all_links)}")

        if last_price is None:
            print("No price information extracted – cannot determine next min_price. Stopping.")
            break

        min_price = last_price + 1
        batch_num += 1

    return all_links


def scrape_details_and_store(links, filename=DETAILS_CSV):
    """
    Visit each property link, extract desired fields, and append to details CSV.
    """
    if not links:
        print("No links to scrape details for.")
        return

    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DETAILS_FIELDS)
        if not file_exists:
            writer.writeheader()

        for index, link in enumerate(links, start=1):
            print(f"{index}. Fetching details of {link}")
            try:
                resp = session.get(link, timeout=10)
                resp.raise_for_status()
            except Exception as e:
                print(f"Failed to fetch {link}: {e}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            detail = {field: "N/A" for field in DETAILS_FIELDS}
            detail["Link"] = link

            # Locality (postal code)
            locality_elem = soup.find("span", class_="city-line")
            if locality_elem:
                text = locality_elem.get_text(strip=True)
                match = re.search(r'\d+', text)
                detail["Locality"] = match.group() if match else "N/A"

            # Subtype & Type of property
            title_elem = soup.find("span", class_="detail__header_title_main")
            if title_elem:
                full_text = title_elem.get_text(strip=True)
                normalized = full_text.lower().strip()

                subtype_mappings = [
                    ("apartment", "01", "1"),
                    ("penthous", "02", "1"),
                    ("ground floor", "03", "1"),
                    ("duplex", "04", "1"),
                    ("studio", "05", "1"),
                    ("loft", "06", "1"),
                    ("triplex", "07", "1"),
                    ("residence", "11", "2"),
                    ("villa", "12", "2"),
                    ("mixed building", "13", "2"),
                    ("master house", "14", "2"),
                    ("cottage", "15", "2"),
                    ("bangalow", "16", "2"),
                    ("bungalow", "16", "2"),1
                    ("chalet", "17", "2"),
                    ("mansion", "18", "2")
                ]

                subtype_mappings.sort(key=lambda x: len(x[0]), reverse=True)
                found = False
                for pattern, code, prop_type in subtype_mappings:
                    if normalized.startswith(pattern):
                        detail["Type of property"] = int(prop_type)
                        detail["Subtype of property"] = code
                        found = True
                        break

                if not found:
                    detail["Subtype of property"] = "N/A"
                    detail["Type of property"] = "N/A"
            else:
                detail["Subtype of property"] = "N/A"
                detail["Type of property"] = "N/A"

            # Price
            price_elem = soup.find("span", class_="detail__header_price_data")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                digits = re.sub(r'[^\d]', '', price_text)
                detail["Price"] = int(digits) if digits else "N/A"

            # Type of sale
            if title_elem:
                full_text = title_elem.get_text(strip=True).lower()
                if "rent" in full_text:
                    detail["Type of sale"] = 1
                elif "sale" in full_text:
                    detail["Type of sale"] = 2
                else:
                    detail["Type of sale"] = "N/A"
            else:
                detail["Type of sale"] = "N/A"

            # Helper to extract text from a data row by <h4> label
            def get_data_row(label):
                h4 = soup.find("h4", string=re.compile(rf"^{re.escape(label)}$", re.I))
                if h4:
                    p = h4.find_next_sibling("p")
                    if p:
                        return p.get_text(strip=True)
                return None

            # Number of bedrooms
            bedrooms_text = get_data_row("Number of bedrooms")
            if bedrooms_text:
                digits = re.sub(r'[^\d]', '', bedrooms_text)
                bedrooms = int(digits) if digits else None
            else:
                bedrooms = None
            detail["Number of rooms"] = bedrooms if bedrooms is not None else "N/A"

            # Living area
            living_text = get_data_row("Livable surface")
            if living_text:
                digits = re.sub(r'[^\d]', '', living_text)
                living_area = int(digits) if digits else None
            else:
                living_area = None
            detail["Livable surface"] = living_area if living_area is not None else "N/A"

            # Fully equipped kitchen
            kitchen_text = get_data_row("Kitchen equipment")
            if kitchen_text:
                detail["Fully equipped kitchen"] = 0 if kitchen_text.lower() == "no" else 1
            else:
                detail["Fully equipped kitchen"] = "N/A"

            # Furnished
            furnished_text = get_data_row("Furnished")
            if furnished_text:
                detail["Furnished"] = 0 if furnished_text.lower() == "no" else 1
            else:
                detail["Furnished"] = "N/A"

            # Open fire
            fire_text = get_data_row("Fireplace")
            if fire_text:
                detail["Fireplace"] = 0 if fire_text.lower() == "no" else 1
            else:
                detail["Fireplace"] = "N/A"

            # Terrace
            terrace_text = get_data_row("Terrace")
            if terrace_text:
                detail["Terrace"] = 0 if terrace_text.lower() == "no" else 1
            else:
                detail["Terrace"] = "N/A"

            # Garden
            garden_text = get_data_row("Garden")
            if garden_text:
                detail["Garden"] = 0 if garden_text.lower() == "no" else 1
            else:
                detail["Garden"] = "N/A"

            # Total land surface
            land_text = get_data_row("Total land surface")
            if land_text:
                digits = re.sub(r'[^\d]', '', land_text)
                land_area = int(digits) if digits else None
            else:
                land_area = None
            detail["Total land surface"] = land_area if land_area is not None else "N/A"

            # Number of facades
            facades_text = get_data_row("Number of facades")
            if facades_text:
                digits = re.sub(r'[^\d]', '', facades_text)
                facades = int(digits) if digits else None
            else:
                facades = None
            detail["Number of facades"] = facades if facades is not None else "N/A"

            # Swimming pool
            pool_text = get_data_row("Swimming pool")
            if pool_text:
                detail["Swimming pool"] = 0 if pool_text.lower() == "no" else 1
            else:
                detail["Swimming pool"] = "N/A"

            # State of the property
            state_text = "N/A"
            h4 = soup.find('h4', string=re.compile(r'State of the property', re.I))
            if h4:
                p = h4.find_next('p')
                if p:
                    state_text = p.get_text(strip=True)

            state_mapping = {
                "new": 1,
                "excellent": 2,
                "fully renovated": 3,
                "normal": 4,
                "to renovate": 5,
                "to be renovated": 5,
            }

            if state_text and state_text != "N/A":
                lower_text = state_text.lower().strip()
                matched_code = "N/A"
                for key, code in state_mapping.items():
                    if key in lower_text:
                        matched_code = code
                        break
                detail["State of the property"] = matched_code
            else:
                detail["State of the property"] = "N/A"

            writer.writerow(detail)


def load_existing_links(filename):
    """Load existing property URLs from CSV into a set."""
    existing = set()
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if row:
                    existing.add(row[0])
    return existing


def store_new_links(new_links, filename=LINKS_CSV):
    """Append new links to the CSV file (creates file with header if needed)."""
    if not new_links:
        print("No new links to store.")
        return
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Link"])
        for link in new_links:
            writer.writerow([link])
    print(f"Appended {len(new_links)} new links to {filename}")


if __name__ == "__main__":
    # ------------------------------------------------------------
    # STEP 1: Fetch all property links from the website
    # ------------------------------------------------------------
    print("Starting link collection...")
    all_links = fetch_all_links_dynamic()
    print(f"\nTotal links collected: {len(all_links)}")

    # Store the links (overwrite any existing file)
    with open(LINKS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Link"])
        for link in all_links:
            writer.writerow([link])
    print(f"Links saved to {LINKS_CSV}")

    # ------------------------------------------------------------
    # STEP 2: Scrape details for all collected links
    # ------------------------------------------------------------
    print("\nStarting details scraping...")
    # Load links from the file (or use all_links directly)
    links_to_scrape = load_existing_links(LINKS_CSV)
    print(f"Loaded {len(links_to_scrape)} links from {LINKS_CSV}.")

    # Scrape details and append to property_details.csv
    scrape_details_and_store(list(links_to_scrape), filename=DETAILS_CSV)

    print(f"\nAll done! Details saved to {DETAILS_CSV}.")