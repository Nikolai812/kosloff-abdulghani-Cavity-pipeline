import os
import csv
from collections import defaultdict
from configparser import SectionProxy
from file_namer import FileNamer, MethodType
import openpyxl


def parse_txt_file(file_path):
    """Parse a single .txt file and return its data as a list of dictionaries."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Skip header lines until the empty line or "Atom" header
    data_lines = []
    for line in lines:
        if "AltLoc" in line:
            data_lines = lines[lines.index(line) + 1:]  # Start from the line containing "AltLoc"
            break

    # Parse data lines
    entries = []
    for line in data_lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            entry = {
                "Atom": parts[0],
                #"AltLoc": parts[1] if len(parts) > 1 else "",
                "Res": parts[1],
                "SeqNo": parts[2],
                "Chain": parts[3],
            }
            entries.append(entry)
    return entries

def process_pupp_out_directory(input_dir, config: SectionProxy) -> None:
    """Process all .txt files in the input directory and create CSV files."""
    # Group files by {OR_name}
    or_name_files = defaultdict(list)
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            or_name = filename.split("_cavities_")[0]
            or_name_files[or_name].append(filename)

    # Verify 5 APOLAR and 5 POLAR files for each {OR_name}
    for or_name, filenames in or_name_files.items():
        apolar_files = [f for f in filenames if "_APOLAR_" in f]
        polar_files = [f for f in filenames if "_POLAR_" in f]
        if len(apolar_files) != 5 or len(polar_files) != 5:
            print(f"Warning: {or_name} does not have 5 APOLAR and 5 POLAR files. Skipping.")
            continue

        # Initialize a dictionary to store unique entries
        unique_entries = defaultdict(set)

        # Process each file
        for filename in filenames:
            file_path = os.path.join(input_dir, filename)
            entries = parse_txt_file(file_path)

            # Extract cavity number from filename
            cav_part = filename.split("cavities_xfine_small_")[1].split("_cav")[1].split("_")[0]

            cavity_number = int(cav_part)

            # Add entries to the unique_entries table
            for entry in entries:
                key = (cavity_number, entry["Chain"], entry["SeqNo"], entry["Res"])
                unique_entries[or_name].add(key)

    # Write CSV files for each {OR_name}
    output_dir = config['output_dir']
    for or_name, entries in unique_entries.items():
        output_path = os.path.join(os.getcwd(), output_dir, or_name)
        os.makedirs(output_path, exist_ok=True)
        csv_res_filename =  FileNamer.get_residues_name(or_name, MethodType.PUPP) + ".csv" # f"{or_name}_pupp_residues.csv"
        csv_path = os.path.join(output_path, csv_res_filename)
        write_to_csv(csv_path, entries)

        xls_res_filename = FileNamer.get_residues_name(or_name,
                                                       MethodType.PUPP) + ".xlsx"  # f"{or_name}_pupp_residues.csv"
        xls_path = os.path.join(output_path, xls_res_filename)
        write_to_excel(xls_path, entries)

def write_to_csv(csv_path, unique_entries):
    """Write the unique entries to a CSV file."""
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Cavity Number", "Chain", "Seq ID", "AA"])
        for entry in sorted(unique_entries):
            writer.writerow([entry[0], entry[1], entry[2], entry[3]])
    print(f"CSV file created: {csv_path}")

import openpyxl

def write_to_excel(excel_path,  unique_entries):
    """Write the unique entries to an Excel file with separate sheets for each cavity number."""
    workbook = openpyxl.Workbook()
    # Remove the default sheet created by openpyxl
    workbook.remove(workbook.active)

    # Group entries by cavity number
    cavities = defaultdict(list)
    for entry in sorted(unique_entries):
        cavity_number = entry[0]
        cavities[cavity_number].append(entry)

    # Create a sheet for each cavity number
    for cavity_number, entries in cavities.items():
        sheet_name = f"cavity {cavity_number}"
        sheet = workbook.create_sheet(sheet_name)
        sheet.append(["Cavity Number", "Chain", "Seq ID", "AA"])
        for entry in entries:
            sheet.append([entry[0], entry[1], entry[2], entry[3]])

    # Save the workbook
    workbook.save(excel_path)
    print(f"Excel file created: {excel_path}")



if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_directory>")
        sys.exit(1)

    input_dir = sys.argv[1]
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory.")
        sys.exit(1)

    process_pupp_out_directory(input_dir)
