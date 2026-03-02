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

    def _has_next_page(self, soup):
        """Return True if a 'next' button exists."""
        next_btn = (
            soup.find("a", string=re.compile(r"Next", re.I))
            or soup.find("a", attrs={"rel": "next"})
        )
        return next_btn is not None

    def fetch_batch(self, min_price, limit=None, max_pages=50):
        """
        Fetch links starting from min_price, up to 'limit' links (if given).
        Returns (list_of_links, last_price).
        """
        batch_links = []
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
                print(f"Batch error (min_price={min_price}, page={page}): {e}")
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
                    page_links.append(link)

            batch_links.extend(page_links)

            # Stop if we've reached the limit
            if limit and len(batch_links) >= limit:
                batch_links = batch_links[:limit]
                break

            # Stop if no next page
            if not self._has_next_page(soup):
                break

            page += 1

        return batch_links, last_price

    def fetch_all_links_dynamic(self, max_links=None):
        """
        Collect all property links, optionally stopping after max_links.
        """
        all_links = []
        min_price = 0
        batch = 1

        while True:
            remaining = max_links - len(all_links) if max_links else None
            print(f"\n=== Batch {batch} | min_price={min_price} | need {remaining if remaining else 'unlimited'} ===")

            links, last_price = self.fetch_batch(min_price, limit=remaining)
            all_links.extend(links)
            print(f"Collected {len(links)} links this batch. Total: {len(all_links)}")

            if not links:
                break

            if max_links and len(all_links) >= max_links:
                # Trim if we overshot (shouldn't happen, but safe)
                all_links = all_links[:max_links]
                break

            if last_price is None:
                break

            min_price = last_price + 1
            batch += 1

        return all_links