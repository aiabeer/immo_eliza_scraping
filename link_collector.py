import requests
import re
from bs4 import BeautifulSoup


class LinkCollector:

    BASE_URL = "https://immovlan.be/en/real-estate?transactiontypes=for-sale,for-rent&propertytypes=apartment,house&propertysubtypes=apartment,ground-floor,duplex,penthouse,studio,loft,triplex,residence,villa,mixed-building,master-house,cottage,bungalow,chalet,mansion&sortdirection=ascending&sortby=price&noindex=1"

    HEADERS = {
        "User-Agent": "Mozilla/5.0"
    }

    PRICE_FROM_PARAM = "minprice"
    SORT_PARAM = "sortby"
    SORT_DIRECTION_PARAM = "sortdirection"
    SORT_VALUE = "price"
    SORT_DIRECTION_VALUE = "ascending"

    CARD_SELECTOR = ".list-view-item"
    LINK_ATTR = "data-url"
    PRICE_SELECTOR = ".list-item-price"
    PROJECT_EXCLUDE = "/projectdetail/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_batch(self, min_price, max_pages=50):
        all_links = []
        last_price = None
        page = 1

        while page <= max_pages:

            url = (
                f"{self.BASE_URL}"
                f"&{self.PRICE_FROM_PARAM}={min_price}"
                f"&{self.SORT_PARAM}={self.SORT_VALUE}"
                f"&{self.SORT_DIRECTION_PARAM}={self.SORT_DIRECTION_VALUE}"
            )

            if page > 1:
                url += f"&page={page}"

            try:
                resp = self.session.get(url)
                resp.raise_for_status()
            except Exception as e:
                print(f"Batch error: {e}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(self.CARD_SELECTOR)

            if not cards:
                break

            page_links = []

            for card in cards:
                link = card.get(self.LINK_ATTR)
                if link and self.PROJECT_EXCLUDE not in link:

                    price_elem = card.select_one(self.PRICE_SELECTOR)
                    if price_elem:
                        digits = re.sub(r"[^\d]", "", price_elem.get_text(strip=True))
                        if digits:
                            last_price = int(digits)

                    if link not in page_links:
                        page_links.append(link)

            all_links.extend(page_links)

            next_btn = (
                soup.find("a", string=re.compile(r"Next", re.I))
                or soup.find("a", attrs={"rel": "next"})
            )

            if not next_btn:
                break

            page += 1

        return all_links, last_price

    def fetch_all_links_dynamic(self):
        all_links = []
        min_price = 0
        batch = 1

        while True:
            print(f"\n=== Batch {batch} | min_price={min_price} ===")
            links, last_price = self.fetch_batch(min_price)

            if not links:
                break

            all_links.extend(links)
            print(f"Collected {len(links)} | Total={len(all_links)}")

            if last_price is None:
                break

            min_price = last_price + 1
            batch += 1

        return all_links