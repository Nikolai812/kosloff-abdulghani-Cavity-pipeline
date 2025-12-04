import configparser
from configparser import SectionProxy

from castpfold_to_csv import run_castpfold
from cavity_plus_to_csv import run_cavity_plus
from prankweb_to_csv import run_prankweb
from pupp_out_to_csv import  process_pupp_out_directory


import os

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']


def get_pdb_files(input_directory: str) -> list[str]:
    """
    Returns a list of .pdb file names in the specified directory.

    Args:
        input_directory (str): The directory to search for .pdb files.

    Returns:
        list[str]: A list of .pdb file names.
    """
    pdb_files = []
    for filename in os.listdir(input_directory):
        if filename.endswith('.pdb'):
            pdb_files.append(filename)
    return pdb_files

def run_4_predictions(pdb_files: list[str], config: SectionProxy) -> None:
    # Processing output files of pacupp JMOL script
    # It is expected, that java JMOL pacupp has been run prior to this python script
    print(f"Expecting that java pacupp has already completed. Processing pacupp output files for {pdb_files} ")
    pacupp_output_directory = config['pacupp_out_dir']
    process_pupp_out_directory(pacupp_output_directory, config)

    for pdb_file in pdb_files:
        print(f'Running 4 predictions for {pdb_file}')
        #run_castpfold(pdb_file, config)
        run_cavity_plus(pdb_file, config)
        #run_prankweb(pdb_file, config)
    pass


if __name__ == '__main__':
    print("Starting main.py script...")
    config = load_config()
    input_dir = config['input_dir']
    pdb_files= get_pdb_files(input_dir)
    run_4_predictions(pdb_files, config)
    print("End of main.py script...")