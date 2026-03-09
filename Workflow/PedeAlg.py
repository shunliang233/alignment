#!/usr/bin/env python3
import copy
import subprocess
from pathlib import Path

try:
    from Alg import Alg
    from FixRule import FixRule
    from ParamIO import ParamIO
except ModuleNotFoundError:
    from Workflow.Alg import Alg
    from Workflow.FixRule import FixRule
    from Workflow.ParamIO import ParamIO


class PedeAlg(Alg):
    """
    Single pede execution step.

    All environment parameters (work_dir, steering, pede_dir) are bound at
    construction time; ``run()`` only receives the input ``ParamIO``.

    Workflow: apply fix rule → write mp2pre_ss.txt → run pede → load millepede.res
    """

    # ---------------------------- Constructor ---------------------------- #

    def __init__(self, rule: FixRule, work_dir: Path,
                 steering: Path, pede_dir: Path = None):
        """
        Args:
            rule:     FixRule describing which parameters to fix.
            work_dir: Directory where pede runs; binary input must already be present.
            steering: Path to the pede steering file
                      (must reference ``mp2pre_ss.txt`` as a text include).
            pede_dir: Directory containing the ``pede`` executable.
                      When ``None`` (default), ``pede`` is looked up on ``$PATH``.
        """
        self._rule     = rule
        self._work_dir = work_dir
        self._steering = steering
        self._pede_dir = pede_dir

    @property
    def rule(self) -> FixRule:
        return self._rule

    # ------------------------------------------------------------------ #

    def apply(self, params: ParamIO) -> None:
        """Apply the fix rule to params in-place (set presigma = -1.0)."""
        params.fix(self._rule)

    def run(self, params: ParamIO) -> ParamIO:
        """
        Full step execution (non-destructive to the input params).

        Steps:
          1. Deep-copy params so the original is untouched.
          2. Apply the fix rule to the copy.
          3. Write copy to <work_dir>/mp2pre_ss.txt.
          4. Run ``pede <steering>`` in work_dir.
          5. Load and return <work_dir>/millepede.res as a new ParamIO.

        Args:
            params: Input parameters (presigma file or previous step's .res).

        Returns:
            ParamIO loaded from millepede.res produced by this step.

        Raises:
            subprocess.CalledProcessError: If pede returns a non-zero exit code.
            FileNotFoundError:             If millepede.res is not produced.
        """
        # 1. Work on a deep copy so the caller's params are not modified
        working = copy.deepcopy(params)

        # 2. Apply fix rule
        self.apply(working)

        # 3. Write parameter file (mp2pre_ss.txt is referenced by mp2str_ss.txt)
        working.write(self._work_dir / "mp2pre_ss.txt")

        # 4. Run pede
        pede_cmd = str(self._pede_dir / "pede") if self._pede_dir is not None else "pede"
        subprocess.run(
            [pede_cmd, str(self._steering.resolve())],
            cwd=self._work_dir,
            check=True,
        )

        # 5. Load result
        res_file = self._work_dir / "millepede.res"
        if not res_file.exists():
            raise FileNotFoundError(
                f"pede did not produce millepede.res in {self._work_dir}")
        return ParamIO(res_file, res_file)





