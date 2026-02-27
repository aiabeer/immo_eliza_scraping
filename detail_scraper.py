import requests
import re
import csv
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup


class DetailScraper:

    HEADERS = {
        "User-Agent": "Mozilla/5.0"
    }

    DETAILS_FIELDS = [
        "Link", "Locality", "Type of property", "Subtype of property",
        "Price", "Type of sale", "Number of rooms", "Livable surface",
        "Fully equipped kitchen", "Furnished", "Fireplace", "Terrace",
        "Garden", "Total land surface", "Number of facades",
        "Swimming pool", "State of the property"
    ]

    def __init__(self, max_workers=12):
        self.max_workers = max_workers
        self.thread_local = threading.local()

    # Thread-safe session
    def _get_session(self):
        if not hasattr(self.thread_local, "session"):
            s = requests.Session()
            s.headers.update(self.HEADERS)
            self.thread_local.session = s
        return self.thread_local.session

    def _get_data_row(self, soup, label):
        h4 = soup.find("h4", string=re.compile(rf"^{re.escape(label)}$", re.I))
        if h4:
            p = h4.find_next_sibling("p")
            if p:
                return p.get_text(strip=True)
        return None

    def _scrape_single(self, link):

        try:
            session = self._get_session()
            resp = session.get(link, timeout=10)
            resp.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        detail = {field: "N/A" for field in self.DETAILS_FIELDS}
        detail["Link"] = link

        # --- Locality ---
        loc = soup.find("span", class_="city-line")
        if loc:
            match = re.search(r"\d+", loc.get_text(strip=True))
            if match:
                detail["Locality"] = match.group()

        # --- Price ---
        price_elem = soup.find("span", class_="detail__header_price_data")
        if price_elem:
            digits = re.sub(r"[^\d]", "", price_elem.get_text(strip=True))
            if digits:
                detail["Price"] = int(digits)

        # Bedrooms
        bedrooms = self._get_data_row(soup, "Number of bedrooms")
        if bedrooms:
            digits = re.sub(r"[^\d]", "", bedrooms)
            if digits:
                detail["Number of rooms"] = int(digits)

        # Living surface
        living = self._get_data_row(soup, "Livable surface")
        if living:
            digits = re.sub(r"[^\d]", "", living)
            if digits:
                detail["Livable surface"] = int(digits)

        return detail

    def scrape_and_store(self, links, output_file):

        if not links:
            print("No links provided.")
            return

        file_exists = os.path.exists(output_file)

        with open(output_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.DETAILS_FIELDS)
            if not file_exists:
                writer.writeheader()

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self._scrape_single, link) for link in links]

                for i, future in enumerate(as_completed(futures), start=1):
                    result = future.result()
                    if result:
                        writer.writerow(result)

                    if i % 10 == 0:
                        print(f"{i}/{len(links)} processed")