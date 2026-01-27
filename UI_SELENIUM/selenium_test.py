import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from chrome_driver_factory import create_chrome_driver

#############################################################################################
# This is just a script to verify selenium usage on the given environment
# The google chrome is to be preinstalled, chrome driver path is hardcoded
# Script just  opens the web page, sleeps 5 sec and closes the browser
#############################################################################################

def run_test():
    # Extract configuration values
    chrome_driver_path = 'C:\Windriver\chromedriver-win64\chromedriver.exe' #"/mnt/c/Windriver/chromedriver-win64/chromedriver.exe" #
    prankweb_url = 'https://prankweb.cz/'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Set up Chrome options to automatically download files
    # chrome_options = Options()
    #
    # download_dir = script_dir
    #
    # prefs = {
    #     "download.default_directory": download_dir,
    #     "download.prompt_for_download": False,
    #     "download.directory_upgrade": True,
    #     "safebrowsing.enabled": False
    # }
    # chrome_options.add_experimental_option("prefs", prefs)
    #
    # # Set up the WebDriver with the specified path
    # service = Service(chrome_driver_path)
    # driver = webdriver.Chrome(service=service, options=chrome_options)

    driver = create_chrome_driver(chrome_driver_path, script_dir, headless = True)

    try:
        # Open the Prankweb URL
        driver.get(prankweb_url)

        # Select the "Custom structure" radio button
        custom_structure_radio = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "input-user-file"))
        )
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(custom_structure_radio))
        custom_structure_radio.click()

        #Waiting download to complete
        time.sleep(5)

        tagname_radio = custom_structure_radio.tag_name
        radioval = custom_structure_radio.get_attribute("value")

        # PAGE TITLE ELEMENT
        h1_css = driver.find_element(By.CSS_SELECTOR, "h1.text-center")
        txt = h1_css.text

        print(f"The tag name is: {tagname_radio}")
        print(f"The text is: {txt}")
        print(f"The radioval is: {radioval}")

        assert txt.startswith('PrankWeb:') == True, f"Wrong text {txt} does not start as expected"
        assert radioval == 'input-user-file'
        assert tagname_radio == 'input'
        print("Test completed.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        print("This is finally, going to quit driver")
        driver.quit()


    print("Selenium test script completed")


if __name__ == '__main__':
    run_test()

