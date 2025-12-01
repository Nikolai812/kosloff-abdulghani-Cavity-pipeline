import os
import csv

import configparser
from configparser import SectionProxy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil
import time
import zipfile

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']

def only_unzip_and_process():
    chrome_driver_path = config['chrome_driver_path']
    prankweb_url = config['prank_web_url']
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    prankweb_temp = config['prankweb_temp']
    pocket_limit = int(config['pocket_limit'])
    pdb_name = os.path.splitext(pdb_input)[0]

    # Construct the full path to the PDB file
    pdb_file_path = os.path.abspath(os.path.join(input_dir, pdb_input))

    # Set up Chrome options to automatically download files
    chrome_options = Options()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    download_dir = os.path.join(script_dir, output_dir, prankweb_temp)
    #unpack_zip_in_directory(download_dir)
    process_prankweb_output(download_dir)

def run_prankweb(pdb_input: str, config: SectionProxy):
    # Extract configuration values
    chrome_driver_path = config['chrome_driver_path']
    prankweb_url = config['prank_web_url']
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    prankweb_temp = config['prankweb_temp']
    pocket_limit = int(config['pocket_limit'])
    pdb_name = os.path.splitext(pdb_input)[0]

    # Construct the full path to the PDB file
    pdb_file_path = os.path.abspath(os.path.join(input_dir, pdb_input))

    # Set up Chrome options to automatically download files
    chrome_options = Options()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    download_dir = os.path.join(script_dir, output_dir,prankweb_temp)
    # Create the directory (or clear it if it exists and is not empty)
    if os.path.exists(download_dir):
        if os.listdir(download_dir):  # Check if directory is not empty
            print(f"Warning: Directory '{download_dir}' exists and is not empty. Clearing it...")
            shutil.rmtree(download_dir)  # Delete the directory and all its contents
        else:
            print(f"Directory '{download_dir}' exists and is empty. Reusing it.")
    else:
        print(f"Directory '{download_dir}' does not exist. Creating it...")

    os.makedirs(download_dir, exist_ok=True)  # Create the directory (if it doesn't exist)
    print(f"Directory '{download_dir}' is ready for downloads.")

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
        # Open the Prankweb URL
        driver.get(prankweb_url)

        # Select the "Custom structure" radio button
        custom_structure_radio = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "input-user-file"))
        )
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(custom_structure_radio))
        custom_structure_radio.click()

        # Upload the PDB file
        # Upload the PDB file using the correct locator
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='user-file']"))
        )
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(file_input))
        driver.execute_script("arguments[0].scrollIntoView();", file_input)
        file_input.send_keys(pdb_file_path)
        time.sleep(5)

        # Wait for the Submit button to be clickable and click it
        submit_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "submit-button"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", submit_button)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(submit_button))
        submit_button.click()

        # Wait for the Info tab to appear and click it (using CSS selector)
        info_tab_css = WebDriverWait(driver, 120).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[role='tab'][id='simple-tab-1']"))
        )
        info_tab_css.click()

        # Wait for the prediction to complete and the download button to appear
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                                        "//button[.//a[text()='Download prediction data']]"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", download_button)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(download_button))
        download_button.click()
        #Waiting download to complete
        time.sleep(5)

        print("Prediction completed. Results should be downloaded automatically.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        print("This is finally, going to quit driver")
        driver.quit()

    print("P2Rank script completed")

def unpack_zip_in_directory(download_dir):
    """
    Unpacks the single expected .zip file in the specified directory.
    Args:
        download_dir (str): Path to the directory containing the .zip file.
    Returns:
        str: Path to the extracted directory, or None if no .zip file was found.
    """
    # List all .zip files in the directory
    zip_files = [f for f in os.listdir(download_dir) if f.endswith('.zip')]

    if not zip_files:
        print(f"No .zip files found in '{download_dir}'.")
        return None
    elif len(zip_files) > 1:
        print(f"Warning: Multiple .zip files found in '{download_dir}'. Using the first one: {zip_files[0]}")

    # Use the first .zip file found
    zip_path = os.path.join(download_dir, zip_files[0])

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)
        print(f"Successfully extracted '{zip_path}' to '{download_dir}'.")
        return download_dir
    except zipfile.BadZipFile:
        print(f"Error: '{zip_path}' is not a valid .zip file.")
        return None
    except Exception as e:
        print(f"Error extracting '{zip_path}': {e}")
        return None


def process_prankweb_output(download_dir):
    """
    Processes the PRANKWeb output files in the specified directory.
    Args:
        download_dir (str): Path to the directory containing the output files.
    Returns:
        tuple: (cav_residues, res_label_name) dictionaries, or (None, None) if files are missing.
    """
    # Initialize dictionaries
    cav_residues = {}
    res_label_name = {}

    # Define expected filenames
    predictions_file = "structure.pdb_predictions.csv"
    residues_file = "structure.pdb_residues.csv"

    # Check if files exist
    if not os.path.exists(os.path.join(download_dir, predictions_file)):
        print(f"Error: '{predictions_file}' not found in '{download_dir}'.")
        return None, None
    if not os.path.exists(os.path.join(download_dir, residues_file)):
        print(f"Error: '{residues_file}' not found in '{download_dir}'.")
        return None, None

    # Read structure.pdb_predictions.csv into cav_residues
    with open(os.path.join(download_dir, predictions_file), mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                stripped_row = {k.strip(): v.strip() for k, v in row.items()}
                cavity_number = int(stripped_row['rank'])
                residue_ids = stripped_row['residue_ids']
                cav_residues[cavity_number] = residue_ids
            except KeyError:
                print(f"Warning: Missing 'rank' or 'residue_ids' column in '{predictions_file}'.")
            except ValueError:
                print(f"Warning: 'rank' value '{row['rank']}' is not an integer.")

    # Read structure.pdb_residues.csv into res_label_name
    with open(os.path.join(download_dir, residues_file), mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                stripped_row = {k.strip(): v.strip() for k, v in row.items()}
                residue_label = stripped_row['residue_label']
                residue_name = stripped_row['residue_name']
                res_label_name[residue_label] = residue_name
            except KeyError:
                print(f"Warning: Missing 'residue_label' or 'residue_name' column in '{residues_file}'.")

    return cav_residues, res_label_name



if __name__ == '__main__':
    config = load_config()
    chrome_driver_path = config['chrome_driver_path']
    print("Driver path: " + chrome_driver_path)
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    pdb_input = config['pdb_input']
    #run_prankweb(pdb_input, config)
    only_unzip_and_process()
