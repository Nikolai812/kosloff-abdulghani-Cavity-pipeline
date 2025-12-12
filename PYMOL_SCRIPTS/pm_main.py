import configparser
from pm_coloring import prepare_for_pymol
from consensus_builder import ConsensusBuilder


def read_config():
    config = configparser.ConfigParser()
    config.read('pm_config.ini')
    return {
        'pdb_file': config['visualization']['pdb_file'],
        'pm_output_dir': config['visualization']['pm_output_dir'],
        'pm_input_dir': config['visualization']['pm_input_dir'],
        'selenium_output_dir': config['visualization']['selenium_output_dir'],
        'best_cavity_strategy': config['visualization']['best_cavity_strategy'],
    }


def main():
    config = read_config()
    pm_input_dir=config['pm_input_dir']
    pm_output_dir=config['pm_output_dir']
    selenium_output_dir=config['selenium_output_dir']
    best_cavity_strategy=config['best_cavity_strategy']

    # 1. Creating consensus file (in a pm_input dir for further script creation)
    ConsensusBuilder.process_multi_or_folder(selenium_output_dir, pm_input_dir, best_cavity_strategy)
    print("")

    # 2. Preparing coloring scripts for PyMol
    prepare_for_pymol(pm_input_dir, pm_output_dir, copy_input=True)
if __name__ == "__main__":
    main()
