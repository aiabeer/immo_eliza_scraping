#from urllib import response

import scrapy
import requests
#import response
import re


class ImmoElizaSpider(scrapy.Spider):
    name = "immo_eliza"
    allowed_domains = ["immovlan.be"]
    start_urls = ["https://immovlan.be/en/real-estate?transactiontypes=for-rent,in-public-sale&propertytypes=house,apartment&propertysubtypes=residence,villa,mixed-building,master-house,cottage,bungalow,chalet,mansion,apartment,penthouse,ground-floor,duplex,studio,loft,triplex&noindex=1"]

    def parse(self, response):
        # Extract property links
        links = response.xpath('//a[contains(@href, "/detail/")]/@href').getall()
        for link in set(links):
            yield response.follow(link, callback=self.parse_property)

        # Find Next Page button
        
        next_page = response.css('a.pagination__next::attr(href)').get()
        
        if not next_page:
            next_page = response.xpath('//a[@rel="next"]/@href').get()
            
        if not next_page:
            next_page = response.xpath('//a[contains(text(), "Next")]/@href').get()

        if next_page:
            self.logger.info(f"SUCCESS: Found next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)
        else:
            self.logger.warning("WARNING: No next page found. Check your selectors!")
        

    def parse_property(self, response):
        # Locality (e.g., '1060 - Sint-Gillis')
        raw_text = response.css('.city-line::text').get(default='').strip()
        locality = " ".join(raw_text.split()[1:]) 
        
        # Type of property
        """
        tag = <span class="detail__header_title_main">
                    Apartment for rent <span class="d-none d-lg-inline">- Somme-Leuze</span> <span class="vlancode">VBD88362</span>
                </span>
        """
        # Extract "Apartment for rent - Sint-Gillis RBV31374"
        full_text = response.css('.detail__header_title_main ::text').get(default='').strip()
        # Split by space and take the first word: "Apartment"
        property_type = full_text.split()[0]
    
        # Price
        # Grab all text nodes within the price span
        raw_price_list = response.css('.detail__header_price_data ::text').getall()
        # Join the list into one string: " 1 750 € "
        price_string = "".join(raw_price_list)
        # Use Regex to extract only the numbers: "1750"
        price = "".join(re.findall(r'\d+', price_string))

        
        # Subtype Extraction Logic (First two words of the description)
        """
        # tag = <div class="description w-100 col-12">
        <h2 class="padding-top-10">Description</h2>
        <div class="dynamic-description active" data-height="200" style="height: 200px;">
            Discover this modern and spacious apartment for rent in Somme-Leuze, perfect for those seeking comfort and contemporary design in a peaceful setting. Situated in a recently built residence from 2023, this property offers a generous living space of 96 square meters, comprising two bedrooms, a well-appointed living room with an integrated kitchen, and modern amenities designed for ease and functionality. The apartment is located on the first floor of a 4-unit building, which features energy-efficient systems such as a central heating system powered by a heat pump, triple-glazed windows for optimal insulation, and an water softener. The residence boasts a recent construction standard, ensuring low energy consumption with an EPC score of A—60 kWh/m² per year—highlighting its eco-friendly credentials. This apartment's interior layout emphasizes comfort and practicality, with a total of two bedrooms measuring 10 m² and 12.5 m², a bathroom with a shower, and a separate toilet. The living area, approximately 38 m², is bright and open, providing ample space for relaxation and entertaining. The property also includes convenient features such as a laundry area, a cellar in the basement, and secure parking spaces—two outdoor spots—complementing the residence’s outdoor amenities. Stepping outside, you'll find a generous 24 m² terrace along with a garden area, offering an excellent space for outdoor living, gardening pursuits, or entertaining guests. The south-facing orientation ensures ample sunlight throughout the day, enhancing the overall comfort of the living environment. Located at Route de Marche 7 M in Somme-Leuze, this apartment provides a peaceful yet accessible setting. The area combines rural tranquility with practical connectivity, making it suitable for individuals or families looking for a serene lifestyle without sacrificing convenience. Available starting from April 1, 2026, this property is offered at €1,000 per month, with charges of €25 covering communal upkeep. With its modern features, energy efficiency, and appealing outdoor spaces, this apartment presents an excellent opportunity for tenants seeking a high-quality rental in this charming Belgian region. For further information or to arrange a viewing, please contact the leasing agency via email at  <a href="#" class="description-contact-link"> Contact </a>  or call  <i class="fas fa-phone-alt">  </i>   <span class="description-phone">  <a href="#" class="description-phone-show"> Tel </a>  <a href="tel:+32 85 84 41 91" class="description-phone-hidden"> 085/84.41.91 </a>  </span> . Take the next step towards your new home today.  <br>    <p class="font-italic generated-description mt-2">  * This text was generated using an artificial intelligence.  </p>  
            <a class="dynamic-description-show-more">
                Show all
                <i class="mi mi-arrow-b"></i>
            </a>
            <a class="dynamic-description-show-less">
                Show less
                <i class="mi mi-arrow-t"></i>
            </a>
        </div>
    </div>

        """
        # Extract the full description text 
        full_description = response.css('div.description-class::text').get(default='').strip()
        # Split the text into words and take the first two
        # Creating a list: ["Beautiful", "apartment", "of", "+-100m²", ...]
        words = full_description.split()
        subtype = " ".join(words[:2]) if len(words) >= 2 else full_description


        # Type of sale (Exclude life sales logic)
        # Extract "Apartment for rent - Sint-Gillis RBV31374"
        full_text = response.css('.detail__header_title_main ::text').get(default='').strip()
        # Split by space and take the first word: "Apartment"
        type_of_sale = full_text.split()[2]

        # Basic Room/Area Info
        # Finds the <h4> with the specific text, then gets the <p> right after it
        rooms = response.xpath('//h4[contains(text(), "Number of bedrooms")]/following-sibling::p/text()').get(default='0').strip()
        nb_rooms = int(rooms) if rooms.isdigit() else 0

        area = response.xpath('//h4[contains(text(), "Livable surface")]/following-sibling::p/text()').re_first(r'\d+')
        living_area = int(area) if area and area.isdigit() else 0

        # Kitchen (Checks if it contains 'Equipped')
        #kitchen_raw = response.xpath('//h4[contains(text(), "Number of bathrooms")]/following-sibling::p/text()').get(default='0').strip()
        #kitchen = int(kitchen_raw) if kitchen_raw.isdigit() else 0 

        furnished_text = response.xpath('//h4[contains(text(), "Furnished")]/following-sibling::p/text()').get(default='No').strip().lower()
        kitchen_equipped = 1 if furnished_text == "yes" else 0
    
        # Furnished
        furnished_text = response.xpath('//h4[contains(text(), "Furnished")]/following-sibling::p/text()').get(default='No').strip().lower()
        furnished = 1 if furnished_text == "yes" else 0
    
        # Open Fire
        description_text = response.css('div.dynamic-description ::text').getall()
        full_text = " ".join(description_text).lower()
        #   Check for "open fire" or "fireplace"
        open_fire = 1 if "open fire" in full_text or "fireplace" in full_text else 0
   
        # Swimming Pool
        swimming_pool = 1 if "swimming pool" in full_text else 0
   

        # Terrace
        terrace_text = response.xpath('//h4[contains(text(), "Terrace")]/following-sibling::p/text()').get(default='No').strip().lower()
        terrace = 1 if terrace_text == "yes" else 0
    
        if terrace == 1:
            terrace_area = response.xpath('//h4[contains(text(), "Surface terrace")]/following-sibling::p/text()').re_first(r'\d+')
        else:
            terrace_area = "0"
    
        # Garden Logic
        garden_text = response.xpath('//h4[contains(text(), "Garden")]/following-sibling::p/text()').get(default='No').strip().lower()
        garden = 1 if garden_text == "yes" else 0
    
        if garden == 1:
            garden_area = response.xpath('//h4[contains(text(), "Surface garden")]/following-sibling::p/text()').re_first(r'\d+')
        else:
            garden_area = "0"
    
    
        #surface_land = get_tech_val("Land surface")
        #plot_surface = get_tech_val("Plot surface")
        #facades = get_tech_val("Facades")
        #building_state = get_tech_val("Condition")

        yield {
            'locality': locality,
            'property_type': property_type,
            'subtype': subtype,
            'price': price,
            'type_of_sale': type_of_sale,
            'nb_rooms': nb_rooms,
            'living_area': living_area,
            'kitchen_equipped': kitchen_equipped,
            'furnished': furnished,
            'open_fire': open_fire,
            'terrace': terrace,
            'terrace_area': terrace_area,
            'garden': garden,
            'garden_area': garden_area,
            #'surface_land': surface_land,
            #'plot_surface': plot_surface,
            #'facades': facades,
            #'swimming_pool': swimming_pool,
            #'building_state': building_state,
            'url': response.url
       }
