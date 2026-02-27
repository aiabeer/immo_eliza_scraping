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