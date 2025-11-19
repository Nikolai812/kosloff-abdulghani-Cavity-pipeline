import os
import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']


def upload_and_submit_pdb(driver, pdb_file_path, pdb_input):
    try:
        # Wait for the dropdown to be present
        dropdown_locator = (By.ID, "cavityInputType")
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(dropdown_locator)
        )

        # Use Select to choose the "PDB File" option
        select = Select(dropdown)
        select.select_by_visible_text("PDB File")

        # Wait for the file input to appear
        file_input_locator = (By.CSS_SELECTOR, "input[type='file'][accept='pdb']")
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(file_input_locator)
        )

        # Upload the PDB file
        file_input.send_keys(pdb_file_path)
        success_div_locator = (By.XPATH,
                               "//input[@type='file' and @accept='pdb']/following-sibling::div[text()='Success.']")
        submit_div = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(success_div_locator)
        )

        print(f"Successfully uploaded the file: {pdb_input}")
        time.sleep(1)

        # Wait for the Submit button to be clickable
        submit_button_locator = (By.CSS_SELECTOR, "button.btn.btn-primary[type='submit']")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(submit_button_locator)
        )

        # Scroll the submit button into view
        driver.execute_script("arguments[0].scrollIntoView();", submit_button)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(submit_button))
        # Use JavaScript to click the submit button
        driver.execute_script("arguments[0].click();", submit_button)
        print("Successfully clicked the Submit button")

    except Exception as e:
        print(f"An error occurred during upload and submit: {e}")
        raise

def write_cavity_results(driver, pdb_file_name_no_extension):
    try:
        # Wait for the Cavity Results table to be present
        table_locator = (By.CSS_SELECTOR, "div.accordion-collapse.show table.table")
        table = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(table_locator)
        )

        # Locate the More (3 dots) element in the first row
        more_button_locator = (By.CSS_SELECTOR, "tbody tr:first-child td:last-child div[style*='color: blue']")
        more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(more_button_locator)
        )

        # Scroll the More button into view
        driver.execute_script("arguments[0].scrollIntoView();", more_button)

        # Click the More button using JavaScript
        driver.execute_script("arguments[0].click();", more_button)
        print("Successfully clicked the More button in the first row")

    except Exception as e:
        print(f"An error occurred while writing cavity results: {e}")
        raise



def run_cavity_plus():
    # Extract configuration values
    config = load_config()
    chrome_driver_path = config['chrome_driver_path']
    cavity_plus_url = config['cavity_plus_url']
    input_dir = config['input_dir']
    pdb_input = config['pdb_input']

    # Construct the full path to the PDB file
    pdb_file_path = os.path.abspath(os.path.join(input_dir, pdb_input))
    pdb_file_name_no_extension = os.path.splitext(pdb_input)[0]

    # Set up Chrome options to automatically download files
    chrome_options = Options()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(script_dir, "output")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Set up the WebDriver with the specified path
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open the CavityPlus URL
        driver.get(cavity_plus_url)

        # Upload and submit the PDB file
        upload_and_submit_pdb(driver, pdb_file_path, pdb_input)

        # Wait for the Download results button to appear and become clickable
        download_button_locator = (By.CSS_SELECTOR, "button.btn.btn-link b")
        download_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable(download_button_locator)
        )
        print("Download results button is now visible and clickable")

        write_cavity_results(driver, pdb_file_name_no_extension)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        print("This is finally, going to quit driver")
        driver.quit()

    print("Cavity Plus script completed")

if __name__ == '__main__':
    run_cavity_plus()
