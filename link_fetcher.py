import requests
import csv
import re
import os
from bs4 import BeautifulSoup

class LinkFetcher:
    """
    Responsible for fetching property links from the search pages,
    handling pagination and dynamic price-based batching.
    """

    def __init__(self, base_url, headers=None, session=None,
                 price_from_param="minprice", price_to_param="maxprice",
                 sort_param="sortby", sort_direction_param="sortdirection",
                 sort_value="price", sort_direction_value="ascending",
                 card_selector=".list-view-item", link_attr="data-url",
                 price_selector=".list-item-price", project_exclude="/projectdetail/",
                 links_csv="property_links.csv"):
        """
        Initialize the LinkFetcher with configuration parameters.
        """
        self.base_url = base_url
        self.price_from_param = price_from_param
        self.price_to_param = price_to_param
        self.sort_param = sort_param
        self.sort_direction_param = sort_direction_param
        self.sort_value = sort_value
        self.sort_direction_value = sort_direction_value
        self.card_selector = card_selector
        self.link_attr = link_attr
        self.price_selector = price_selector
        self.project_exclude = project_exclude
        self.links_csv = links_csv

        # Set up session
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            if headers:
                self.session.headers.update(headers)
            else:
                self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def fetch_batch(self, min_price, max_pages=50):
        """
        Fetch a batch of links starting from a given minimum price.
        Returns (list_of_links, last_price) or ([], None) if none found.
        """
        all_links = []
        last_price = None
        page = 1

        while page <= max_pages:
            url = f"{self.base_url}&{self.price_from_param}={min_price}&{self.sort_param}={self.sort_value}&{self.sort_direction_param}={self.sort_direction_value}"
            if page > 1:
                url += f"&page={page}"

            print(f"Fetching page {page}")
            try:
                resp = self.session.get(url)
                resp.raise_for_status()
            except Exception as e:
                print(f"Error: {e}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(self.card_selector)

            if not cards:
                break

            page_links = []
            for card in cards:
                link = card.get(self.link_attr)
                if link and self.project_exclude not in link:
                    price_elem = card.select_one(self.price_selector)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        digits = re.sub(r'[^\d]', '', price_text)
                        if digits:
                            last_price = int(digits)
                    if link not in page_links:
                        page_links.append(link)

            all_links.extend(page_links)

            next_btn = (soup.find("a", string=re.compile(r"Next", re.I)) or
                        soup.find("a", attrs={"rel": "next"}))
            if not next_btn:
                break

            page += 1

        return all_links, last_price

    def fetch_all_links_dynamic(self):
        """
        Repeatedly fetch batches using the last price from the previous batch as the new minimum.
        Continues until a batch returns no links.
        """
        all_links = []
        min_price = 0
        batch_num = 1

        while True:
            print(f"\n=== Batch {batch_num}: min_price = {min_price} ===")
            links, last_price = self.fetch_batch(min_price)

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

    def load_existing_links(self, filename=None):
        """Load existing property URLs from CSV into a set."""
        if filename is None:
            filename = self.links_csv
        existing = set()
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    if row:
                        existing.add(row[0])
        return existing

    def store_new_links(self, new_links, filename=None):
        """Append new links to the CSV file (creates file with header if needed)."""
        if filename is None:
            filename = self.links_csv
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