import configparser
import csv
import os

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return {
        'vis_input_csv': config['visualization']['vis_input_csv'],
        'pdb_file': config['visualization']['pdb_file'],
        'pm_output': config['visualization']['pm_output']
    }

def read_csv(filename):
    seq_ids = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) > 1:
                seq_ids.append(row[1])
    return seq_ids

def generate_pml(seq_ids, pdb_file, output_dir, saved_file_name="color_and_save"):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate paths for output files
    pml_path = os.path.join(output_dir, f"{saved_file_name}.pml")
    png_path = os.path.join(output_dir, f"{saved_file_name}.png")
    pse_path = os.path.join(output_dir, f"{saved_file_name}.pse")

    # Create a selection string for PyMOL
    selection = " or ".join([f"resi {res}" for res in seq_ids])

    # Write the .pml script
    with open(pml_path, 'w') as f:
        f.write(f"load {pdb_file}\n")
        f.write(f"select poc1, {selection}\n")
        f.write("show sticks, poc1\n")
        f.write("color red, poc1\n")
        f.write(f"save {pse_path}\n")
        f.write("ray 800, 600\n")
        f.write(f"png {png_path}\n")
        f.write("quit\n")

    return pml_path

def main():
    config = read_config()
    seq_ids = read_csv(config['vis_input_csv'])
    pml_path = generate_pml(
        seq_ids,
        config['pdb_file'],
        config['pm_output'],
        saved_file_name="color_and_save"
    )
    print(f"Generated {pml_path} for {len(seq_ids)} residues.")
    print(f"Output files will be saved to {config['pm_output']}.")

if __name__ == "__main__":
    main()
