import configparser
import os

import pandas as pd
import stat
import shutil

def read_config():
    config = configparser.ConfigParser()
    config.read('pm_config.ini')
    return {
        'pdb_file': config['visualization']['pdb_file'],
        'pm_output_dir': config['visualization']['pm_output_dir'],
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

        # Process only .xlsx files including consensus
        file_key = filename.split('_residues')[0] if 'consensus' not in filename else filename.split('.')[0] #filename.split('_consensus')[0]
        if filename.endswith('.xlsx'):
            print(f"Processing file: {filename}")

            # Initialize the dictionary for this file's cavities
            file_data = {}

            if 'consensus' in filename:
                # Handle consensus files: read from "Sheet 1" and filter by "consensus" column
                try:
                    df = pd.read_excel(file_path, sheet_name="Sheet1")
                    if "Seq ID" in df.columns and "consensus" in df.columns:
                        # Filter rows where "consensus" == 1
                        consensus_rows = df[df["consensus"] == 1]
                        seq_ids = consensus_rows["Seq ID"].dropna().astype(str).tolist()
                        file_data["consensus"] = seq_ids
                        print(f"  Found {len(seq_ids)} consensus seq IDs in Sheet 1")
                    else:
                        print(f"  Warning: 'Seq ID' or 'consensus' column not found in Sheet 1 of {filename}")
                except Exception as e:
                    print(f"  Could not read Sheet 1 in {filename}: {e}")

            else:
                # Handle non-consensus files: read from Cavity 1-5 worksheets
                for cavity_num in range(1, 6):
                    sheet_name = f"Cavity {cavity_num}"
                    sheet_short_name = f"cav_{cavity_num}"
                    try:
                        # Read the worksheet
                        df = pd.read_excel(file_path, sheet_name=sheet_name)

                        # Extract the "Seq ID" column
                        if "Seq ID" in df.columns:
                            seq_ids = df["Seq ID"].dropna().astype(str).tolist()
                            file_data[sheet_short_name] = seq_ids
                            print(
                                f"  Found {len(seq_ids)} seq IDs in {sheet_name} ({len(seq_ids)}, expected to be distinct)")
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
        "consensus" : "red",
        "cav_1": "orange",
        "cav_2": "yellow",
        "cav_3": "cyan",
        "cav_4": "blue",
        "cav_5": "magenta"
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
            f.write(f"load {pdb_base}.pdb\n") #f.write(f"load {pdb_file}\n")

            # Create selections and color them for each cavity
            for cav_name, seq_ids in cavities.items():
                if seq_ids:  # Only process if seq_ids is not empty
                    selection = " or ".join([f"resi {res}" for res in seq_ids])
                    f.write(f"select {cav_name}, {selection}\n")
                    f.write(f"show sticks, {cav_name}\n")
                    f.write(f"color {cavity_colors[cav_name]}, {cav_name}\n")

            # Save the session and image
            f.write(f"save {file_key}.pse\n")  #f.write(f"save {pse_path}\n")
            f.write("ray 800, 600\n")
            f.write(f"png {file_key}.png\n")    # f.write(f"png {png_path}\n")
            f.write("quit\n")

        print(f"  Generated {pml_path}")
        print(f"  Output files: {pse_path}, {png_path}")


def prepare_for_pymol(input_directory, output_directory, copy_input=False):
    """
    Prepares PyMOL scripts for all 1st-level subdirectories in input_directory.
    Verifies .pdb and .xlsx files, creates output subdirectories, and generates PyMOL scripts.

    Args:
        input_directory (str): Path to the input directory containing 1st-level subdirectories.
        output_directory (str): Path to the output directory where results will be saved.
        copy_input (bool): If True, copies input files to the output subdirectories.
    """
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Iterate over 1st-level subdirectories in input_directory
    for subdir_name in os.listdir(input_directory):
        subdir_path = os.path.join(input_directory, subdir_name)

        # Skip if not a directory
        if not os.path.isdir(subdir_path):
            continue

        print(f"\nProcessing subdirectory: {subdir_name}")

        # Step 1: Verify .pdb file
        pdb_files = [f for f in os.listdir(subdir_path) if f.endswith('.pdb')]
        if len(pdb_files) != 1:
            print(f"  Warning: Expected 1 .pdb file in {subdir_name}, found {len(pdb_files)}")
            continue

        pdb_file = pdb_files[0]
        or_name = subdir_name
        if not pdb_file.startswith(or_name):
            print(f"  Warning: PDB file '{pdb_file}' does not start with '{or_name}' in {subdir_name}")
            continue

        # Step 2: Verify .xlsx files (exclude hidden files)
        xlsx_files = []
        for filename in os.listdir(subdir_path):
            file_path = os.path.join(subdir_path, filename)

            # Skip hidden files
            try:
                file_attr = os.stat(file_path).st_file_attributes
                if file_attr & stat.FILE_ATTRIBUTE_HIDDEN:
                    continue
            except AttributeError:
                if filename.startswith('.'):
                    continue

            if filename.endswith('.xlsx') and filename.startswith(or_name):
                xlsx_files.append(filename)

        if len(xlsx_files) != 5:
            print(f"  Warning: Expected 5 .xlsx files (with consensus) starting with '{or_name}' in {subdir_name}, found {len(xlsx_files)}")
            continue

        # Step 3: Create output subdirectory
        output_subdir = os.path.join(output_directory, subdir_name)
        if os.path.exists(output_subdir):
            print(f"  Warning: Output directory '{output_subdir}' already exists, deleting it")
            shutil.rmtree(output_subdir)  # Delete existing subdirectory
        os.makedirs(output_subdir)

        # Step 4: Copy input files if requested
        if copy_input:
            for filename in os.listdir(subdir_path):
                src_path = os.path.join(subdir_path, filename)
                dst_path = os.path.join(output_subdir, filename)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)

        # Step 5: Read .xlsx files and generate PyMOL scripts
        # Consensus file needs special treatment
        all_files_data = read_input_xlsx_files(subdir_path)
        generate_multi_cav_pml(all_files_data, subdir_path, output_subdir)

        print(f"  Successfully processed {subdir_name}")


def main():
    config = read_config()
    pm_input_dir=config['pm_input_dir']
    pm_output_dir=config['pm_output_dir']
    prepare_for_pymol(pm_input_dir, pm_output_dir, copy_input=True)
if __name__ == "__main__":
    main()
