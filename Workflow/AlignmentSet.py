#!/usr/bin/env python3
"""
AlignmentSet: represents one entry from data.set.steps in config.json.

One set entry looks like:
    {
        "iters":   15,
        "reco":    3,
        "comment": "fix2layers",
        "pede": [
            ["IFT", 210, 410],
            ["IFT", 200, 220, 300, 310, 320, 400, 420]
        ]
    }

The four template strings come from data.set:
    dir  = "set{s}_iter{i}_st{r}_{comment}"
    iter = "iter{i}"
    reco = "reco"
    pede = "pede{p}"

Directory layout produced:
    <base_dir>/
    └── set{s}_iter{i}_st{r}_{comment}/     ← set_dir
        ├── iter00/                          ← iter_dir(0)
        │   ├── reco/                        ← reco_dir(0)
        │   ├── pede0/                       ← pede_dir(0, 0)
        │   └── pede1/                       ← pede_dir(0, 1)
        └── iter01/
            ├── reco/
            ├── pede0/
            └── pede1/
"""

from pathlib import Path
from typing import TYPE_CHECKING

try:
    from FixRule import FixRule          # when run from Workflow/
except ModuleNotFoundError:
    from Workflow.FixRule import FixRule  # when run from project root

if TYPE_CHECKING:
    from Config import SetConfig, StepConfig


class AlignmentSet:
    """
    Represents one workflow set built from config.json's set structure.

    Constructed by AlignmentConfig.make_set(step_index).
    """

    def __init__(self, set_cfg: 'SetConfig', step_cfg: 'StepConfig',
                 step_index: int):
        """
        Args:
            set_cfg:    SetConfig for config["set"] (contains dir/iter/reco/pede/steps).
            step_cfg:   StepConfig for a single element of set.steps.
                        Carries iters/reco/comment/pedes.
            step_index: 0-based index of step_cfg in set.steps (used in dir naming).
        """
        self._iters:   int = step_cfg.iters
        self._reco:    int = step_cfg.reco
        self._comment: str = step_cfg.comment
        self._index:   int = step_index

        # step_cfg.pedes is already list[FixRule] (constructed by Pydantic at load time).
        # PedeAlg objects are created at execution time (need runtime work_dir/steering).
        self._fix_rules: list[FixRule] = step_cfg.pedes
        self._set_cfg = set_cfg

        # set_cfg.dir is SetDirFmtStr — format() is statically typed by Pylance.
        self._set_dir: Path = Path(set_cfg.dir.format(
            set=step_index,
            iters=self._iters,
            reco=self._reco,
            comment=self._comment,
        ))

    # ------------------------------------------------------------------ #
    #  Read-only properties
    # ------------------------------------------------------------------ #

    @property
    def iters(self) -> int:
        """Number of alignment iterations for this set."""
        return self._iters

    @property
    def reco(self) -> int:
        """Reco station count (used in directory naming)."""
        return self._reco

    @property
    def comment(self) -> str:
        """Human-readable label for this set."""
        return self._comment

    @property
    def index(self) -> int:
        """0-based index of this set in data.set.steps."""
        return self._index

    @property
    def fix_rules(self) -> list[FixRule]:
        """Ordered list of FixRule objects (one per pede step)."""
        return self._fix_rules

    @property
    def set_dir(self) -> Path:
        """Root directory for this set (not created automatically)."""
        return self._set_dir

    # ------------------------------------------------------------------ #
    #  Directory helpers  (do NOT create directories automatically)
    # ------------------------------------------------------------------ #

    def _base_kwargs(self, iteration: int) -> dict:
        """Common kwargs for set.iter / set.reco templates."""
        return dict(
            set=self._index,
            iters=self._iters,
            reco=self._reco,
            comment=self._comment,
            iter=f"{iteration:02d}",
        )

    def iter_dir(self, iteration: int) -> Path:
        """Sub-directory for iteration i, e.g. .../iter03."""
        return Path(self._set_cfg.iter.format(**self._base_kwargs(iteration)))

    def reco_dir(self, iteration: int) -> Path:
        """Reco sub-directory inside iteration i, e.g. .../iter03/reco."""
        return Path(self._set_cfg.reco.format(**self._base_kwargs(iteration)))

    def pede_dir(self, iteration: int, pede_index: int) -> Path:
        """Pede sub-directory inside iteration i, e.g. .../iter03/pede0."""
        return Path(self._set_cfg.pede.format(**self._base_kwargs(iteration), pede=pede_index))

    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (f"AlignmentSet(index={self._index}, "
                f"iters={self._iters}, reco={self._reco}, "
                f"comment={self._comment!r}, "
                f"fix_rules={len(self._fix_rules)})")
