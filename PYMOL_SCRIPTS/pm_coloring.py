import configparser
import os

import pandas as pd
import stat


def read_config():
    config = configparser.ConfigParser()
    config.read('pm_config.ini')
    return {
        'vis_input_csv': config['visualization']['vis_input_csv'],
        'pdb_file': config['visualization']['pdb_file'],
        'pm_output': config['visualization']['pm_output'],
        'pm_input_dir': config['visualization']['pm_input_dir']
    }




def read_input_xlsx_files(directory):
    # Initialize the main dictionary to store all data
    all_files_data = {}

    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Skip hidden files (Windows and Unix-like systems)
        try:
            # Get file attributes
            file_attr = os.stat(file_path).st_file_attributes
            # Check if the file is hidden (Windows)
            if file_attr & stat.FILE_ATTRIBUTE_HIDDEN:
                print(f"Skipping hidden file: {filename}")
                continue
        except AttributeError:
            # Fallback for Unix-like systems (check if filename starts with '.')
            if filename.startswith('.'):
                print(f"Skipping hidden file: {filename}")
                continue

        # Process only .xlsx files
        file_key = filename.split('_residues')[0]
        if filename.endswith('.xlsx'):
            print(f"Processing file: {filename}")

            # Initialize the dictionary for this file's cavities
            file_data = {}

            # Check each cavity worksheet (1 to 5)
            for cavity_num in range(1, 6):
                sheet_name = f"Cavity {cavity_num}"
                sheet_short_name = f"cav_{cavity_num}"
                try:
                    # Read the worksheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)

                    # Extract the "Seq ID" column (3rd column, index 2)
                    if "Seq ID" in df.columns:
                        seq_ids = df["Seq ID"].dropna().astype(str).tolist()
                        file_data[sheet_short_name] = seq_ids
                        print(f"  Found {len(seq_ids)} seq IDs in {sheet_name} ({len(seq_ids)}, expected to be distinct)")
                    else:
                        print(f"  Warning: 'Seq ID' column not found in {sheet_name} of {filename}")
                except Exception as e:
                    print(f"  Could not read {sheet_name} in {filename}: {e}")

            # Add the file's data to the main dictionary
            all_files_data[file_key] = file_data

    return all_files_data



def generate_multi_cav_pml(all_files_data, pdb_dir, output_dir):
    """
    Generates PyMOL scripts for each file_key in all_files_data.
    Creates 5 selections (cav_1 to cav_5) with distinct colors and saves .pml, .pse, and .png files.

    Args:
        all_files_data (dict): Dictionary returned by read_input_xlsx_files.
        pdb_dir (str): Directory containing PDB files (named as {file_key}.pdb).
        output_dir (str): Directory to save output files.
    """
    # Define colors for each cavity
    cavity_colors = {
        "cav_1": "red",
        "cav_2": "orange",
        "cav_3": "yellow",
        "cav_4": "magenta",
        "cav_5": "cyan"
    }

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate over each file_key in all_files_data
    for file_key, cavities in all_files_data.items():
        # Path to the PDB file (assumes PDB files are named {or_name}.pdb - method_name is to be truncated from {file_key})
        # Truncate file_key at the last underscore to get the PDB filename
        pdb_base = file_key.rsplit('_', 1)[0]  # Removes everything after the last '_'
        pdb_file = os.path.join(pdb_dir, f"{pdb_base}.pdb")

        # Generate paths for output files
        pml_path = os.path.join(output_dir, f"{file_key}.pml")
        png_path = os.path.join(output_dir, f"{file_key}.png")
        pse_path = os.path.join(output_dir, f"{file_key}.pse")

        print(f"Generating PyMOL script for {file_key}...")

        # Write the .pml script
        with open(pml_path, 'w') as f:
            f.write(f"load {pdb_file}\n")

            # Create selections and color them for each cavity
            for cav_name, seq_ids in cavities.items():
                if seq_ids:  # Only process if seq_ids is not empty
                    selection = " or ".join([f"resi {res}" for res in seq_ids])
                    f.write(f"select {cav_name}, {selection}\n")
                    f.write(f"show sticks, {cav_name}\n")
                    f.write(f"color {cavity_colors[cav_name]}, {cav_name}\n")

            # Save the session and image
            f.write(f"save {pse_path}\n")
            f.write("ray 800, 600\n")
            f.write(f"png {png_path}\n")
            f.write("quit\n")

        print(f"  Generated {pml_path}")
        print(f"  Output files: {pse_path}, {png_path}")



def main():
    config = read_config()
    input_or_subdir=config['pm_input_dir'] + "/HsOR343CF_1"
    file_seq_dict = read_input_xlsx_files(input_or_subdir)
    generate_multi_cav_pml(file_seq_dict, input_or_subdir, input_or_subdir)
if __name__ == "__main__":
    main()
