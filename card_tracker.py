import os
import shutil
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup as bs4
import time


temp_dir = "tmp"
psw_CT = os.environ.get('CT_PSW')
usr_CT = os.environ.get('CT_USR')
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"

@dataclass
class Card:
    name: str
    price: float
    link: str
    seller: str

@dataclass
class Filter:
    expansion: str 
    language: list # Inglese, Italiano, Tedesco, Francese, Spagnolo, Russo, Cinese, Giapponese, Portoghese change to your location language 
    condition: str # Near Mint, Lightly Played, Moderately Played, Heavily Played, Poor
    foil: bool
    tracked: bool
    continent: bool
    max_price: float

# Set up the browser
def driver_start():
    
    os.makedirs(temp_dir)
    os.environ["TMPDIR"] = temp_dir
    options = webdriver.FirefoxOptions()
    options.add_argument('-no-sandbox')
    # options.add_argument(f'-user-agent={user_agent}')
    # options.add_argument('-headless')  # Run Firefox in headless mode (no GUI)
    # options.binary_location = '/usr/snap/firefox'  # Set the path to the Firefox binary
    driver = webdriver.Firefox(options=options)
    driver.get(r'https://www.cardtrader.com/')
    wait = WebDriverWait(driver, 30)    # Set a wait timer before timing out
    print("Driver started")
    return driver, wait

def login_CT(driver, wait):
    driver.get(r'https://www.cardtrader.com/users/sign_in?locale=it')
    reject_cookies(driver)
    try:
        email_box = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-modal-static"]//input[@data-test-id="login-input-email"]')))
        email_box.send_keys(usr_CT)
        time.sleep(1)
        email_box.send_keys(Keys.TAB)

        psw_box = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-modal-static"]//input[@data-test-id="login-input-password"]')))
        psw_box.send_keys(psw_CT)
        time.sleep(1)
        psw_box.send_keys(Keys.ENTER)

        time.sleep(1)

        # Check if the login was successful
        wait.until(EC.presence_of_element_located((By.XPATH, '//i[@class="top-header__icons fas fa-shopping-cart ss-fw text-white"]')))
    except:
        print("Login failed")
        exit(1)
    else:
        print("Login successful")
        return driver, wait

def search_CT(driver, wait, search_term, filter):
    # Search for the card
    search_box = wait.until(EC.element_to_be_clickable((By.ID, 'manasearch-input')))
    driver.execute_script("arguments[0].click();", search_box)
    search_box.send_keys(search_term)
    time.sleep(1)
    search_box.send_keys(Keys.ENTER)
    print("Search term entered")

    
    # Get all the rows in the table
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[@data-gtm-name='"+search_term+"']")))
    print("Search term found")
    # Get the HTML of the page  
    html = driver.page_source
    soup = bs4(html, 'html.parser')
    rows = soup.find_all('tr', attrs={'data-product-id': True})

    # Initialize a variable to store the lowest price
    lowest_price = Card(name=search_term, price=None, link=driver.current_url, seller=None)

    for x in range(5) :
        if rows==[]:
            html = driver.page_source
            soup = bs4(html, 'html.parser')
            rows = soup.find_all('tr', attrs={'data-product-id': True})
        else:
            break
    if rows==[]:
        print("No results found")
        exit(1)

    # Iterate over each row
    for row in rows:
        if filter_card(filter, row):
            # Find the price in the current row
            price_element = row['gtm-price']

            # If a price was found
            if price_element:
                # Remove any non-numeric characters (like $) and convert to float
                price = float(price_element)

                # If this is the first price we've found, or it's lower than the current lowest price
                if lowest_price.price is None or price < lowest_price.price:
                    # Update the lowest price
                    lowest_price.price = price
                    lowest_price.seller = row.find('span', attrs={'class': 'd-sm-none font-weight-light-bold'}).text
                    print(lowest_price.price)
        

    # Return the lowest priced card
    # seller = wait.until(EC.presence_of_element_located((By.XPATH, '//tr[@gtm-price="'+str(lowest_price.price)+'"]//span[@class="d-sm-none font-weight-light-bold"]')))
    # lowest_price.seller = seller.text
    return lowest_price

def wishlist_search_CT(driver, wait, search_list, filter):
    driver.get(r'https://www.cardtrader.com/wishlists/new/')

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'deck-table')))

    # Get the HTML of the page
    html = driver.page_source
    soup = bs4(html, 'html.parser')

    # Find the button by its class
    buttons = driver.find_elements(By.CSS_SELECTOR, '.text-tertiary.hand')
    driver.execute_script("arguments[0].click();", buttons[2])

    # Get the paste box
    paste_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder]")))
    for search_term in search_list:
        paste_box.send_keys(search_term)
        paste_box.send_keys(Keys.ENTER)
    print("Search list entered")

    # Press the search button
    paste_box.send_keys(Keys.TAB, Keys.TAB, Keys.ENTER)

    # Get output of the search
    wait.until(lambda driver: driver.find_element(By.XPATH, "//*[contains(text(), '✔️')]") or driver.find_element(By.XPATH, "//*[contains(text(), '❗')]"))
    # exit if failure to find card/s
    output = [tag.string for tag in soup.find_all(lambda tag: tag.string is not None and tag.string.startswith("❗"))]
    if output:
        for error in output:
            print(error+" not found\n")
        exit(1)

    
    # confirm_button = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Import')]")))
    # confirm_button.click()
    paste_box.send_keys(Keys.TAB, Keys.TAB, Keys.ENTER)

    select_options_CT(driver, wait, filter)    

    # Get all prices
    wait.until(EC.invisibility_of_element((By.CSS_SELECTOR, '.fas.fa-spinner.fa-spin.fa-3x')))
    html = driver.page_source
    soup = bs4(html, 'html.parser')

    results = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//h2[@class='m-0 text-center']")))
    for result in results:
        if float(result.text[1:]) > filter.max_price:
            print("Price too high: "+result.text+"\n")
        else:
            print(result.text)

def select_options_CT(driver, wait, filter):
    html = driver.page_source
    soup = bs4(html, 'html.parser')
    
    check_all = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="check_all"]')))
    check_all.click()

    # Set the expansion 
    expansion = wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="setExpansionButton"]')))
    expansion.click()

    any = wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '"+filter.expansion+"')]")))
    any.click()

    # Set the language
    language = wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="setLanguageButton"]')))
    language.click()

    if len(filter.language) > 1:
        lan_string = ""
        for lan in filter.language:
            lan_string += lan + "+"
        lan_string = lan_string[:-1]
        language_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='"+lan_string+"']")))
        language_option.click()
    else:
        language_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='"+filter.language[0]+"']")))
        language_option.click()

    # Set the condition
    condition = wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="setConditionButton"]')))
    condition.click()

    nm_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='"+filter.condition+"']")))
    nm_option.click()

    # Set the Foil
    foil = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='setFoilButton']")))
    foil.click()

    if filter.foil:
        foil_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='true']")))
        foil_option.click()
    else:
        foil_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='false']")))
        foil_option.click()

    # Set only Tracked Cards
    if filter.tracked:
        tracked = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="only-tracked-checkbox"]')))
        tracked.click()

    # Set only User Continent 
    if filter.continent:
        continent = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="only-user-continent-checkbox"]')))
        continent.click()

    # Optimize the search
    optimize = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[@class='btn btn-lg btn-success btn-block nowrap ml-3 ml-md-0']")))
    optimize.click()

def login_CM(driver, wait):
    driver.get(r'https://www.cardmarket.com/en/Magic')
    time.sleep(2)
    try:
        email_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@named="username"]')))
        email_box.send_keys(usr_CT)
        time.sleep(1)
        email_box.send_keys(Keys.ENTER)

        psw_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="userPassword"]')))
        psw_box.send_keys(psw_CT)
        time.sleep(1)
        psw_box.send_keys(Keys.ENTER)

        time.sleep(1)

        # Check if the login was successful
        wait.until(EC.presence_of_element_located((By.XPATH, '//span[@text="00uno00"]')))
    except:
        print("Login failed")
    else:
        print("Login successful")
        return driver, wait

def req_CM():
    url = "https://www.cardmarket.com/en/Magic"
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1"
    }
    response = requests.get(url, headers=headers)
    print(response.status_code)

# def min_tot(card_list):
    
def filter_card(filter, row):
    soup = bs4(row.prettify(), 'html.parser')
    if filter.language:
        for lang in filter.language:
            if soup.find('span', attrs={'data-original-title': lang}):
                break
        else:
            return False
    if filter.condition:
        if not soup.find('span', attrs={'data-original-title': filter.condition}):
            return False
    if filter.max_price:
        if float(row['gtm-price']) > filter.max_price:
            return False
        
    return True

def reject_cookies(driver):
    # Assuming `driver` is your WebDriver object
    # Replace 'css_selector' with the actual CSS selector for the button
    wait = WebDriverWait(driver, 10)
    reject_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.iubenda-cs-reject-btn.iubenda-cs-btn-primary')))

    reject_button.click()

if __name__ == "__main__":

    firefox, sleep = driver_start()
    firefox, sleep = login_CT(firefox, sleep)
    # Search for the card
    print("strating search")
    filter = Filter("Indifferente", language=["EN", "IT"], condition="Near Mint", foil=False, tracked=True, continent=True, max_price=11)
    # print(search_CT(firefox, sleep, "Roaming Throne", filter))
    wishlist_search_CT(firefox, sleep, ["Roaming Throne"], filter)
    # req_CM()

    # Close the element window
    firefox.close()
    shutil.rmtree(temp_dir)