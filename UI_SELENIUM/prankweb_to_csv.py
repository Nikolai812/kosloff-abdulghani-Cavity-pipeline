import os
import csv

from configparser import SectionProxy
from datetime import datetime
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd

import shutil
import time
import zipfile

from chrome_driver_factory import create_chrome_driver
from file_namer import FileNamer, MethodType
from utils import str_to_bool, load_config


logger = logging.getLogger(__name__)

def only_unzip_and_process(pdb_input: str, config: SectionProxy):
    output_dir = config['output_dir']
    prankweb_temp = config['prankweb_temp']
    pdb_name = os.path.splitext(pdb_input)[0]

    script_dir = os.path.dirname(os.path.abspath(__file__))

    download_dir = os.path.join(script_dir, output_dir, prankweb_temp, pdb_name)
    unpack_zip_in_directory(download_dir)
    process_prankweb_output(download_dir, pdb_name, output_dir)
    delete_directory(download_dir)


def delete_directory(download_dir):
    """
    Deletes the specified directory and all its contents.
    Args:
        download_dir (str): Path to the directory to be deleted.
    """
    try:
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
            logger.info(f"Directory '{download_dir}' and its contents have been deleted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
        else:
            logger.info(f"Directory '{download_dir}' does not exist. No action taken at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"Warning: Failed to delete directory '{download_dir}'. Error: {e} \n at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def run_prankweb(pdb_input: str, config: SectionProxy):
    # Extract configuration values
    chrome_driver_path = config['chrome_driver_path']
    prankweb_url = config['prank_web_url']
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    prankweb_temp = config['prankweb_temp']
    pocket_limit = int(config['pocket_limit'])
    headless = config['chrome_headless_mode']
    pdb_name = os.path.splitext(pdb_input)[0]

    # Construct the full path to the PDB file
    pdb_file_path = os.path.abspath(os.path.join(input_dir, pdb_input))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(script_dir, output_dir, prankweb_temp, pdb_name)

    # Create the directory (or clear it if it exists and is not empty)
    if os.path.exists(download_dir):
        if os.listdir(download_dir):  # Check if directory is not empty
            logger.info(f"Warning: Directory '{download_dir}' exists and is not empty. Clearing it... at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            shutil.rmtree(download_dir)  # Delete the directory and all its contents
        else:
            logger.info(f"Directory '{download_dir}' exists and is empty. Reusing it.")
    else:
        logger.info(f"Directory '{download_dir}' does not exist. Creating it... at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    os.makedirs(download_dir, exist_ok=True)  # Create the directory (if it doesn't exist)
    print(f"Directory '{download_dir}' is ready for downloads.")

    use_headless_mode = str_to_bool(headless)
    driver = create_chrome_driver(chrome_driver_path, download_dir, use_headless_mode)

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

        logger.info(f"Prediction completed. Results should be downloaded automatically at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

    except Exception as e:
        logger.info(f"An error occurred: {e} \n at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"err_p2rk_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
    finally:
        # Close the browser
        logger.info("Prank2Web finally, going to quit driver")
        driver.quit()

    only_unzip_and_process(pdb_input, config)
    logger.info(f"P2Rank script completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

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
        logger.info(f"No .zip files found in '{download_dir}'.")
        return None
    elif len(zip_files) > 1:
        logger.info(f"Warning: Multiple .zip files found in '{download_dir}'. Using the first one: {zip_files[0]}")

    # Use the first .zip file found
    zip_path = os.path.join(download_dir, zip_files[0])

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)
        logger.info(f"Successfully extracted '{zip_path}' to '{download_dir}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
        return download_dir
    except zipfile.BadZipFile as e:
        logger.error(f"Error: '{zip_path}' is not a valid .zip file. at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
        logger.error(e)
        return None
    except Exception as e:
        logger.error(f"Error extracting '{zip_path}': {e} \n at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
        return None


def process_prankweb_output(download_dir, pdb_name, output_dir):
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
        logger.error(f"Error: '{predictions_file}' not found in '{download_dir}'.")
        return None, None
    if not os.path.exists(os.path.join(download_dir, residues_file)):
        logger.error(f"Error: '{residues_file}' not found in '{download_dir}'.")
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
                logger.error(f"Warning: Missing 'rank' or 'residue_ids' column in '{predictions_file}'.")
            except ValueError:
                logger.error(f"Warning: 'rank' value '{row['rank']}' is not an integer.")

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
                logger.warning(f"Missing 'residue_label' or 'residue_name' column in '{residues_file}'.")

    output_table = prepare_output_table(cav_residues, res_label_name)

    ## write_csv(output_table, pdb_name, output_dir)
    write_xlsx(output_table, pdb_name, output_dir)


    return cav_residues, res_label_name


def prepare_output_table(cav_residues, res_label_name):
    """
    Prepares the output table for .csv and .xlsx files.
    Args:
        cav_residues (dict): Dictionary with cavity numbers as keys and residue IDs as values.
        res_label_name (dict): Dictionary with residue labels as keys and residue names as values.
    Returns:
        list: List of dictionaries, each representing a row in the output table.
    """
    output_table = []

    for cavity_number, residue_ids_str in cav_residues.items():
        residue_ids = residue_ids_str.split()  # Split by spaces

        for residue_id in residue_ids:
            chain, seq_id = residue_id.split('_')  # Split by '_'
            aa = res_label_name.get(seq_id, 'Unknown')  # Look up AA in res_label_name

            row = {
                "Cavity Number": cavity_number,
                "Chain": chain,
                "Seq ID": seq_id,
                "AA": aa
            }
            output_table.append(row)

    return output_table


def write_csv(output_table, pdb_name, output_dir):
    """
    Writes the output table to a .csv file.
    Args:
        output_table (list): List of dictionaries representing the output table.
        pdb_name (str): Name of the PDB file (used for the output filename).
        output_dir (str): Directory where the output file will be saved.
    """

    # Create output subfolder
    output_or_subfolder = os.path.join(os.getcwd(), output_dir, pdb_name)
    os.makedirs(output_or_subfolder, exist_ok=True)

    output_filename = FileNamer.get_residues_name(pdb_name, MethodType.P2RK) + ".csv"
    output_path = os.path.join(output_or_subfolder, output_filename)

    with open(output_path, mode='w', newline='') as csvfile:
        fieldnames = ["Cavity Number", "Chain", "Seq ID", "AA"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(output_table)

    logger.info(f"Output table saved to '{output_path}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def write_xlsx(output_table, pdb_name, output_dir):
    """
    Writes the output table to an .xlsx file with multiple sheets.
    Args:
        output_table (list): List of dictionaries representing the output table.
        pdb_name (str): Name of the PDB file (used for the output filename).
        output_dir (str): Directory where the output file will be saved.
    """
    # Create output subfolder
    output_or_subfolder = os.path.join(os.getcwd(), output_dir, pdb_name)
    os.makedirs(output_or_subfolder, exist_ok=True)

    # Use the same naming convention as for the CSV file
    output_filename = FileNamer.get_residues_name(pdb_name, MethodType.P2RK) + ".xlsx"
    output_path = os.path.join(output_or_subfolder, output_filename)

    # Create a DataFrame from the output_table
    df = pd.DataFrame(output_table)

    # Create a dictionary to hold DataFrames for each cavity number
    sheets = {}
    for cavity_number in df["Cavity Number"].unique():
        sheet_name = f"Cavity {cavity_number}"
        sheets[sheet_name] = df[df["Cavity Number"] == cavity_number]

    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, sheet_df in sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    logger.info(f"Output table saved to '{output_path}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    config = load_config()
    chrome_driver_path = config['chrome_driver_path']
    print("Driver path: " + chrome_driver_path)
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    pdb_input = config['pdb_input']
    run_prankweb(pdb_input, config)
    #only_unzip_and_process()
