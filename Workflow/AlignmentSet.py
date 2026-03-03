#!/usr/bin/env python3
"""
AlignmentSet: handles one workflow set from config.json.

One set corresponds to one entry under config.workflow (e.g. set0, set1, set2).
It contains multiple PedeStep instances that are executed sequentially:

    initial params
        ↓
    [step0] apply fix → write mp2par.txt → run pede → load .res
        ↓
    [step1] apply fix → write mp2par.txt → run pede → load .res
        ↓
    final params (millepede.res of the last step)
"""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Allow importing AlignmentConfig from the parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from PedeStep import PedeStep
from ParamIO import ParamIO

if TYPE_CHECKING:
    from AlignmentConfig import AlignmentConfig


class AlignmentSet:
    """
    Handles one alignment set from config.json workflow section.

    Example config entry (set0):
        "set0": {
            "iters": 10,
            "comment": "3ST Alignment",
            "pede": {
                "step0": ["IFT", 210, 410],
                "step1": ["IFT", 200, 220, 300, 310, 320, 400, 420]
            }
        }

    Usage:
        config = AlignmentConfig(Path("config.json"))
        aset   = AlignmentSet("set0", config)
        result = aset.run(initial_params, work_dir, steering, pede_dir)
    """

    def __init__(self, set_name: str, config: 'AlignmentConfig'):
        """
        Args:
            set_name: Key under config.workflow (e.g. 'set0').
            config:   AlignmentConfig instance.

        Raises:
            AttributeError: If set_name is not found in config.workflow.
            ValueError:      If no pede steps are found.
        """
        set_cfg = getattr(config.workflow, set_name)

        self._name:    str         = set_name
        self._iters:   int         = int(set_cfg.iters)
        self._comment: str         = str(set_cfg.comment)
        self._steps:   list[PedeStep] = self._parse_steps(set_cfg.pede)

        if not self._steps:
            raise ValueError(f"No pede steps found for '{set_name}'.")

    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_steps(pede_node) -> list[PedeStep]:
        """Parse PedeStep list from the pede config node (sorted by key)."""
        steps = []
        # pede_node._data is {"step0": [...], "step1": [...], ...}
        for key in sorted(pede_node._data.keys()):
            fix_list = pede_node._data[key]   # raw list from JSON
            steps.append(PedeStep(fix_list))
        return steps

    # ------------------------------------------------------------------ #

    @property
    def name(self) -> str:
        """Set identifier (e.g. 'set0')."""
        return self._name

    @property
    def iters(self) -> int:
        """Number of alignment iterations this set should be repeated."""
        return self._iters

    @property
    def comment(self) -> str:
        """Human-readable description of this set."""
        return self._comment

    @property
    def steps(self) -> list[PedeStep]:
        """Ordered list of PedeStep instances."""
        return self._steps

    # ------------------------------------------------------------------ #

    def run(self, params: ParamIO, work_dir: Path,
            steering: Path, pede_dir: Path) -> ParamIO:
        """
        Execute all pede steps sequentially.

        Each step receives the result of the previous one.
        Intermediate millepede.res files are archived as
        ``millepede.res.step{N:02d}`` so nothing is lost.

        Args:
            params:   Initial parameters (presigma file loaded as ParamIO).
                      The object is NOT modified; each step works on a deep copy.
            work_dir: Working directory.  Must already contain the binary input
                      data (mp2input.bin, produced by the 1convert step).
            steering: Path to the pede steering file.
                      The steering file must include ``mp2par.txt`` as a text file.
            pede_dir: Directory containing the ``pede`` executable.

        Returns:
            ParamIO loaded from the millepede.res of the final step.
        """
        current = params
        n = len(self._steps)

        for i, step in enumerate(self._steps):
            print(f"[{self._name}] step {i}/{n - 1} ...")
            current = step.run(current, work_dir, steering, pede_dir)

            # Archive intermediate result so the next step can overwrite
            # millepede.res without losing data.
            if i < n - 1:
                archived = work_dir / f"millepede.res.step{i:02d}"
                (work_dir / "millepede.res").rename(archived)
                # current already holds the parsed parameters in memory;
                # no need to reload from the archived file.

        print(f"[{self._name}] all {n} step(s) completed.")
        return current

    def __repr__(self) -> str:
        return (f"AlignmentSet({self._name!r}, "
                f"iters={self._iters}, "
                f"steps={len(self._steps)}, "
                f"comment={self._comment!r})")
