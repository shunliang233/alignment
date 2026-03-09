#!/usr/bin/env python3
"""MergeAlg: convert millepede.res to FASER DB inputforalign.txt."""

import shutil
import subprocess
from pathlib import Path

try:
    from Alg import Alg
except ModuleNotFoundError:
    from Workflow.Alg import Alg


class MergeAlg(Alg):
    """
    Convert millepede.res to the FASER DB inputforalign.txt format.

    Wraps the ``5.1PedetoDB_ss`` + ``5.2add_param`` post-processing chain.

    Workflow: millepede.res + inputforalign_in → inputforalign_out
    """

    def __init__(self, work_dir: Path, inputforalign_in: Path,
                 inputforalign_out: Path, bin_dir: Path):
        """
        Args:
            work_dir:          Millepede working directory
                               (must contain millepede.res when run() is called).
            inputforalign_in:  Current inputforalign.txt (from reco_dir).
            inputforalign_out: Destination for the updated inputforalign.txt
                               (written to the iteration root for the next reco job).
            bin_dir:           Directory containing ``5.1PedetoDB_ss``
                               and ``5.2add_param``.
        """
        self._work_dir          = work_dir
        self._inputforalign_in  = inputforalign_in
        self._inputforalign_out = inputforalign_out
        self._bin_dir           = bin_dir

    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """
        Run the DB conversion chain and write the updated inputforalign.txt.

        Steps:
          1. cp inputforalign_in → work_dir/inputforalign_temp.txt
          2. 5.1PedetoDB_ss < millepede.res >> inputforalign_temp.txt
          3. 5.2add_param   < inputforalign_temp.txt > inputforalign_new.txt
          4. cp inputforalign_new.txt → inputforalign_out

        Raises:
            FileNotFoundError:             If millepede.res is missing.
            subprocess.CalledProcessError: If either binary returns non-zero.
        """
        millepede_res      = self._work_dir / 'millepede.res'
        inputforalign_temp = self._work_dir / 'inputforalign_temp.txt'
        inputforalign_new  = self._work_dir / 'inputforalign_new.txt'

        if not millepede_res.exists():
            raise FileNotFoundError(
                f"millepede.res not found in {self._work_dir}")

        # 1. Start from the current inputforalign.txt
        shutil.copy2(self._inputforalign_in, inputforalign_temp)

        # 2. Append pede DB entries
        print(f"Executing: 5.1PedetoDB_ss <{millepede_res} >>{inputforalign_temp}")
        with open(millepede_res, 'r') as res_in, \
             open(inputforalign_temp, 'a') as tmp_out:
            subprocess.run(
                [str(self._bin_dir / '5.1PedetoDB_ss')],
                stdin=res_in, stdout=tmp_out,
                check=True, cwd=self._work_dir,
            )

        # 3. Merge parameters
        print(f"Executing: 5.2add_param <{inputforalign_temp} >{inputforalign_new}")
        with open(inputforalign_temp, 'r') as tmp_in, \
             open(inputforalign_new, 'w') as new_out:
            subprocess.run(
                [str(self._bin_dir / '5.2add_param')],
                stdin=tmp_in, stdout=new_out,
                check=True, cwd=self._work_dir,
            )

        # 4. Copy to iteration root for the next reco job
        shutil.copy2(inputforalign_new, self._inputforalign_out)
        print(f"Updated inputforalign written to: {self._inputforalign_out}")
