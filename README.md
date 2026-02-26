# immo_eliza_scraping
I started working on README

Project Overview:
This project is the first phase of a data science mission for ImmoEliza. The goal is to build a high-quality dataset of the Belgian real estate market, consisting of at least 10,000 properties. This data will be used to train a Machine Learning model to predict house prices across Belgium.

The URL used for the project is the following:
"https://immovlan.be/en/real-estate?transactiontypes=for-sale,for-rent&propertytypes=apartment,house&propertysubtypes=apartment,ground-floor,duplex,penthouse,studio,loft,triplex,residence,villa,mixed-building,master-house,cottage,bungalow,chalet,mansion&sortdirection=ascending&sortby=price&noindex=1"

It filters houses and appartments for rent in Belgium.


Installation:
In order to run the scrap, Python needs to be installed.

1. Clone the repository:
git clone (Name of the repository)

2. Install required libraries:
pip install requests beautifulsoup4

3. Run the main script in order to start the collection process:
python.main.py

The script will first gather property links and then visit each link to extract detailed features, saving everything into a .csv file.

Technical Strategy:
Since websites often limit the number of results visible per search, this scraper uses a Dynamic Price-Batching approach:

1. Price Ranges: The scraper fetches properties in batches. Once it reaches the end of a batch, it looks at the price of the last house found and starts a new search from that price + €1. This ensures we bypass the "maximum page" limits and reach our 10,000-property goal.

2. Data Cleaning: We use Regular Expressions (re) to strip currency symbols and non-numeric characters, ensuring the dataset is clean and ready for numerical analysis. 

3. None Handling: Per requirements, any missing information is recorded as None to ensure the dataset remains uniform and easy to process with tools like Pandas.

Dataset Features:
The scraper extracts the following columns for each property:
- Locality (Postal code) 
- Property Type (House/Apartment) 
- Subtype (Bungalow, Mansion, etc.)
- Price 
- Living Area & Land Surface 
- Features: Kitchen equipment, Furnished, Open fire, Terrace, Garden, Swimming pool
- Building State: New, to be renovated, etc.

Challenges & Solutions:
1. Bot Detection: Implemented a custom User-Agent header to mimic a standard web browser and prevent access blocks. 

2. Data Integrity: Implemented a system to skip duplicates and ensure that "Project" details (new builds without specific prices) are excluded to keep the training data relevant for a prediction model.


