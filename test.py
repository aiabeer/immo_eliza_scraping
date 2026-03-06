import requests
import csv
import time
import re
from bs4 import BeautifulSoup

main_url = "https://immovlan.be/en/real-estate?transactiontypes=for-sale&propertytypes=house,apartment&propertysubtypes=residence,villa,mixed-building,master-house,cottage,bungalow,chalet,mansion,apartment,penthouse,ground-floor,duplex,studio,loft,triplex"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_all_links(base_url, max_pages=50):
    all_links = []
    page = 1

    while True:
        if max_pages and page > max_pages:
            print(f"Reached maximum page limit ({max_pages}). Stopping.")
            break

        # Build URL with page parameter
        if page == 1:
            url = base_url
        else:
            separator = "&" if "?" in base_url else "?"
            url = f"{base_url}{separator}page={page}"

        print(f"Fetching page {page}: {url}")
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        # Find all elements with class 'list-view-item' (could be article, div, etc.)
        cards = soup.find_all(class_="list-view-item")

        if not cards:
            print(f"No property cards found on page {page}. Stopping.")
            break

        page_links = []
        for card in cards:
            link = card.get("data-url")
            # check if link contains /projectdetail do not include it
            if link and "/projectdetail/" not in link:
                # The data-url is already absolute, no need to prepend domain
                page_links.append(link)

        print(f"Page {page}: found {len(page_links)} links")
        all_links.extend(page_links)

        # Check for a "Next" button – adjust selector as needed
        next_btn = soup.find("a", string=re.compile(r"Next", re.I)) or \
                   soup.find("a", attrs={"rel": "next"}) or \
                   soup.find("li", class_="next")
        if not next_btn:
            print("No 'Next' button found – assuming last page.")
            break

        page += 1
        time.sleep(1)

    return all_links


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

        # Locality (postal code)
        locality_elem = soup.find("span", class_="city-line")
        if locality_elem:
            text = locality_elem.get_text(strip=True)
            match = re.search(r'\d+', text)
            detail["Locality"] = match.group() if match else "N/A"
        else:
            detail["Locality"] = "N/A"

        # Subtype of property (first word of the main title)
        title_elem = soup.find("span", class_="detail__header_title_main")
        if title_elem:
            full_text = title_elem.get_text(strip=True)
            detail["Subtype of property"] = full_text.split()[0] if full_text else "N/A"
        else:
            detail["Subtype of property"] = "N/A"

        # Price
        price_elem = soup.find("span", class_="detail__price")
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            digits = re.sub(r'[^\d]', '', price_text)
            detail["Price"] = int(digits) if digits else "N/A"
        else:
            detail["Price"] = "N/A"

        # Type of sale (third word of the main title)
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

        # Number of bedrooms
        bedrooms_text = get_data_row("Number of bedrooms")
        detail["Number of rooms"] = bedrooms_text if bedrooms_text else "N/A"

        # Living Area
        living_text = get_data_row("Livable surface")
        detail["Living Area"] = living_text if living_text else "N/A"

        # Fully equipped kitchen (0/1)
        kitchen_text = get_data_row("Kitchen equipment")
        if kitchen_text:
            detail["Fully equipped kitchen"] = 0 if kitchen_text.lower() == "no" else 1
        else:
            detail["Fully equipped kitchen"] = "N/A"

        # Furnished (0/1)
        furnished_text = get_data_row("Furnished")
        if furnished_text:
            detail["Furnished"] = 0 if furnished_text.lower() == "no" else 1
        else:
            detail["Furnished"] = "N/A"

        # Open fire (0/1)
        fire_text = get_data_row("Open fire")
        if fire_text:
            detail["Open fire"] = 0 if fire_text.lower() == "no" else 1
        else:
            detail["Open fire"] = "N/A"

        # Terrace, Garden, Surface of the land, Surface area of the plot of land,
        # Number of facades, Swimming pool, State of the building
        # (Add similar extraction for the remaining fields if desired)

        details_list.append(detail)
        time.sleep(1)  # be polite

    # Write to CSV
    fieldnames = [
        "Link", "Locality", "Subtype of property", "Type of sale", "Price",
        "Number of rooms", "Living Area", "Fully equipped kitchen",
        "Furnished", "Open fire"
        # Add more fields here if you extend the extraction
    ]
    with open("property_details_test.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in details_list:
            writer.writerow(row)

    print(f"Stored details of {len(details_list)} properties in property_details_test.csv")


def store_links(links):
    """Save the list of property URLs to a CSV file."""
    with open("property_links_test.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Link"])
        for link in links:
            writer.writerow([link])
    print(f"Stored {len(links)} links in property_links_test.csv")


if __name__ == "__main__":
    all_links = fetch_all_links(main_url)
    if all_links:
        store_links(all_links)
        scrape_details_and_store(all_links)
    else:
        print("No links found. Exiting.")