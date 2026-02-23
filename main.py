# importing the libraries
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import random
# import pandas as pd

url = "https://immovlan.be/en/real-estate/house/for-sale?province=limburg&page=1"
MAX_PAGES = None

# Create Chrome options for headless browsing
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")  # Often needed in Linux environments
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resources

# Create driver with these options
driver = webdriver.Chrome(options=chrome_options)
driver.get(url)
wait = WebDriverWait(driver, 10)

# Set the cookie_url variable (1 line)
cookie_url = root_=url + '/cookie'

# Query the enpoint, set the cookies variable and display it (2 lines)
cookies = requests.get(cookie_url).cookies
print(cookies)




"""
what we need to scrape from the website: villa:
	•	Locality Uccle
    <font dir="auto" style="vertical-align: inherit;">- Uccle </font>

	•	Type of property (House/apartment):  House
    <font dir="auto" style="vertical-align: inherit;">
                    House for rent </font>

	•	Subtype of property (Bungalow, Chalet, Mansion, ...): Entire home
    <font dir="auto" style="vertical-align: inherit;">
            Entire home. Between the Observatory and Uccle train station, in a residential area close to shops and public transport: superb furnished villa on 4 levels in the middle of a 12-acre south-facing green plot, comprising 5 bedrooms ranging from 20 to 40 m2, workspaces, indoor pool and wellness area, terraces and garden. Outdoor parking for 3-4 cars.
            </font>

	•	Price: 20000€/month
    <font dir="auto" style="vertical-align: inherit;">€20,000
                        </font>

	•	Type of sale (Exclusion of life sales): Rent
    <font dir="auto" style="vertical-align: inherit;">
                    House for rent </font>

	•	Number of rooms: 5 bedrooms 
        from discription

	•	Living Area: no exact data 

	•	Fully equipped kitchen (Yes/No): Because it is Furneshed it is yes
    <font dir="auto" style="vertical-align: inherit;">Furniture</font>


	•	Furnished (Yes/No): Yes
    <font dir="auto" style="vertical-align: inherit;">Furniture</font>

	•	Open fire (Yes/No): No fire no information 

	•	Terrace (Yes/No): Yes
    <font dir="auto" style="vertical-align: inherit;">Yes</font>

    ◦	If yes: Area: no information

	•	Garden (Yes/No): Yes
    <div>
                                <h4><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">Garden</font></font></h4>
                                <p><font dir="auto" style="vertical-align: inherit;"><font dir="auto" style="vertical-align: inherit;">Yes</font></font></p>
                            </div>

	◦	If yes: Area: no information
	•	Surface of the land: 480 
    <font dir="auto" style="vertical-align: inherit;">480 m²</font>

	•	Surface area of the plot of land: 12-acre convert to m2 = 48561.6 m2
    the area of total floors 

	•	Number of facades: no information

	•	Swimming pool (Yes/No): Yes 
    <font dir="auto" style="vertical-align: inherit;">Outdoor pool</font> 

	•	State of the building (New, to be renovated, ...): no information

"""

"""
what we need to scrape from the website:
	•	Locality 1000 Brussels 
    <font dir="auto" style="vertical-align: inherit;">1000 Brussels</font>

	•	Type of property (House/apartment) Apartment
    <font dir="auto" style="vertical-align: inherit;">
                    Apartment for rent </font>

	•	Subtype of property (Bungalow, Chalet, Mansion, ...): penthouse

<font dir="auto" style="vertical-align: inherit;">
            Discover this exceptional 540m² penthouse (according to the Energy Performance Certificate), available for immediate occupancy after a complete renovation by Claire Bataille. The main entrance to the apartment is in the reception hall, which leads to the formal dining room, cloakroom, and guest toilet. On one side, you'll find the large, fully equipped kitchen with Miele appliances, a pantry, and a staff toilet. A family room with a gas fireplace, TV, and sound system adjoins this part of the apartment. On the other side, a large reception room with a small bar area for aperitifs opens onto a first southwest-facing terrace with views of the Bois de la Cambre. Two bedrooms are also located on this floor, each with its own bathroom, toilet, and dressing room. Marble, solid Macassar ebony, and patinated metals are used throughout the bedrooms. On the upper floor, a second living room with a separate kitchenette provides access to a second terrace, which offers even more expansive views of the Bois de la Cambre trees. A guest toilet and storage areas complete this reception area. A third bedroom and a walk-in closet offering over 40 linear meters of storage space complete the apartment's layout. Air conditioning, home automation, an integrated sound system, and exceptional natural materials are features found throughout the apartment; nothing has been left to chance. A cellar, laundry room, wine cellar, and triple garage are included in the rental. An au pair apartment is available as an option in the basement. Energy Performance Certificate (EPC) rating: C. A monthly provision of €2,000 covers the maintenance of common areas and grounds, concierge services, and hot water and heating. Available immediately!
            </font>
    
	•	Price: 9000€/month
    <font dir="auto" style="vertical-align: inherit;">€9,000
                        </font>

	•	Type of sale (Exclusion of life sales): Rent
    <font dir="auto" style="vertical-align: inherit;">
                    Apartment for rent </font>

	•	Number of rooms: 2
    <font dir="auto" style="vertical-align: inherit;">Number of bedrooms</font>

	•	Living Area: 540 
    <font dir="auto" style="vertical-align: inherit;">Living area</font>

	•	Fully equipped kitchen (Yes/No): Yes
    <font dir="auto" style="vertical-align: inherit;">
            Discover this exceptional 540m² penthouse (according to the Energy Performance Certificate), available for immediate occupancy after a complete renovation by Claire Bataille. The main entrance to the apartment is in the reception hall, which leads to the formal dining room, cloakroom, and guest toilet. On one side, you'll find the large, fully equipped kitchen with Miele appliances, a pantry, and a staff toilet. A family room with a gas fireplace, TV, and sound system adjoins this part of the apartment. On the other side, a large reception room with a small bar area for aperitifs opens onto a first southwest-facing terrace with views of the Bois de la Cambre. Two bedrooms are also located on this floor, each with its own bathroom, toilet, and dressing room. Marble, solid Macassar ebony, and patinated metals are used throughout the bedrooms. On the upper floor, a second living room with a separate kitchenette provides access to a second terrace, which offers even more expansive views of the Bois de la Cambre trees. A guest toilet and storage areas complete this reception area. A third bedroom and a walk-in closet offering over 40 linear meters of storage space complete the apartment's layout. Air conditioning, home automation, an integrated sound system, and exceptional natural materials are features found throughout the apartment; nothing has been left to chance. A cellar, laundry room, wine cellar, and triple garage are included in the rental. An au pair apartment is available as an option in the basement. Energy Performance Certificate (EPC) rating: C. A monthly provision of €2,000 covers the maintenance of common areas and grounds, concierge services, and hot water and heating. Available immediately!
            </font>

	•	Furnished (Yes/No): YEs
    <font dir="auto" style="vertical-align: inherit;">
            Discover this exceptional 540m² penthouse (according to the Energy Performance Certificate), available for immediate occupancy after a complete renovation by Claire Bataille. The main entrance to the apartment is in the reception hall, which leads to the formal dining room, cloakroom, and guest toilet. On one side, you'll find the large, fully equipped kitchen with Miele appliances, a pantry, and a staff toilet. A family room with a gas fireplace, TV, and sound system adjoins this part of the apartment. On the other side, a large reception room with a small bar area for aperitifs opens onto a first southwest-facing terrace with views of the Bois de la Cambre. Two bedrooms are also located on this floor, each with its own bathroom, toilet, and dressing room. Marble, solid Macassar ebony, and patinated metals are used throughout the bedrooms. On the upper floor, a second living room with a separate kitchenette provides access to a second terrace, which offers even more expansive views of the Bois de la Cambre trees. A guest toilet and storage areas complete this reception area. A third bedroom and a walk-in closet offering over 40 linear meters of storage space complete the apartment's layout. Air conditioning, home automation, an integrated sound system, and exceptional natural materials are features found throughout the apartment; nothing has been left to chance. A cellar, laundry room, wine cellar, and triple garage are included in the rental. An au pair apartment is available as an option in the basement. Energy Performance Certificate (EPC) rating: C. A monthly provision of €2,000 covers the maintenance of common areas and grounds, concierge services, and hot water and heating. Available immediately!
            </font>


	•	Open fire (Yes/No): yes 
    <font dir="auto" style="vertical-align: inherit;">Open fire</font>

	•	Terrace (Yes/No) Yes
    <font dir="auto" style="vertical-align: inherit;">Furnished terrace</font>

	◦	If yes: Area

	•	Garden (Yes/No) no
    <font dir="auto" style="vertical-align: inherit;">Garden</font>

	◦	If yes: Area

	•	Surface of the land: no information

	•	Surface area of the plot of land: no information

	•	Number of facades: 4
    <font dir="auto" style="vertical-align: inherit;">Number of facades</font>
	
    •	Swimming pool (Yes/No): no information

	•	State of the building (New, to be renovated, ...)  new 
    <font dir="auto" style="vertical-align: inherit;">Condition of the property</font>

"""