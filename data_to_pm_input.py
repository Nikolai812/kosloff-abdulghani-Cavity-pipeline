import configparser
import logging
import os
from UI_SELENIUM.file_namer import MethodType

import shutil


# Set a logger for this very script
logger = logging.getLogger(__name__)

# Color formatting class for console output
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[37m",     # Gray
        logging.INFO: "\033[0m",       # Default
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }

    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)

        if record.levelno >= logging.WARNING:
            msg = f"{record.levelname}: {record.getMessage()}"
        else:
            msg = record.getMessage()

        return f"{color}{msg}{self.RESET}"
# End of ColorFormatter class

def verify_and_copy(
    selenium_input_dir: str,
    selenium_output_dir: str,
    pymol_input_dir: str
) -> None:
    """
    Verify XLSX outputs per OR_NAME (case-insensitive) and copy
    OR_NAME folders and PDB files into the PyMOL input directory.
    """

    # ------------------------------------------------------------------
    # Sanity checks
    # ------------------------------------------------------------------
    for path, label in [
        (selenium_input_dir, "selenium_input_dir"),
        (selenium_output_dir, "selenium_output_dir"),
        (pymol_input_dir, "pymol_input_dir"),
    ]:
        if not os.path.isdir(path):
            raise NotADirectoryError(f"{label} does not exist or is not a directory: {path}")

    os.makedirs(pymol_input_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Collect OR_NAME directories (1st level, excluding OLD_DATA)
    # ------------------------------------------------------------------
    or_names = [
        name for name in os.listdir(selenium_output_dir)
        if name != "OLD_DATA"
        and os.path.isdir(os.path.join(selenium_output_dir, name))
    ]

    # ------------------------------------------------------------------
    # 2. Verify XLSX files per OR_NAME
    # ------------------------------------------------------------------
    for or_name in or_names:
        or_dir = os.path.join(selenium_output_dir, or_name)

        xlsx_files = [
            f for f in os.listdir(or_dir)
            if f.lower().endswith(".xlsx")
        ]

        for method in MethodType:
            found = any(
                f.lower().startswith(or_name.lower())
                and method.value in f.lower()
                for f in xlsx_files
            )

            if not found:
                logger.warning(
                    f"Missing XLSX file for OR_NAME='{or_name}', "
                    f"MethodType='{method.name}',"
                    f"!!!!!!!! CONSENSUS file cannot be built for {or_name}!!!!"
                )

    # ------------------------------------------------------------------
    # 3. Copy OR_NAME directories (overwrite with warning)
    # ------------------------------------------------------------------
    for or_name in or_names:
        src_dir = os.path.join(selenium_output_dir, or_name)
        dst_dir = os.path.join(pymol_input_dir, or_name)

        if os.path.exists(dst_dir):
            logger.info(
                f"+++++ Directory already exists and will be overwritten: {dst_dir}"
            )
            shutil.rmtree(dst_dir)

        shutil.copytree(src_dir, dst_dir)

    # ------------------------------------------------------------------
    # 4. Copy {OR_NAME}.pdb from selenium_input_dir (case-insensitive)
    # ------------------------------------------------------------------
    input_files = os.listdir(selenium_input_dir)

    for or_name in or_names:
        pdb_found = next(
            (f for f in input_files
             if f.lower() == f"{or_name.lower()}.pdb"),
            None
        )

        if pdb_found is None:
            logger.warning(
                f"!!!!!!! Missing PDB file for OR_NAME='{or_name}', PYMOL script won't work for it")
            continue

        shutil.copy2(
            os.path.join(selenium_input_dir, pdb_found),
            os.path.join(pymol_input_dir, or_name, pdb_found)
        )


def main() -> None:

    # Setting logger and color logging fot console
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter())

    file_handler = logging.FileHandler("log_data_to_pm.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    )

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
             handler, file_handler
        ]
    )
    # end of logger settings

    script_dir = os.path.dirname(os.path.abspath(__file__))  # folder of this very script
    logger.info(f"\n!!!!!! Script Data_to_PM_INPUT running at directory: {script_dir} !!!! ")
    selenium_config = configparser.ConfigParser()
    selenium_config_path = os.path.join(script_dir, "UI_SELENIUM/config.ini")
    selenium_config.read(selenium_config_path, encoding="utf-8")

    pymoll_config = configparser.ConfigParser()
    pymoll_config_path = os.path.join(script_dir, "PYMOL_SCRIPTS/pm_config.ini")
    pymoll_config.read(pymoll_config_path, encoding="utf-8")

    selenium_input_dir = os.path.join(script_dir,"UI_SELENIUM", selenium_config['DEFAULT']['input_dir'])
    selenium_output_dir = os.path.join(script_dir, "UI_SELENIUM",selenium_config['DEFAULT']['output_dir'])
    pymol_input_dir = os.path.join(script_dir, "PYMOL_SCRIPTS", pymoll_config['visualization']['pm_input_dir'])

    logger.info("\n\n===============================================================================================")
    logger.info(f"Starting verification and copying: \n {selenium_input_dir}, {selenium_output_dir} -> {pymol_input_dir} completed")
    logger.info("===============================================================================================\n\n")

    verify_and_copy(selenium_input_dir, selenium_output_dir, pymol_input_dir)
    logger.info("===============================================================================================")
    logger.info(f"Verify and copy from {selenium_input_dir}, {selenium_output_dir} -> {pymol_input_dir} completed")
    logger.info("===============================================================================================")


if __name__ == '__main__':
    main()