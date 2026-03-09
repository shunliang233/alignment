#!/usr/bin/env python3
"""BinAlg: convert kfalign output to millepede binary input."""

import subprocess
from pathlib import Path

try:
    from Alg import Alg
except ModuleNotFoundError:
    from Workflow.Alg import Alg


class BinAlg(Alg):
    """
    Convert kfalign binary output to millepede input (mp2input.bin).

    Wraps the ``1convert`` executable.

    Workflow: kfalign_dir → <work_dir>/mp2input.bin
    """

    def __init__(self, input_dir: Path, work_dir: Path, bin_dir: Path):
        """
        Args:
            input_dir: kfalign output directory (source of binary track data).
            work_dir:  Millepede working directory (destination).
            bin_dir:   Directory containing the ``1convert`` executable.
        """
        self._input_dir = input_dir
        self._work_dir  = work_dir
        self._bin_dir   = bin_dir

    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """
        Run ``1convert`` to produce mp2input.bin in work_dir.

        Raises:
            subprocess.CalledProcessError: If ``1convert`` returns non-zero.
        """
        cmd = [
            str(self._bin_dir / '1convert'),
            '-i', str(self._input_dir),
            '-o', str(self._work_dir / 'mp2input'),
        ]
        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, cwd=self._work_dir)
