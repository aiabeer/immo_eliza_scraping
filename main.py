from lib.link_collector import LinkCollector
from lib.detail_scraper import DetailScraper

DETAILS_FILE = "property_details.csv"

def main(test_limit=None):
    collector = LinkCollector()
    scraper = DetailScraper(max_workers=12)

    print("Collecting links...")
    links = collector.fetch_all_links_dynamic(max_links=test_limit)
    print(f"Total links collected: {len(links)}")

    print("\nScraping details...")
    scraper.scrape_and_store(links, DETAILS_FILE)

if __name__ == "__main__":
    # Set TEST_LIMIT to a number (e.g., 1000) to limit collection,
    # or None to collect everything.
    TEST_LIMIT = None  # change this as needed
    main(test_limit=TEST_LIMIT)