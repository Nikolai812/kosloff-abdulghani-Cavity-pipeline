import configparser
from datetime import datetime
import logging
import traceback
import yaml

from cavities_usage import CavitiesUsage
from consensus_builder import ConsensusBuilder
from pm_coloring import prepare_for_pymol

from pymol_scripts_exception import PymolScriptsException



def read_config():
    config = configparser.ConfigParser()
    config.read('pm_config.ini')
    return {
        'pm_output_dir': config['visualization']['pm_output_dir'],
        'pm_input_dir': config['visualization']['pm_input_dir'],
        'selenium_output_dir': config['visualization']['selenium_output_dir'],
        'best_cavity_strategy': config['visualization']['best_cavity_strategy'],
        'use_cavities': config['visualization']['use_cavities'],
    }


def main():
    # Configure logging once
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler('pymol_scripts.log')  # Uncomment to log to a file
        ]
    )

    # Set a specific logger for the project
    logger = logging.getLogger(__name__)
    config = read_config()
    pm_input_dir=config['pm_input_dir']
    pm_output_dir=config['pm_output_dir']
    selenium_output_dir=config['selenium_output_dir']
    best_cavity_strategy=config['best_cavity_strategy']
    use_cavities_file=config['use_cavities']


    try:
        # 1. Creating consensus file (in a pm_input dir for further script creation)
        logger.info(f"Beginning to process  {pm_input_dir} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        with open(use_cavities_file, "r") as f:
            use_cavities_dict = yaml.safe_load(f)

        CavitiesUsage.verify(use_cavities_dict)
        print(use_cavities_dict)

        ConsensusBuilder.process_multi_or_folder(selenium_output_dir, pm_input_dir, best_cavity_strategy, use_cavities_dict)
        logger.info(f"Successfully processed {pm_input_dir},  at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 2. Preparing coloring scripts for PyMol
        logger.info(f"Starting task: PyMol script preparation for {pm_input_dir}.")
        # looks to be called for all, even is REST: 0
        prepare_for_pymol(pm_input_dir, pm_output_dir, use_cavities_dict, copy_input=True)
        logger.info(
            f"Completed task:  PyMol script preparation to {pm_output_dir}, exiting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except ValueError as e:
        logging.error(f"Exception type: {type(e)}")  # Debugging line
        logging.error(f"Value Error processing {pm_input_dir},: {e} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except PymolScriptsException as e:
        logging.error(f"Exception type: {type(e)}")  # Debugging line
        logging.error(f"Error processing {pm_input_dir}: {e} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logging.critical(f"Exception type: {type(e)}")  # Debugging line
        logging.critical(f"Unexpected error when processing {pm_input_dir}: {e} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        traceback.print_exc()  # Print the full traceback



if __name__ == "__main__":
    main()
