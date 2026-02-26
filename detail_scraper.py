import requests
import csv
import re
import os
from bs4 import BeautifulSoup

class DetailScraper:
    """
    Responsible for scraping individual property details from given links.
    """

    def __init__(self, session=None, headers=None, details_fields=None,
                 details_csv="property_details.csv"):
        """
        Initialize the DetailScraper with a session and field definitions.
        """
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            if headers:
                self.session.headers.update(headers)
            else:
                self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        if details_fields is None:
            self.details_fields = [
                "Link", "Locality", "Type of property", "Subtype of property",
                "Price", "Type of sale", "Number of rooms", "Livable surface",
                "Fully equipped kitchen", "Furnished", "Fireplace", "Terrace",
                "Garden", "Total land surface", "Number of facades", "Swimming pool",
                "State of the property"
            ]
        else:
            self.details_fields = details_fields

        self.details_csv = details_csv

        # Internal mapping for subtypes
        self.subtype_mappings = [
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
            ("chalet", "17", "2"),
            ("mansion", "18", "2")
        ]
        # Internal mapping for property state
        self.state_mapping = {
            "new": 1,
            "excellent": 2,
            "fully renovated": 3,
            "normal": 4,
            "to renovate": 5,
            "to be renovated": 5,
            "renovate": 5,
        }

    def scrape_details(self, links, output_filename=None):
        """
        Visit each property link, extract desired fields, and append to CSV.
        """
        if output_filename is None:
            output_filename = self.details_csv

        if not links:
            print("No links to scrape details for.")
            return

        file_exists = os.path.exists(output_filename)
        with open(output_filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.details_fields)
            if not file_exists:
                writer.writeheader()

            for index, link in enumerate(links, start=1):
                print(f"{index}. Fetching details of {link}")
                try:
                    resp = self.session.get(link, timeout=10)
                    resp.raise_for_status()
                except Exception as e:
                    print(f"Failed to fetch {link}: {e}")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                detail = self._extract_detail_from_soup(soup, link)
                writer.writerow(detail)

    # ------------------------------------------------------------------
    # Helper methods for extraction
    # ------------------------------------------------------------------
    def _extract_detail_from_soup(self, soup, link):
        """Extract all desired fields from a property page's soup."""
        detail = {field: "N/A" for field in self.details_fields}
        detail["Link"] = link

        # Locality (postal code)
        locality_elem = soup.find("span", class_="city-line")
        if locality_elem:
            text = locality_elem.get_text(strip=True)
            match = re.search(r'\d+', text)
            detail["Locality"] = match.group() if match else "N/A"
        else:
            detail["Locality"] = "N/A"

        # Subtype & Type of property
        title_elem = soup.find("span", class_="detail__header_title_main")
        if title_elem:
            full_text = title_elem.get_text(strip=True)
            normalized = full_text.lower().strip()

            # Sort mappings by length descending to match longest first
            sorted_mappings = sorted(self.subtype_mappings, key=lambda x: len(x[0]), reverse=True)
            found = False
            for pattern, code, prop_type in sorted_mappings:
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
        else:
            detail["Price"] = "N/A"

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

        # Helper to get data row text by <h4> label
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

        # Fireplace
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
        state_text = get_data_row("State of the property")
        if not state_text:
            state_text = get_data_row("State of the property")  # fallback to same label (was "Building condition"?)

        if state_text and state_text != "N/A":
            lower_text = state_text.lower().strip()
            matched_code = "N/A"
            for key, code in self.state_mapping.items():
                if key in lower_text:
                    matched_code = code
                    break
            detail["State of the property"] = matched_code
        else:
            detail["State of the property"] = "N/A"

        return detail