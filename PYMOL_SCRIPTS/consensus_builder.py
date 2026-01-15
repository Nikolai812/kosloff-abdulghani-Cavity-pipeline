from enum import Enum
from datetime import datetime
import os
import pandas as pd
from pandas import ExcelFile
from pathlib import Path
import logging
import stat


from pymol_scripts_exception import PymolScriptsException
from cavities_usage import CavitiesUsage
from score_handler import ScoreHandler


logger = logging.getLogger(__name__)

class StrategyName(Enum):
    FIRST = "first"
    LONGEST = "longest"
    CUSTOM = "custom"
    PUPP_LONGEST_OTHER_FIRST = "pupp_longest_other_first"



class ConsensusBuilder:
    @staticmethod
    def is_file_hidden(filepath: str) -> bool:
        fname = os.path.basename(filepath)

        # Unix/Linux/macOS: hidden files start with "."
        if fname.startswith("."):
            return True

        # Windows: check file attribute
        try:
            attrs = os.stat(filepath).st_file_attributes
            return bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)
        except AttributeError:
            # st_file_attributes does not exist on non-Windows
            return False

    from typing import List, Dict
    @classmethod
    def extract_seq_id_for_proper_cavity(cls, sub_path, strategy: StrategyName, use_cavities_dict: List[Dict[str, str]]=None) ->dict[str,tuple[int,list[int],list[str]]]:
        """
        Searches  for 4 .xlsx files:
        containing 'cspf', 'cvpl', 'p2rk', 'pupp' in filenames AND starting with the subdir name.

        For each file:
            - searches worksheets 'Cavity 1'...'Cavity 5'
            - selects the one according to the chosen strategy
            - prints warning if selected sheet != 'Cavity 1'
            - extracts the 3rd column ('Seq ID') as a list (truncated to actual rows)

        Returns dictionary:
            { 'cspf': [...], 'cvpl': [...], 'p2rk': [...], 'pupp': [...] }
        """

        ######### Internal method to search for a longest cavity worksheet #####################
        ########################################################################################
        def get_longest_cavity_sheet(xls_file: ExcelFile)->tuple[str, int, int] | tuple[None, None, int]:
            max_rows = -1
            selected_sheet = None
            selected_cavity_number = None

            for i in range(1, 6):
                sheet_name = f"Cavity {i}"
                if sheet_name in xls_file.sheet_names:
                    df = xls_file.parse(sheet_name)
                    num_rows = len(df)
                    if num_rows > max_rows:
                        max_rows = num_rows
                        selected_sheet = sheet_name
                        selected_cavity_number = i

            return selected_sheet, selected_cavity_number, max_rows

        ######### END OF: Internal method to search for a longest cavity worksheet #####################
        ################################################################################################

        ##################### Internal method to select cavity by number ###############################
        ################################################################################################
        def get_cavity_sheet(cavity_number: int)-> str | None:
            if cavity_number > 5 or  cavity_number < 1:
                return None
            selected_sheet = f"Cavity {cavity_number}"
            selected_cavity_number = cavity_number
            return selected_sheet

        ##################### END OF Internal method to select cavity by number ########################
        ################################################################################################

        ################### INTERNAL METHOD  select_cavity_sheet_by_strategy##########
        ##############################################################################
        def select_cavity_sheet_by_strategy(strategy: StrategyName, xls: ExcelFile , key: str, required_keys: list[str])->tuple[str,int] | tuple[None, None]:
            """
            Selects the cavity sheet based on the strategy and key.

            Args:
                strategy (StrategyName): The strategy to use for selecting the cavity sheet.
                xls: The Excel file object or data structure.
                key: The key to check for special handling.
                required_keys (list): List of required keys for special handling.

            Returns:
                tuple: (selected_sheet, selected_cavity_number)
            """
            selected_sheet = None
            selected_cavity_number = 1

            # Depending on the strategy, the best cavities are chosen
            if strategy == StrategyName.FIRST:
                # First cavity for all
                selected_sheet = get_cavity_sheet(1)
                selected_cavity_number = 1

            elif strategy == StrategyName.LONGEST:
                # Longest strategy for all
                selected_sheet, selected_cavity_number, _ = get_longest_cavity_sheet(xls)

            # DEFAULT strategy: longest for pupp, first for all other
            elif key == required_keys[3]:
                selected_sheet, selected_cavity_number, _ = get_longest_cavity_sheet(xls)
            else:
                selected_sheet = get_cavity_sheet(1)
                selected_cavity_number = 1

            return selected_sheet, selected_cavity_number

        ##############################################################################
        ################### END OF: INTERNAL METHOD  select_cavity_sheet_by_strategy##
        ##############################################################################


        # Getting or_name from the full path:
        sub = os.path.basename(os.path.normpath(sub_path))
        # Cavity mask should be defined for a sub, if use_cavities_dictionary is not None, strategy is to be used as a default mask
        mask_to_apply: str | None = None
        # If use_cavities_dictionary is defined, the corresponding cavities should be applied for any strategy

        if use_cavities_dict:
            # 1. First - need to check whether the sub_path is present explicitely. If yes
            mask_to_apply = CavitiesUsage.get_value_for_key(yaml_dict=use_cavities_dict, target_key=sub)
            # 2. If not present, apply the rest mask in case if it is not "O"
            if None == mask_to_apply and not ConsensusBuilder.has_rest_zero(use_cavities_dict):
                mask_to_apply = CavitiesUsage.get_value_for_key(yaml_dict=use_cavities_dict, target_key="REST")
                pass


            if None == mask_to_apply:
                logger.info (f"or_name {sub} has no explicit mask, default strategy will be applied")
            else:
                logger.info(f"for or_name {sub} using mask_to_apply {mask_to_apply}")



        required_keys = ["cspf", "cvpl", "p2rk", "pupp"]
        results = {k: (-1,[]) for k in required_keys}
        files_found = {k: '' for k in required_keys}
        # find 4 required files, hidden excluded
        for fname in os.listdir(sub_path):
            fpath = os.path.join(sub_path, fname)
            if not fname.lower().endswith(".xlsx"):
                continue

            if ConsensusBuilder.is_file_hidden(fpath):
                continue

            # filename must start with subdir name
            if not fname.lower().startswith(sub.lower()):
                continue

            # match keys
            lower = fname.lower()
            found = False
            for key in required_keys:
                if key in lower:
                    files_found[key] = fpath
                    found = True
                    break

            if not found and not "consensus" in lower:
                logger.warning(f"file {fname} does not match any prediction key: {key}, and even is not consensus file, looks like something wrong in {sub_path}")

        # process each of the 4 files
        for key, fpath in files_found.items():
            if fpath == '':
                raise PymolScriptsException(f"Missing required file containing '{key}' in {sub_path}, not all files provided, cannot build consensus")

            xls = pd.ExcelFile(fpath)
            selected_sheet = None
            selected_cavity_number = None
            # max_rows = -1

            # Depending on the strategy, the best cavities are chosen
            if None == mask_to_apply:
                selected_sheet, selected_cavity_number = select_cavity_sheet_by_strategy(strategy, xls, key,
                                                                                                 required_keys)
            else:
                zero_based_index = required_keys.index(key)  # getting 0 in case of "cspf", 1- "cvpl", etc
                selected_cavity_number_str = mask_to_apply[zero_based_index]
                selected_cavity_number= int (selected_cavity_number_str)
                selected_sheet = get_cavity_sheet(selected_cavity_number)
                logger.info(f"For OR_name {sub} choosing cavity {selected_cavity_number}  for key '{key}', cavity mask '{mask_to_apply}'")

            if selected_sheet != "Cavity 1":
                logger.warning(f": {fpath} used '{selected_sheet}' instead of 'Cavity 1'")

            df = xls.parse(selected_sheet)

            # extract 3rd column ('Seq ID') and 4th ('AA')
            if df.shape[1] < 4:
                logger.warning(f"Warning: File {fpath}, sheet {selected_sheet} has fewer than 3 columns")
                continue

            seq_ids = df.iloc[:, 2].dropna().tolist()
            aa_names = df.iloc[:, 3].dropna().tolist()
            results[key] = (selected_cavity_number, seq_ids, aa_names)


        return results


    @classmethod
    def write_consensus_file(cls,
                             sub: str,
                             best_cavity_ids: dict[str, tuple[int, list[int], list[str]]],
                             scores_map: dict[str, list[tuple[str, int, float]]],
                             output_dir: str) -> None:
        """
        Creates an Excel consensus file for the given subdirectory.
        Output file: {sub}_consensus.xlsx

        Columns:
            Seq ID | cspf | cvpl | p2rk | pupp
        """

        # Extract all (Seq ID, aa_name) tuples from all four prediction methods
        all_tuples = set()

        for method_key, (_, seq_list, aa_names) in best_cavity_ids.items():
            # Assert that seq_list and aa_names have the same length
            assert len(seq_list) == len(aa_names), \
                f"Length mismatch in {method_key}: seq_list ({len(seq_list)}) and aa_names ({len(aa_names)})"

            # Need to find scores for sed_ids
            score_values = ScoreHandler.get_scores_by_seq_ids(scores_map, sub, seq_list)

            # Add tuples (seq_id, aa_name) to the set
            all_tuples.update(zip(seq_list, aa_names, score_values))

        # Sort the tuples by seq_id in ascending order
        sorted_tuples = sorted(all_tuples, key=lambda x: x[0])

        # Prepare table structure
        rows = []
        for seq_tuple in sorted_tuples:
            cspf = 1 if seq_tuple[0] in best_cavity_ids.get("cspf", (None, []))[1] else 0
            cvpl = 1 if seq_tuple[0] in best_cavity_ids.get("cvpl", (None, []))[1] else 0
            p2rk = 1 if seq_tuple[0] in best_cavity_ids.get("p2rk", (None, []))[1] else 0
            pupp = 1 if seq_tuple[0] in best_cavity_ids.get("pupp", (None, []))[1] else 0

            # Consensus rule:
            # 1 if cspf=1 OR p2rk=1 OR (cvpl=1 AND pupp=1)
            consensus = 1 if (cspf == 1 or p2rk == 1 or (cvpl == 1 and pupp == 1)) else 0

            row = {
                "Seq ID": seq_tuple[0],
                "AA": seq_tuple[1],
                "plddt": seq_tuple[2],
                "cspf": cspf,
                "cvpl": cvpl,
                "p2rk": p2rk,
                "pupp": pupp,
                "consensus": consensus
            }
            rows.append(row)

        # Create DataFrame
        df = pd.DataFrame(rows, columns=["Seq ID","AA", "plddt", "cspf", "cvpl", "p2rk", "pupp", "consensus"])

        # Create subdirectory inside output_dir
        sub_output_dir = os.path.join(output_dir, sub)
        os.makedirs(sub_output_dir, exist_ok=True)

        # Save Excel file inside that subdirectory
        out_path = os.path.join(sub_output_dir, f"{sub}_consensus.xlsx")
        df.to_excel(out_path, index=False)

        logger.info(f"Consensus file saved: {out_path} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    @classmethod
    def process_multi_or_folder(cls, sel_output_dir, pm_input_dir, best_cavity_strategy, use_cavities_dict=None)->None:
        """
        Scans 1st-level subdirectories of the Selenium Output: sel_output_dir (except containing 'temp' and 'OLD'), extracts best cavities ids,
        Then constructs a consensus file according to the chosen strategy and writes it to pm_input_dir.
        sel_output_dir works as an source (input) directory, pm_input_dir - as an output for consensus file
        Nevertheless the scores from pdb files are being read (sourced) from the pm_input_dir
        """

        # There might be several strategies to choose the best cavity (from the first 5 in 4 preriction methods)
        strategy=StrategyName(best_cavity_strategy)

        # Creating an empty dictionary for each OR (.pdb file) to keep residue scores
        pdb_aa_scores: dict[str, list[tuple[str, int, float]]] = {}

        # Before iterate
        subdir_names_to_iterate = []
        if use_cavities_dict is not None:
            # 1. Verify that for all keys from yaml (except "REST") correspond to existing OR_subfolders. Otherwise -exception
            pm_input_subdirs = os.listdir(pm_input_dir)
            non_rest_yaml_keys = [key for item in use_cavities_dict for key in item.keys() if key != "REST"] #[item.keys()[0] for item in yaml_dict]
            missing_keys = [key for key in non_rest_yaml_keys if key not in pm_input_subdirs]
            if missing_keys:
                raise ValueError(f"The following yaml keys : {missing_keys} do not correspond to any {pm_input_dir} subdirectory {pm_input_subdirs}")


            # 2. Verify whether -REST: "0" is present. If yes,  all non_key directories should be skipped (continue)
            if CavitiesUsage.has_rest_zero(use_cavities_dict):
                subdir_names_to_iterate = non_rest_yaml_keys
                logger.info(f"Rest '0' found, the following subdirs are to be processed : {subdir_names_to_iterate}")
            # 3. Run over all subdirs. If subdir key is present - apply cavity mask, else is REST is present - apply rest mask, else- apply default strategy
            else:
                subdir_names_to_iterate = os.listdir(pm_input_dir)
                logger.info(f"All subdirs from {pm_input_dir} are to be processed : {subdir_names_to_iterate}")


        # iterate over first-level subdirectories
        for sub in subdir_names_to_iterate:

            # sub_path = os.path.join(sel_output_dir, sub)
            # if not os.path.isdir(sub_path):
            #     continue
            # # skipping prankweb_temp and OLD_DATA folders
            # if  'temp' in sub or 'OLD' in sub:
            #     continue

            sub_path = Path(pm_input_dir) / sub
            if not sub_path.is_dir():
                raise PymolScriptsException(f"{sub_path} is not a directory at {pm_input_dir}")

            # Expected PDB filename
            expected_pdb = sub_path / f"{sub_path.name}.pdb"

            # Find all PDB files in directory
            pdb_files = list(sub_path.glob("*.pdb"))

            if not (len(pdb_files) == 1):
                logger.warning(f"Expected exactly one .pdb file in {sub_path}, "
                                            f"found {len(pdb_files)}, skipping the {sub_path.name}, \n"
                                                 f"please, find {expected_pdb} and put it manually to {sub_path.name} and rerun the script")
                continue

            elif not (pdb_files[0] == expected_pdb):
                logger.warning(f"Expected PDB file named {expected_pdb.name}, "
                                            f"found {pdb_files[0].name}",
                                            f"please, find {expected_pdb} and put it manually to {sub_path.name} and rerun the script"
                                            )
                continue


            ScoreHandler.collect_subdir_plddt(sub, pm_input_dir, pdb_aa_scores)
            best_cavity_ids = ConsensusBuilder.extract_seq_id_for_proper_cavity(sub_path, strategy, use_cavities_dict)
            ConsensusBuilder.write_consensus_file(sub, best_cavity_ids, pdb_aa_scores, pm_input_dir)
            print("")



