import requests
import csv
import re
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


def fetch_batch(min_price, max_pages=50):
    all_links = []
    last_price = None
    page = 1

    while True:
        if page > max_pages:
            break

        url = f"{base_url}&{PRICE_FROM_PARAM}={min_price}&{SORT_PARAM}={SORT_VALUE}&{SORT_DIRECTION_PARAM}={SORT_DIRECTION_VALUE}"
        if page > 1:
            url += f"&page={page}"

        print(f"Fetching page {page}")
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

"""Locality
Type of property (House/apartment)
Subtype of property (Bungalow, Chalet, Mansion, ...)
Price
Type of sale (Exclusion of life sales)
Number of rooms
Living Area
Fully equipped kitchen (Yes/No)
Furnished (Yes/No)
Open fire (Yes/No)
Terrace (Yes/No)
If yes: Area
Garden (Yes/No)
If yes: Area
Surface of the land
Surface area of the plot of land
Number of facades
Swimming pool (Yes/No)
State of the building (New, to be renovated, ...)
"""
def scrape_details_and_store(links):
    """Visit each property link, extract desired fields, and save to CSV."""
    details_list = []

    for link in links:
        print(f"Scraping details from: {link}")
        try:
            resp = session.get(link, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {link}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        detail = {"Link": link}

        # ==========================================================
        # Locality (postal code) 
        # ==========================================================
        locality_elem = soup.find("span", class_="city-line")
        if locality_elem:
            text = locality_elem.get_text(strip=True)
            match = re.search(r'\d+', text)
            detail["Locality"] = match.group() if match else "N/A"
        else:
            detail["Locality"] = "N/A"
        # ==========================================================
        # type of property 
        # ==========================================================

        # ==========================================================
        # Subtype of property (first word of the main title)
        # ==========================================================
        title_elem = soup.find("span", class_="detail__header_title_main")
        if title_elem:
            full_text = title_elem.get_text(strip=True)
            detail["Subtype of property"] = full_text.split()[0] if full_text else "N/A"
        else:
            detail["Subtype of property"] = "N/A"

        # ==========================================================
        # Price
        # ==========================================================
        price_elem = soup.find("span", class_="detail__price")
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            digits = re.sub(r'[^\d]', '', price_text)
            detail["Price"] = int(digits) if digits else "N/A"
        else:
            detail["Price"] = "N/A"

        # ==========================================================
        # Type of sale
        # ==========================================================
        if title_elem:
            parts = title_elem.get_text(strip=True).split()
            detail["Type of sale"] = parts[2] if len(parts) >= 3 else "N/A"
        else:
            detail["Type of sale"] = "N/A"

        # Helper to extract text from a data row by <h4> label
        def get_data_row(label):
            # Find the <h4> with exact text, then take the next <p>
            h4 = soup.find("h4", string=re.compile(rf"^{re.escape(label)}$", re.I))
            if h4:
                p = h4.find_next_sibling("p")
                if p:
                    return p.get_text(strip=True)
            return None

        # ==========================================================
        # Number of bedrooms
        # ==========================================================
        bedrooms_text = get_data_row("Number of bedrooms")
        if bedrooms_text:
            # Extract all digits from the string (handles "3", "3 bedrooms", etc.)
            digits = ''.join(filter(str.isdigit, bedrooms_text))
            bedrooms = int(digits) if digits else None
        else:
            bedrooms = None

        detail["Number of rooms"] = bedrooms if bedrooms is not None else "N/A"

        # ==========================================================
        # Living Area
        # ==========================================================
        linving_area_text = get_data_row("Livable surface")
        if linving_area_text:
        # Extract all digits and join them (handles numbers like "12000")
            digits = ''.join(filter(str.isdigit, linving_area_text))
            living_land_area = int(digits) if digits else None
        else:
            living_land_area = None

        detail["Livable surface"] = living_land_area if living_land_area is not None else "N/A"

        # ==========================================================
        # Fully equipped kitchen (0/1)
        # ==========================================================
        kitchen_text = get_data_row("Kitchen equipment")
        if kitchen_text:
            detail["Fully equipped kitchen"] = 0 if kitchen_text.lower() == "no" else 1
        else:
            detail["Fully equipped kitchen"] = "N/A"

        # ==========================================================
        # Furnished (0/1)
        # ==========================================================
        furnished_text = get_data_row("Furnished")
        if furnished_text:
            detail["Furnished"] = 0 if furnished_text.lower() == "no" else 1
        else:
            detail["Furnished"] = "N/A"

        # ==========================================================
        # Open fire (0/1)
        # ==========================================================
        fire_text = get_data_row("Open fire")
        if fire_text:
            detail["Open fire"] = 0 if fire_text.lower() == "no" else 1
        else:
            detail["Open fire"] = "N/A"

        # ==========================================================
        # Terrace
        # ==========================================================
        terrace = get_data_row("Terrace")
        if terrace:
            detail["Terrace"] = 0 if terrace.lower() == "no" else 1
        else:
            detail["Terrace"] = "N/A"

        # ==========================================================
        # Garden Surface garden
        # ==========================================================
        garden = get_data_row("Garden")
        if garden:
            detail["Garden"] = 0 if garden.lower() == "no" else 1
        else:
            detail["Garden"] = "N/A"

        # ==========================================================
        # Surface of the land 
        # ==========================================================
        land_area_text = get_data_row("Total land surface")
        if land_area_text:
        # Extract all digits and join them (handles numbers like "12000")
            digits = ''.join(filter(str.isdigit, land_area_text))
            land_area = int(digits) if digits else None
        else:
            land_area = None

        detail["Total land surface"] = land_area if land_area is not None else "N/A"

        # ==========================================================
        # Number of facades Number of facades
        # ==========================================================
        facades_text = get_data_row("Number of facades")
        if facades_text:
            digits = ''.join(filter(str.isdigit, facades_text))
            facades = int(digits) if digits else None
        else:
            facades = None

        detail["Number of facades"] = facades if facades is not None else "N/A"

        # ==========================================================
        # Swimming pool
        # ==========================================================
        swimming_pool = get_data_row("Swimming pool")
        if swimming_pool:
            detail["Swimming pool"] = 0 if swimming_pool.lower() == "no" else 1
        else:
            detail["Swimming pool"] = "N/A"        
            
        # ==========================================================
        # State of the building
        # ==========================================================


        details_list.append(detail)


def store_links(links):
    """Save the list of property URLs to a CSV file."""
    with open("property_links.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Link"])
        for link in links:
            writer.writerow([link])
    print(f"Stored {len(links)} links in property_links.csv")


if __name__ == "__main__":
    all_links = fetch_all_links_dynamic()
    if all_links:
        store_links(all_links)
        scrape_details_and_store(all_links)
    else:
        print("No links found. Exiting.")