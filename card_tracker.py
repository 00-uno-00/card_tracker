import os
import shutil
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

# Set up the browser
def driver_start():
    
    os.makedirs(temp_dir)
    os.environ["TMPDIR"] = temp_dir
    options = webdriver.FirefoxOptions()
    options.add_argument('-no-sandbox')
    # options.add_argument('-headless')  # Run Firefox in headless mode (no GUI)
    # options.binary_location = '/usr/snap/firefox'  # Set the path to the Firefox binary
    driver = webdriver.Firefox(options=options)
    driver.get(r'https://www.cardtrader.com/')
    wait = WebDriverWait(driver, 30)    # Set a wait timer before timing out
    print("Driver started")
    return driver, wait

def login(driver, wait):
    driver.get(r'https://www.cardtrader.com/users/sign_in?locale=it')
    try:
        email_box = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@data-test-id="login-input-email"]')))
        email_box.send_keys(usr_CT)
        time.sleep(1)
        email_box.send_keys(Keys.ENTER)

        psw_box = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@data-test-id="login-input-password"]')))
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


def search(driver, wait, search_term):
    # Search for the card
    search_box = wait.until(EC.presence_of_element_located((By.ID, 'manasearch-input')))
    search_box.send_keys(search_term)
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
    lowest_price = None

    # Iterate over each row
    for row in rows:
        # Find the price in the current row
        price_element = row['gtm-price']

        # If a price was found
        if price_element:
            # Remove any non-numeric characters (like $) and convert to float
            price = float(price_element)

            # If this is the first price we've found, or it's lower than the current lowest price
            if lowest_price is None or price < lowest_price:
                # Update the lowest price
                lowest_price = price

    return lowest_price

def wishlist_search(driver, wait, search_list):
    driver.get(r'https://www.cardtrader.com/wishlists/new/')

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'deck-table')))

    # Get the HTML of the page
    html = driver.page_source
    soup = bs4(html, 'html.parser')

    # Find the button by its class
    buttons = wait.until(EC.presence_of_element_located((By.XPATH, "//a[text()='paste lists from your text files']")))
    buttons.click()

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

    select_options(driver, wait)    

    # Get all prices
    html = driver.page_source
    soup = bs4(html, 'html.parser')

    results = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//h2[@class='m-0 text-center']")))
    for result in results:
        print(result.text)




def select_options(driver, wait):
    html = driver.page_source
    soup = bs4(html, 'html.parser')

    check_all = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="check_all"]')))
    check_all.click()

    # Set the expansion 
    expansion = wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="setExpansionButton"]')))
    expansion.click()

    any = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='Any']")))
    any.click()

    # Set the language
    language = wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="setLanguageButton"]')))
    language.click()

    english_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='EN']")))
    english_option.click()

    # Set the condition
    condition = wait.until(EC.presence_of_element_located((By.XPATH, '//button[@id="setConditionButton"]')))
    condition.click()

    nm_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='Near Mint']")))
    nm_option.click()

    # Set the Foil
    foil = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='setFoilButton']")))
    foil.click()

    foil_option = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='false']")))
    foil_option.click()

    # Set only Tracked Cards
    tracked = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="only-tracked-checkbox"]')))
    tracked.click()

    # Set only User Continent 
    continent = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="only-user-continent-checkbox"]')))
    continent.click()

    # Optimize the search
    optimize = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[@class='btn btn-lg btn-success btn-block nowrap ml-3 ml-md-0']")))
    optimize.click()

    

if __name__ == "__main__":

    firefox, sleep = driver_start()
    firefox, sleep = login(firefox, sleep)
    # Search for the card
    print("stating search")
    # print(search(firefox, sleep, "Roaming Throne"))
    wishlist_search(firefox, sleep, ["Roaming Throne", "Cultivate", "Sol Ring"])

    # Close the element window
    firefox.close()
    shutil.rmtree(temp_dir)