from enum import Enum
import os

class MethodType(Enum):
    CSPF = "cspf"
    CVPL = "cvpl"
    P2RK = "p2rk"
    PUPP = "pupp"

class FileNamer:
    @staticmethod
    def get_va_name(pdb_name: str, method_type: MethodType) -> str:
        """Returns the VA filename for the given PDB name and method type."""
        return f"{pdb_name}_{method_type.value}_va"

    @staticmethod
    def get_residues_name(pdb_name: str, method_type: MethodType) -> str:
        """Returns the residues filename for the given PDB name and method type."""
        return f"{pdb_name}_{method_type.value}_residues"


    @staticmethod
    def verify_pdb_exists(input_dir: str, pdb_file: str) -> bool:
        """
        Verifies if a file named {pdb_name}.pdb exists in the specified directory.

        Args:
            input_dir (str): The directory to check for the PDB file.
            pdb_file (str): The name of the PDB file (without the .pdb extension).

        Returns:
            bool: True if the file exists, False otherwise.
        """
        pdb_file_path = os.path.join(input_dir, f"{pdb_file}")
        return os.path.isfile(pdb_file_path)