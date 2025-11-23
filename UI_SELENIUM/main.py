import configparser
from configparser import SectionProxy

from castpfold_to_csv import run_castpfold
from cavity_plus_to_csv import run_cavity_plus


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
    for pdb_file in pdb_files:
        print(f'Running 4 predictions for {pdb_file}')
        run_castpfold(pdb_file, config)
        #run_cavity_plus(pdb_file, config)
    pass


if __name__ == '__main__':
    print("Starting main.py script...")
    config = load_config()
    input_dir = config['input_dir']
    pdb_files= get_pdb_files(input_dir)
    run_4_predictions(pdb_files, config)
    print("End of main.py script...")