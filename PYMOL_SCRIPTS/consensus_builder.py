from enum import Enum
import os
import pandas as pd
import stat

from pandas import ExcelFile


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

    @classmethod
    def extract_seq_id_for_proper_cavity(cls, sub_path, strategy: StrategyName) ->dict[str,tuple[int,list[int]]]:
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

        # Internal method to search for a longest cavity worksheet
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

        #Internal method to select cavity by number
        def get_cavity_sheet(cavity_number: int)-> str | None:
            if cavity_number > 5 or  cavity_number < 1:
                return None
            selected_sheet = f"Cavity {cavity_number}"
            selected_cavity_number = cavity_number
            return selected_sheet



        sub = os.path.basename(os.path.normpath(sub_path))
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
            for key in required_keys:
                if key in lower:
                    files_found[key] = fpath


        # process each of the 4 files
        for key, fpath in files_found.items():
            if fpath == '':
                print(f"Warning: Missing required file containing '{key}' in {sub_path}")
                continue

            xls = pd.ExcelFile(fpath)
            selected_sheet = None
            selected_cavity_number = None
            max_rows = -1

            # Depending on the strategy, the best cavities are chosen
            if strategy == StrategyName.FIRST:
                # First cavity for all
                selected_sheet = get_cavity_sheet(1)
                selected_cavity_number =1

            elif strategy == StrategyName.LONGEST:
                # Longest strategy for all
                selected_sheet, selected_cavity_number, max_rows = get_longest_cavity_sheet(xls)

            # DEFAULT startegy: longest for pupp, first for all other
            elif key == required_keys[3]:
                selected_sheet, selected_cavity_number, max_rows = get_longest_cavity_sheet(xls)
            else:
                selected_sheet = get_cavity_sheet(1)
                selected_cavity_number = 1

            if selected_sheet is None:
                print(f"Warning: No Cavity sheets found in {fpath}")
                continue

            if selected_sheet != "Cavity 1":
                print(f"Warning: {fpath} used '{selected_sheet}' instead of 'Cavity 1'")

            # extract 3rd column ('Seq ID')
            df = xls.parse(selected_sheet)

            if df.shape[1] < 3:
                print(f"Warning: File {fpath}, sheet {selected_sheet} has fewer than 3 columns")
                continue

            seq_ids = df.iloc[:, 2].dropna().tolist()
            results[key] = (selected_cavity_number, seq_ids)

        return results


    @classmethod
    def write_consensus_file(cls,
                             sub: str,
                             best_cavity_ids: dict[str, tuple[int, list[int]]],
                             output_dir: str) -> None:
        """
        Creates an Excel consensus file for the given subdirectory.
        Output file: {sub}_consensus.xlsx

        Columns:
            Seq ID | cspf | cvpl | p2rk | pupp
        """

        # Extract all Seq ID values from all four tools
        all_ids = set()

        for tool, (_, seq_list) in best_cavity_ids.items():
            all_ids.update(seq_list)

        # Sort them ascending
        sorted_ids = sorted(all_ids)

        # Prepare table structure
        rows = []
        for seq_id in sorted_ids:
            cspf = 1 if seq_id in best_cavity_ids.get("cspf", (None, []))[1] else 0
            cvpl = 1 if seq_id in best_cavity_ids.get("cvpl", (None, []))[1] else 0
            p2rk = 1 if seq_id in best_cavity_ids.get("p2rk", (None, []))[1] else 0
            pupp = 1 if seq_id in best_cavity_ids.get("pupp", (None, []))[1] else 0

            # Consensus rule:
            # 1 if cspf=1 OR p2rk=1 OR (cvpl=1 AND pupp=1)
            consensus = 1 if (cspf == 1 or p2rk == 1 or (cvpl == 1 and pupp == 1)) else 0

            row = {
                "Seq ID": seq_id,
                "cspf": cspf,
                "cvpl": cvpl,
                "p2rk": p2rk,
                "pupp": pupp,
                "consensus": consensus
            }
            rows.append(row)

        # Create DataFrame
        df = pd.DataFrame(rows, columns=["Seq ID", "cspf", "cvpl", "p2rk", "pupp", "consensus"])

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save Excel file
        out_path = os.path.join(output_dir, f"{sub}_consensus.xlsx")
        df.to_excel(out_path, index=False)

        print(f"Consensus file saved: {out_path}")

    @classmethod
    def process_multi_or_folder(cls, input_dir, output_dir, best_cavity_strategy)->None:
        """
        Scans 1st-level subdirectories of the input_dir (except containing 'temp' and 'OLD'), extracts best cavities ids,
        Then constructs a consensus file according to the chosen strategy
        """

        strategy=StrategyName(best_cavity_strategy)

        # iterate over first-level subdirectories
        for sub in os.listdir(input_dir):
            sub_path = os.path.join(input_dir, sub)
            if not os.path.isdir(sub_path):
                continue
            # skipping prankweb_temp and OLD_DATA folders
            if  'temp' in sub or 'OLD' in sub:
                continue


            best_cavity_ids = ConsensusBuilder.extract_seq_id_for_proper_cavity(sub_path, strategy)
            ConsensusBuilder.write_consensus_file(sub, best_cavity_ids, output_dir)
            print("")



