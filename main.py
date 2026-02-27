from link_collector import LinkCollector
from detail_scraper import DetailScraper


LINKS_FILE = "src/property_links.csv"
DETAILS_FILE = "src/property_details.csv"


def main(test_limit=None):

    collector = LinkCollector()
    scraper = DetailScraper(max_workers=12)

    print("Collecting links...")
    links = collector.fetch_all_links_dynamic()
    print(f"Total links collected: {len(links)}")

    # ------------------------------------------------
    # TEST MODE: Limit number of links
    # ------------------------------------------------
    if test_limit:
        print(f"\nTEST MODE ACTIVE → Using only first {test_limit} links")
        links = links[:test_limit]

    print("\nScraping details...")
    scraper.scrape_and_store(links, DETAILS_FILE)

    print("Done.")


if __name__ == "__main__":

    # Change this number to test fewer links
    # None → full run
    # 5 → scrape only 5 links
    # 20 → scrape only 20 links
    TEST_LIMIT = None

    main(test_limit=TEST_LIMIT)