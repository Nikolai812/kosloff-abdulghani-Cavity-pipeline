import csv
import os
import configparser
from configparser import SectionProxy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

from file_namer import FileNamer, MethodType

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
        submit_div = WebDriverWait(driver, 50).until(
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



def write_cavity_results(driver, pdb_name, output_dir="output", pocket_limit= -1):
    try:
        # Wait for the Cavity Results table
        table_locator = (By.CSS_SELECTOR, "div.accordion-collapse.show table.table")
        table = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(table_locator)
        )

        # Locate ALL top-level rows
        rows = driver.find_elements(
            By.XPATH,
            "//button[.//b[normalize-space()='Download results']]"
            "/ancestor::div[contains(@class,'container')]"
            "//table[1]/tbody/tr[count(td)=7]"
        )

        total_rows = len(rows)
        print(f"Found {total_rows} cavity rows.")

        # Apply pocket limit if specified
        if pocket_limit > 0:
            if pocket_limit > total_rows:
                print(
                    f"WARNING: pocket_limit={pocket_limit} exceeds total cavities ({total_rows}). "
                    f"Processing all available cavities instead."
                )
                rows_to_process = rows  # safe
            else:
                print(f"Applying pocket limit: processing first {pocket_limit} cavities.")
                rows_to_process = rows[:pocket_limit]  # always safe
        else:
            rows_to_process = rows

        # Iterate only over the selected row

        # Create output subfolder
        output_path = os.path.join(os.getcwd(), output_dir, pdb_name)
        os.makedirs(output_path, exist_ok=True)

        # File names
        va_csv_filename = FileNamer.get_va_name(pdb_name, MethodType.CVPL) + ".csv"
        residues_csv_filename = FileNamer.get_residues_name(pdb_name, MethodType.CVPL) + ".csv"

        # Open CSVs
        with open(os.path.join(output_path, va_csv_filename), 'w', newline='', encoding='utf-8') as va_file, \
             open(os.path.join(output_path, residues_csv_filename), 'w', newline='', encoding='utf-8') as res_file:

            va_writer = csv.writer(va_file)
            res_writer = csv.writer(res_file)

            # Headers
            va_writer.writerow(['Cavity Number', 'Surface Area', 'Volume'])
            res_writer.writerow(['Cavity Number', 'Chain', 'Seq ID', 'AA'])

            # Iterate over actual row elements (stable)
            for cavity_index, row in enumerate(rows_to_process, start=1):
                print(f"\nProcessing cavity row {cavity_index}...")
                cavity_number = row.find_element(By.XPATH, "./td[1]").text.strip()
                if not cavity_number:
                    raise RuntimeError(f"Could not read cavity number for row index {cavity_index}")

                # --- CLICK MORE BUTTON INSIDE THIS ROW ---
                more_button = row.find_element(
                    By.CSS_SELECTOR,
                    "td:last-child div[style*='color: blue']"
                )

                driver.execute_script("arguments[0].scrollIntoView();", more_button)
                driver.execute_script("arguments[0].click();", more_button)
                print(f"Expanded details for row {cavity_index}")

                # Wait for the expanded detail <tr id='more_{cavity_number}'> to appear (and be visible)
                detail_tr_id = f"more_{cavity_number}"
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, detail_tr_id))
                )
                detail_tr = driver.find_element(By.ID, detail_tr_id)

                # Optionally wait until it has class 'collapse show' or is displayed
                WebDriverWait(driver, 10).until(
                    lambda d: 'show' in detail_tr.get_attribute("class") or detail_tr.is_displayed()
                )

                # Now scope lookups to the detail_tr only (relative XPath with '.' prefix)
                surface_area_td = detail_tr.find_element(
                    By.XPATH,
                    ".//th[contains(normalize-space(),'Surface Area')]/following-sibling::td"
                )
                volume_td = detail_tr.find_element(
                    By.XPATH,
                    ".//th[contains(normalize-space(),'Volume')]/following-sibling::td"
                )
                residues_td = detail_tr.find_element(
                    By.XPATH,
                    ".//th[contains(normalize-space(),'Residues')]/following-sibling::td"
                )

                # Extract texts
                surface_area = surface_area_td.text.strip()
                volume = volume_td.text.strip()
                residues_text = residues_td.text.strip()
                residues_list = [r.strip() for r in residues_text.split(',') if r.strip()]

                print(f"Surface Area: {surface_area}, Volume: {volume}, #residues: {len(residues_list)}")

                # --- WRITE VA DATA ---
                va_writer.writerow([cavity_index, surface_area, volume])

                # --- WRITE RESIDUES ---
                line_num = len(residues_list)
                for residue in residues_list:
                    aa, seq_id, chain = residue.split('-')
                    res_writer.writerow([cavity_index, chain, seq_id, aa])

                print(f"Successfully wrote {line_num} lines for cavity {cavity_index}")

                # --- COLLAPSE AGAIN ---
                driver.execute_script("arguments[0].click();", more_button)
                print(f"Collapsed details for row {cavity_index}")

            print("\nAll cavities processed successfully.")

    except Exception as e:
        print(f"An error occurred while writing cavity results: {e}")
        raise


def run_cavity_plus(pdb_input: str, config: SectionProxy):
    # Extract configuration values
    #config = load_config()
    chrome_driver_path = config['chrome_driver_path']
    cavity_plus_url = config['cavity_plus_url']
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    pocket_limit = int(config['pocket_limit'])
    pdb_name=os.path.splitext(pdb_input)[0]

    # Construct the full path to the PDB file
    pdb_file_path = os.path.abspath(os.path.join(input_dir, pdb_input))

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

        write_cavity_results(driver, pdb_name, output_dir, pocket_limit=pocket_limit)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser
        print("This is finally, going to quit driver")
        driver.quit()

    print("Cavity Plus script completed")

if __name__ == '__main__':
    config = load_config()
    chrome_driver_path = config['chrome_driver_path']
    cavity_plus_url = config['cavity_plus_url']
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    pdb_input = config['pdb_input']
    run_cavity_plus(pdb_input, config)
