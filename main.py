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

# <input type="number" id="price-range-from" class="form-control">
PRICE_FROM_PARAM = "minprice"   # e.g., "minPrice" or "price-from"

# <input type="number" id="price-range-to" class="form-control">
PRICE_TO_PARAM   = "maxprice"     # e.g., "maxPrice" or "price-to"

# <button class="button button-secondary dropdown-toggle px-3 text-nowrap  " type="button" id="dropdownSearchButton" data-toggle="dropdown" aria-expanded="true">
#                    <i class="fas fa-sort-alpha-down " aria-hidden="true"></i>
#                </button>
SORT_PARAM = "sortby"
SORT_DIRECTION_PARAM = "sortdirection"
SORT_VALUE = "price"
SORT_DIRECTION_VALUE = "ascending"



CARD_SELECTOR        = ".list-view-item"           # class for each property card
LINK_ATTR            = "data-url"                   # attribute containing the detail URL
PRICE_SELECTOR       = ".list-item-price"               # class for the price element on the card
PROJECT_EXCLUDE      = "/projectdetail/"            # string to exclude project links

def fetch_batch(min_price, max_pages=50):
    all_links = []
    last_price = None
    page = 1

    while True:
        if page > max_pages:
            break

        # Base URL with price filter and sorting
        url = f"{base_url}&{PRICE_FROM_PARAM}={min_price}&{SORT_PARAM}={SORT_VALUE}&{SORT_DIRECTION_PARAM}={SORT_DIRECTION_VALUE}"
        if page > 1:
            url += f"&page={page}"

        print(f"  Fetching page {page} (min_price={min_price}): {url}")
        try:
            resp = session.get(url)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(CARD_SELECTOR)   # e.g., ".list-view-item"

        if not cards:
            break

        page_links = []
        for card in cards:
            link = card.get(LINK_ATTR)       # e.g., "data-url"
            if link and PROJECT_EXCLUDE not in link:
                # Extract price from card (adjust selector as needed)
                price_elem = card.select_one(PRICE_SELECTOR)  # e.g., ".card__price"
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    digits = re.sub(r'[^\d]', '', price_text)
                    if digits:
                        price = int(digits)
                        last_price = price
                page_links.append(link)

        all_links.extend(page_links)

        # Check for next page
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
    min_price = 0          # start from the lowest price
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

        # Set next min_price to last_price + 1 to move forward
        # (you may use a larger step if prices are very granular)
        min_price = last_price + 1
        batch_num += 1

    return all_links

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
        #scrape_details_and_store(all_links)
    else:
        print("No links found. Exiting.")