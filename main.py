import requests
import csv
import time
from selenium import webdriver
from selenium.common import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

main_url = "https://immovlan.be/en/real-estate?transactiontypes=for-sale&propertytypes=house,apartment&propertysubtypes=residence,villa,mixed-building,master-house,cottage,bungalow,chalet,mansion,apartment,penthouse,ground-floor,duplex,studio,loft,triplex"


"""
urls: 

appartment for rent: https://immovlan.be/en/real-estate?transactiontypes=for-rent&propertytypes=apartment&propertysubtypes=apartment,duplex,studio,ground-floor,penthouse,triplex,loft&noindex=1
appartment for sale: https://immovlan.be/en/real-estate?transactiontypes=for-sale&propertytypes=apartment&propertysubtypes=apartment,duplex,studio,ground-floor,penthouse,triplex,loft&noindex=1

"""

def accept_cookies(driver):
    """Accept cookies using the provided driver instance."""
    try:
        wait = WebDriverWait(driver, 1)
        accept_button = wait.until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        accept_button.click()
        print("Cookies accepted (normal click)")
    except TimeoutException:
        print("Cookie button not found – may already be accepted or not present.")
    except ElementClickInterceptedException:
        # Fallback to JavaScript click
        print("Normal click intercepted – trying JavaScript click")
        driver.execute_script("arguments[0].click();", accept_button)
        print("Cookies accepted (JavaScript click)")
    time.sleep(2)  # let popup disappear

def fetch_all_links(base_url, max_pages=50):
    """
    Scrape property links from all pages up to max_pages (if provided).
    If max_pages is None, scrape until no more pages are found.
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    all_links = []
    page = 1

    while True:
        # Stop if we've reached the maximum page limit
        if max_pages is not None and page > max_pages:
            print(f"Reached maximum page limit ({max_pages}). Stopping.")
            break

        # Construct URL for current page
        if page == 1:
            url = base_url
        else:
            # Add page parameter (assuming the site uses &page=)
            if '?' in base_url:
                url = f"{base_url}&page={page}"
            else:
                url = f"{base_url}?page={page}"

        print(f"Navigating to page {page}: {url}")
        driver.get(url)

        # Accept cookies (in case popup reappears)
        accept_cookies(driver)

        # Wait for property cards to load
        try:
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, "list-view-item"))
            )
        except TimeoutException:
            print(f"No property cards found on page {page}. Stopping.")
            break

        # Extract links from current page
        cards = driver.find_elements(By.CLASS_NAME, "list-view-item")
        if not cards:
            print(f"No cards on page {page}. Stopping.")
            break

        page_links = []
        for card in cards:
            link = card.get_attribute("data-url")
            if link:
                page_links.append(link)

        print(f"Page {page}: found {len(page_links)} links")
        all_links.extend(page_links)

        # Check if there is a "Next" button to determine if more pages exist
        try:
            # Look for a clickable next button (adjust selector if needed)
            next_button = driver.find_element(
                By.XPATH,
                "//a[contains(text(),'Next')] | //a[contains(@rel,'next')] | //li[contains(@class,'next')]/a[not(contains(@class,'disabled'))]"
            )
    
            # The presence of a next button confirms that page+1 should exist.
        except:
            print("No 'Next' button found – assuming last page.")
            break

        page += 1
        time.sleep(1)  # polite delay

    driver.quit()
    return all_links


# scrape every details page informations and store them in a csv file
def scrape_details_and_store(links):    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    details_list = []

    for link in links:
        print(f"Scraping details from: {link}")
        driver.get(link)
        time.sleep(2)  # wait for page to load

        # Extract details Locality, Type of property, Subtype of property, Price, Type of sale, Number of rooms, Living Area, Fully equipped kitchen, Furnished, Open fire, Terrace, Garden, Surface of the land, Surface area of the plot of land, Number of facades, Swimming pool, State of the building
        # <span class="city-line">9820 Merelbeke</span>
        try:
            locality = driver.find_element(By.CLASS_NAME, "city-line").text
            match = re.search(r'\d+', locality)
            locality = match.group() if match else "N/A"
        except:
            locality = "N/A"


        # <span class="detail__header_title_main"> Residence for sale <span class="d-none d-lg-inline">- Merelbeke</span> <span class="vlancode">RBV33387</span></span>
        try:
            full_text = driver.find_element(By.CLASS_NAME, "detail__header_title_main").text
            # Extract first word
            property_subtype = full_text.split()[0] if full_text else "N/A"
        except:
            property_subtype = "N/A"

        # Price
        # <span class="detail__header_price_data"><small></small> 445 000 €
        try: 
            price_text = driver.find_element(By.CLASS_NAME, "detail__price").text
            price = re.sub(r'[^\d]', '', price_text)
            price = int(price) if price else "N/A"
        except:
            price = "N/A"


        # <span class="detail__header_title_main"> Residence for sale <span class="d-none d-lg-inline">- Merelbeke</span> <span class="vlancode">RBV33387</span></span>
        # store it like 0 or 1 
        try:
            full_line = driver.find_element(By.CLASS_NAME, "detail__header_title_main").text
            # Extract the third word
            sale_type = full_line.split()[2] if full_line else "N/A"
        except:
            sale_type = "N/A"

        # Number of rooms
        # 
        try:
            wrapper = driver.find_element(By.CLASS_NAME, "data-row-wrapper")
            bedrooms = wrapper.find_element(By.XPATH, ".//h4[text()='Number of bedrooms']/following-sibling::p").text
        except:
            bedrooms = "N/A" 

        # Living Area
        # <h4>Livable surface</h4>
        try:
            wrapper = driver.find_element(By.CLASS_NAME, "data-row-wrapper")
            living_area = wrapper.find_element(By.XPATH, ".//h4[text()='Livable surface']/following-sibling::p").text
        except:
            living_area = "N/A"

        # Fully equipped kitchen
        # <h4>Kitchen equipment</h4>
        try:
            wrapper = driver.find_element(By.CLASS_NAME, "data-row-wrapper")
            kitchen_text = wrapper.find_element(By.XPATH, ".//h4[text()='Kitchen equipment']/following-sibling::p").text.strip()
            kitchen_equipment = 0 if kitchen_text.lower() == 'no' else 1
        except:
            kitchen_equipment = "N/A"
        
        # Furnished
        try:
            wrapper = driver.find_element(By.CLASS_NAME, "data-row-wrapper")
            furnished_text = wrapper.find_element(By.XPATH, ".//h4[text()='Furnished']/following-sibling::p").text.strip()
            furnished = 0 if furnished_text.lower() == 'no' else 1
        except:
            furnished = "N/A"

        # Open fire
        try:
            wrapper = driver.find_element(By.CLASS_NAME, "data-row-wrapper")
            open_fire_text = wrapper.find_element(By.XPATH, ".//h4[text()='Open fire']/following-sibling::p").text.strip()
            open_fire = 0 if open_fire_text.lower() == 'no' else 1
        except:
            open_fire = "N/A"

        # Terrace
        # Garden
        # Surface of the land
        # Surface area of the plot of land
        # Number of facades
        # Swimming pool
        # State of the building               

        details_list.append({
            "Link": link,
            "Locality": locality,
            "Subtype of property": property_subtype,
            "Type of sale": sale_type, 
            "Price": price,
            "Number of rooms": bedrooms, 
            "Living Area": living_area, 
            "Fully equipped kitchen": kitchen_equipment,

        })

    driver.quit()

    # store details Locality, Type of property, Subtype of property, Price, Type of sale, Number of rooms, Living Area, Fully equipped kitchen, Furnished, Open fire, Terrace, Garden, Surface of the land, Surface area of the plot of land, Number of facades, Swimming pool, State of the building in a csv file 




    # Store details in CSV
    with open('property_details.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Link", "Locality", "Subtype of property", "Type of sale", "Price", "Number of rooms", "Living Area", "Fully equipped kitchen"])
        writer.writeheader()
        for details in details_list:
            writer.writerow(details)
    print(f"Stored details of {len(details_list)} properties in property_details.csv")

def store_links(links):
    with open('property_links.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Link"])
        for link in links:
            writer.writerow([link])
    print(f"Stored {len(links)} links in property_links.csv")

# Main execution
all_links = fetch_all_links(main_url)
store_links(all_links)