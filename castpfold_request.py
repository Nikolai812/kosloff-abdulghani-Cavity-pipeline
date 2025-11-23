from castpfoldpy.client import CastpFoldClient, CastpFoldResultPaths
from pathlib import Path
import os

# === INPUTS ===
#pdb_file = Path(r"C:\Users\user\source\repos\uh-cast-p-fold\UI_SELENIUM\input\HsOR343CF_1.pdb")  # your PDB file
#output_dir = Path(r"C:\Users\user\source\repos\uh-cast-p-fold\UI_SELENIUM\output")
# os.makedirs(output_dir, exist_ok=True)
def submit_castpfold_request(pdb_file: str)  ->str:
    probe_radius = 1.4  # optional, default is 1.4 Å
    compute_pockets = True  # optional, whether to compute pocket coordinates
    email = None  # optional, server can email results if you provide

    # === CREATE CLIENT ===
    client = CastpFoldClient()
    # === OPTION 1: Full workflow (submit + download + optional pockets) ===
    result: CastpFoldResultPaths = client.run(
        pdb= Path(pdb_file),
        out_dir= Path(os.getcwd()),
        radius=probe_radius,
        compute_pockets=compute_pockets,
        email="N/A"
    )

    print(f"Job ID: {result.jobid}")
    return result.jobid
