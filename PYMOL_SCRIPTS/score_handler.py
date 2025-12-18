
from pathlib import Path
import warnings

class ScoreHandler:

    @classmethod
    def extract_plddt_by_residue(cls, pdb_file) -> list[tuple[str, int, float]]:
        rows = []
        seen = set()

        with open(pdb_file) as f:
            for line in f:
                if line.startswith("ATOM"):
                    fields = line.split()
                    chain = fields[4]
                    seq_id = fields[5]
                    chain_seq_id = (chain, seq_id)

                    if chain_seq_id not in seen:
                        seen.add(chain_seq_id)
                        plddt = float(fields[10])
                        rows.append((chain, seq_id, plddt))

        return rows

    @classmethod
    def collect_subdir_plddt(
        cls,
        sub: str,
        pm_input: str,
        pdb_aa_scores: dict[str, list[tuple[str, int, float]]]
    ) -> None:
        """
        Verify that sub_path contains exactly one PDB file named
        <sub_path_basename>.pdb, extract pLDDT values from it,
        and store them in pdb_aa_scores[sub_path].

        Parameters
        ----------
        sub_path : str
            Path to directory containing the PDB file
        pdb_aa_scores : dict
            Mapping sub_path -> list of (chain, residue, plddt)
        """

        sub_path = Path(pm_input) / sub
        assert sub_path.is_dir(), f"{sub_path} is not a directory"

        # Expected PDB filename
        expected_pdb = sub_path / f"{sub_path.name}.pdb"

        # Find all PDB files in directory
        pdb_files = list(sub_path.glob("*.pdb"))

        assert len(pdb_files) == 1, (
            f"Expected exactly one .pdb file in {sub_path}, "
            f"found {len(pdb_files)}"
        )

        assert pdb_files[0] == expected_pdb, (
            f"Expected PDB file named {expected_pdb.name}, "
            f"found {pdb_files[0].name}"
        )

        # Warn if overwriting existing key
        if str(sub_path) in pdb_aa_scores:
            warnings.warn(
                f"Key '{sub_path}' exists in pdb_aa_scores; reassigning",
                UserWarning
            )

        # Extract scores and store
        rows = cls.extract_plddt_by_residue(expected_pdb)
        pdb_aa_scores[sub] = rows

    @classmethod
    def get_scores_by_seq_ids(
            cls,
            pdb_aa_scores: dict[str, list[tuple[str, int, float]]],
            sub: str,
            seq_ids: list[int]
    ) -> list[float]:
        """
        Extract pLDDT scores matching the given residue sequence IDs.
        Assumes exactly one score per residue across pdb_aa_scores.

        Parameters
        ----------
        pdb_aa_scores : dict
            Mapping sub_path -> list of (chain, residue, plddt)
        seq_ids : list[int]
            Residue sequence IDs to retrieve scores for

        Returns
        -------
        scores : list[float]
            List of pLDDT scores matching seq_ids.
            If any seq_id is missing or duplicated, returns empty list.
        """

        score_map: dict[int, float] = {}

        # Build residue → score map
        # Residues should be taken only for a single OR name (or sub- subdirectory name)
        list_for_selected_or_name = pdb_aa_scores[sub]
        for _, residue, score in list_for_selected_or_name:
            #for _, residue, score in rows:
            residue = int(residue)

            if residue in score_map:
                warnings.warn(
                    f"Duplicate score found for residue {residue}, or name {sub}, skipping it",
                    UserWarning
                )
                continue

            score_map[residue] = score

        # Collect scores for requested seq_ids
        scores: list[float] = []

        for seq_id in seq_ids:
            if seq_id not in score_map:
                warnings.warn(
                    f"Sequence ID {seq_id} not found in pdb_aa_scores, or name {sub}, assigning 0 value and continuing",
                    UserWarning
                )
                scores.append(0.0)

            scores.append(score_map[seq_id])

        return scores
