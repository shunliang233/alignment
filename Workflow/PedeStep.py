#!/usr/bin/env python3
import copy
import subprocess
from pathlib import Path
from typing import Union

from Label import Label
from FixRule import FixRule
from ParamIO import ParamIO


class PedeStep:
    """
    Single pede execution step.

    Workflow: apply fix rules → write mp2par.txt → run pede → load millepede.res
    """

    def __init__(self, fix: list[Union[str, int, Label]]):
        """
        Args:
            fix: List of fix rule descriptors (str abbreviations or int component labels).
        """
        self._rules: list[FixRule] = []
        for item in fix:
            if isinstance(item, str):
                self._rules.append(FixRule(item))
            elif isinstance(item, (int, Label)):
                self._rules.append(FixRule(int(item)))
            else:
                raise TypeError(f"Unparseable fix item: {type(item).__name__}")

    @property
    def rules(self) -> list[FixRule]:
        return self._rules

    # ------------------------------------------------------------------ #

    def apply(self, params: ParamIO) -> None:
        """Apply all fix rules to params in-place (set presigma = -1.0)."""
        for rule in self._rules:
            params.fix(rule)

    def run(self, params: ParamIO, work_dir: Path,
            steering: Path, pede_dir: Path = None) -> ParamIO:
        """
        Full step execution (non-destructive to the input params).

        Steps:
          1. Deep-copy params so the original is untouched.
          2. Apply all fix rules to the copy.
          3. Write copy to <work_dir>/mp2pre_ss.txt.
          4. Run ``pede <steering>`` in work_dir.
          5. Load and return <work_dir>/millepede.res as a new ParamIO.

        Args:
            params:   Input parameters (presigma file or previous step's .res).
            work_dir: Directory where pede runs; binary input must already be present.
            steering: Absolute path to the pede steering file.
                      The steering file must reference ``mp2pre_ss.txt`` as a text include.
            pede_dir: Directory containing the ``pede`` executable.
                      When ``None`` (default), ``pede`` is looked up on ``$PATH``
                      (the caller's shell, e.g. runMillepede.sh, is responsible
                      for setting PATH before invoking this script).

        Returns:
            ParamIO loaded from millepede.res produced by this step.

        Raises:
            subprocess.CalledProcessError: If pede returns a non-zero exit code.
            FileNotFoundError: If millepede.res is not produced.
        """
        # 1. Work on a deep copy so the caller's params are not modified
        working = copy.deepcopy(params)

        # 2. Apply fix rules
        self.apply(working)

        # 3. Write parameter file (mp2pre_ss.txt is referenced by mp2str_ss.txt)
        mp2pre = work_dir / "mp2pre_ss.txt"
        working.write(mp2pre)

        # 4. Run pede
        # When pede_dir is None, rely on pede being on $PATH
        # (runMillepede.sh prepends env_pede to PATH before calling this script).
        pede_cmd = str(pede_dir / "pede") if pede_dir is not None else "pede"
        subprocess.run(
            [pede_cmd, str(steering.resolve())],
            cwd=work_dir,
            check=True,
        )

        # 5. Load result
        res_file = work_dir / "millepede.res"
        if not res_file.exists():
            raise FileNotFoundError(
                f"pede did not produce millepede.res in {work_dir}")
        return ParamIO(res_file, res_file)




