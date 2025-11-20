import configparser
import csv
import os
import time

from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def enter_text_in_input(driver, input_id, text):
    """
    Locates an input field by ID and enters the specified text.

    Parameters:
    - input_id: The ID of the input field.
    - text: The text to enter into the input field.
    """
    input_field = driver.find_element(By.ID, input_id)
    input_field.clear()  # Clear any existing text
    input_field.send_keys(text)

def click_button_by_id(driver, button_id):
    """
    Locates a button by ID and clicks it.

    Parameters:
    - button_id: The ID of the button.
    """
    button = driver.find_element(By.ID, button_id)
    button.click()


def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']


def write_pocket_info_csv(driver, csv_filename):
    # Locate the table element
    table = driver.find_element(By.CSS_SELECTOR, "table")

    # Extract headers
    headers = []
    header_row = table.find_element(By.CSS_SELECTOR, "thead tr")
    for th in header_row.find_elements(By.TAG_NAME, "th"):
        if th.text.strip():  # Skip empty header cells
            headers.append(th.text.strip())

    # Extract rows
    rows = []
    for tr in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
        row = []
        for td in tr.find_elements(By.TAG_NAME, "td"):
            if td.text.strip():  # Skip empty cells

                row.append(td.text.strip())
        if row:  # Only add non-empty rows
            rows.append(row)

    # Write to CSV
    os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Data written to {csv_filename}")

def open_atom_info_save_csv(driver, output_directory):
    # Locate all rows in the table
    pocket_rows = driver.find_elements(By.XPATH, "//table[.//th/div[contains(text(), 'Pocket ID')]]/tbody[1]/tr[contains(@class, 'ant-table-row-level-0')]")

    for i, pocket_row in enumerate(pocket_rows):
        try:
            # Get pocket ID from the second column
            pocket_id = pocket_row.find_elements(By.TAG_NAME, "td")[1].text.strip()

            # Click the expand icon
            expand_icon = pocket_row.find_element(By.CSS_SELECTOR, "td.ant-table-row-expand-icon-cell span.ant-table-row-collapsed")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", expand_icon)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(expand_icon))
            driver.execute_script("arguments[0].click();", expand_icon)
            time.sleep(1)  # Wait for the row to expand

            # Click the "Atom Info" element
            atom_info_header = pocket_row.find_element(By.XPATH, "./following-sibling::tr//*[contains(text(), 'Atom Info')]")
            atom_info_header.click()
            time.sleep(1)  # Wait for the atom info to load

            ul_atom_pagination = pocket_row.find_elements(By.XPATH, "./following-sibling::tr[contains(@class, 'ant-table-expanded-row-level-1') and not(contains(@style, 'display: none'))]//ul[contains(@class, 'ant-pagination')]")
            assert len(ul_atom_pagination) == 1, f"Expected exactly 1 pagination element, but found {len(ul_atom_pagination)} in {i} pocket row"

            li_pag_items = ul_atom_pagination[-1].find_elements(By.CSS_SELECTOR, "li.ant-pagination-item a")
            page_texts = [item.text for item in li_pag_items]
            atom_tab_count = int(page_texts[-1])

            # Initialize a list to store all rows from all pagination tabs
            all_atom_rows = []

            # Extract headers once (they are the same for all tabs)
            atom_info_table = pocket_row.find_element(By.XPATH, "./following-sibling::tr//div[contains(@class, 'ant-table-content')]//table")
            headers = []
            header_row = atom_info_table.find_element(By.CSS_SELECTOR, "thead tr")
            for th in header_row.find_elements(By.TAG_NAME, "th"):
                if th.text.strip():
                    headers.append(th.text.strip())
            headers.append("Atom pagination tab")  # Add a new column for the tab number

            # Click on the first pagination tab to begin
            first_button = ul_atom_pagination[-1].find_element(By.CSS_SELECTOR, "li.ant-pagination-item-1")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", first_button)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(first_button))
            driver.execute_script("arguments[0].click();", first_button)
            time.sleep(0.5)

            for ia in range(1, atom_tab_count + 1):
                # Extract rows from the current tab
                atom_info_table = pocket_row.find_element(By.XPATH, "./following-sibling::tr//div[contains(@class, 'ant-table-content')]//table")
                for tr in atom_info_table.find_elements(By.CSS_SELECTOR, "tbody tr"):
                    atom_row = []
                    for td in tr.find_elements(By.TAG_NAME, "td"):
                        if td.text.strip():
                            atom_row.append(td.text.strip())
                    if atom_row:
                        atom_row.append(f"tab: {ia}")  # Add the tab number to the row
                        all_atom_rows.append(atom_row)

                print(f"Atom pagination tab {ia} is displayed")

                if ia < atom_tab_count:
                    next_button = ul_atom_pagination[-1].find_element(By.CSS_SELECTOR, "li.ant-pagination-next a")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", next_button)
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(next_button))
                    driver.execute_script("arguments[0].click();", next_button)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, f"li.ant-pagination-item-{ia + 1}.ant-pagination-item-active"))
                    )
                    ul_atom_pagination = pocket_row.find_elements(By.XPATH, "./following-sibling::tr[contains(@class, 'ant-table-expanded-row-level-1') and not(contains(@style, 'display: none'))]//ul[contains(@class, 'ant-pagination')]")

            # Write all data to CSV
            with open(f"{output_directory}/pocket_{pocket_id}_atom_info.csv", 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(all_atom_rows)
            print(f"Atom info for pocket {pocket_id} saved to pocket_{pocket_id}_atom_info.csv")

            # Close the "Atom Info" section
            time.sleep(1)
            atom_info_header = pocket_row.find_element(By.XPATH, "./following-sibling::tr//*[contains(text(), 'Atom Info')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", atom_info_header)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(atom_info_header))
            driver.execute_script("arguments[0].click();", atom_info_header)
            time.sleep(0.5)

            # Collapse the row
            expand_icon = pocket_row.find_element(By.CSS_SELECTOR, "td.ant-table-row-expand-icon-cell span.ant-table-row-expanded")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", expand_icon)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(expand_icon))
            driver.execute_script("arguments[0].click();", expand_icon)
            time.sleep(0.5)
        except Exception as e:
            print(f"Error processing pocket {i}: {e}")
            raise


def iterate_pagination(driver, output_directory):
    # Locate the pagination element
    pagination = driver.find_element(By.CSS_SELECTOR, "ul.ant-pagination")

    # Find all pagination items (excluding "Previous" and "Next" buttons)
    pagination_items = pagination.find_elements(By.CSS_SELECTOR, "li.ant-pagination-item a")

    # Get the last tab number from the list
    last_tab = pagination_items[-1]
    tab_count = int(last_tab.text)
    print(f"Total pagination tabs for all pockets: {tab_count}")

    for i in range(1, tab_count + 1):
        # Wait for the current tab to be active
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"li.ant-pagination-item-{i}.ant-pagination-item-active"))
        )

        # Print the current tab number
        print(f"Pagination tab {i} is displayed")

        write_pocket_info_csv(driver, f"{output_directory}/tab_{i}_pockets.csv")
        open_atom_info_save_csv(driver, output_directory)

        # If not the last tab, click "Next Page"
        if i < tab_count:
            next_button = pagination.find_element(By.CSS_SELECTOR, "li.ant-pagination-next a")
            next_button.click()
            # Wait for the next tab to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"li.ant-pagination-item-{i+1}.ant-pagination-item-active"))
            )

    # Return to the first tab
    first_tab = pagination.find_element(By.CSS_SELECTOR, "li.ant-pagination-item-1 a")
    first_tab.click()

    # Print completion message
    print(f"All {tab_count} tabs displayed")


def run_castpfold():
    print("Starting CASTpFold script...")
    # Load config
    config = load_config()
    chrome_driver_path = config['chrome_driver_path']
    base_url = config['base_url']
    job_number = config['job_number']
    output_directory = config['out_dir'] + '_' + job_number

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
        # Open the specified URL
        driver.get(f"{base_url}?{job_number}")
        time.sleep(1)
        iterate_pagination(driver, output_directory=output_directory)
        time.sleep(1)
    # write_pocket_info_csv(driver, f"{output_directory}/pocket_info.csv")
    # open_atom_info_save_csv(driver, output_directory)
    except BaseException as e:
        print("While running: ", e)
    finally:
        print("this is finally, going to quit driver")
        driver.quit()
        print("after quit")

    print("CASTpFold script completed.")


if __name__ == '__main__':
    run_castpfold()