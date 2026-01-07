import configparser
from datetime import datetime
import logging
import traceback

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


    try:
        # 1. Creating consensus file (in a pm_input dir for further script creation)
        logger.info(f"Beginning to process  {pm_input_dir} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ConsensusBuilder.process_multi_or_folder(selenium_output_dir, pm_input_dir, best_cavity_strategy)
        logger.info(f"Successfully processed {pm_input_dir},  at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


    except PymolScriptsException as e:
        logging.error(f"Exception type: {type(e)}")  # Debugging line
        logging.error(f"Error processing {pm_input_dir}: {e} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logging.critical(f"Exception type: {type(e)}")  # Debugging line
        logging.critical(f"Unexpected error when processing {pm_input_dir}: {e} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        traceback.print_exc()  # Print the full traceback

    # 2. Preparing coloring scripts for PyMol
    logger.info(f"Starting task: PyMol script preparation for {pm_input_dir}.")
    prepare_for_pymol(pm_input_dir, pm_output_dir, copy_input=True)
    logger.info(
        f"Completed task:  PyMol script preparation to {pm_output_dir}, exiting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
