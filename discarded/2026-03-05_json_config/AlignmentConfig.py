#!/usr/bin/env python3
"""
Alignment-specific configuration manager for FASER alignment scripts.

Loads config.json via the Pydantic AppConfig schema (Config.py), then
exposes validated, formatted values as properties and helper methods.

All type checking and key-existence checking is done by Pydantic at
construction time (model_validate).  This class only handles:
  - string formatting  ({year}, {run}, {iter}, …)
  - path construction  (joining base dirs, checking existence)
  - archiving          (copying config.json into the data directory)
"""

import json
import shutil
from pathlib import Path

from Config import AppConfig, SetConfig, StepConfig
from RawList import RawList
from Workflow.AlignmentSet import AlignmentSet


class AlignmentConfig:
    """Manages alignment configuration with formatting and path helpers."""

    def __init__(self, config_file: Path):
        """
        Load and validate configuration.

        Args:
            config_file: Path to JSON configuration file.

        Raises:
            FileNotFoundError: If the config file does not exist.
            pydantic.ValidationError: If any field is missing or has the wrong type.
        """
        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}")
        self._config_file: Path = config_file
        self._cfg: AppConfig = AppConfig.model_validate(
            json.loads(config_file.read_text()))

    # =============================== Archive ================================

    def archive(self) -> None:
        """Copy the config file into the data directory."""
        dest = self.data_config
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self._config_file, dest)

    # =============================== Raw info ===============================

    @property
    def year(self) -> str:
        """Year string, zero-padded to 4 digits."""
        return str(self._cfg.raw.year).zfill(4)

    @property
    def run(self) -> str:
        """Run string, zero-padded to 6 digits."""
        return str(self._cfg.raw.run).zfill(6)

    @property
    def files(self) -> RawList:
        """Files range as a RawList object."""
        return self._cfg.raw.files

    @property
    def initial(self) -> Path:
        """Initial parameters file path (must exist)."""
        path = self._cfg.raw.initial
        if not path.exists():
            raise FileNotFoundError(
                f"raw.initial: path does not exist: {path}")
        return path

    @property
    def format(self) -> str:
        """Formatted run identifier string, e.g. Y2022_R008294_F101-151."""
        return self._cfg.raw.format.format(
            year=self._cfg.raw.year,
            run=self._cfg.raw.run,
            files=self.files)

    # =============================== Data info ==============================

    @property
    def data_dir(self) -> Path:
        """Data directory path (created if it does not exist)."""
        path = Path(self._cfg.data.dir.format(format=self.format))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_config(self) -> Path:
        """Path where the config file will be archived inside data_dir."""
        return self.data_dir / self._cfg.data.config

    # ========================== Sets info ===================================

    def make_set(self, step_index: int) -> AlignmentSet:
        """
        Factory: construct an AlignmentSet for the given step index.

        Args:
            step_index: 0-based index into set.steps.

        Raises:
            IndexError: If step_index is out of range.
        """
        steps = self._cfg.set.steps
        if not (0 <= step_index < len(steps)):
            raise IndexError(
                f"step_index {step_index} out of range [0, {len(steps)})")
        return AlignmentSet(self._cfg.set, steps[step_index],
                            step_index, self.data_dir)

    # ============================== Source info =============================

    @property
    def src_dir(self) -> Path:
        """Source directory path (must exist)."""
        path = self._cfg.src.dir
        if not path.exists():
            raise FileNotFoundError(
                f"src.dir: path does not exist: {path}")
        return path

    # =============================== DAG info ===============================

    @property
    def dag_dir(self) -> Path:
        """DAG files directory (created if it does not exist)."""
        path = Path(self._cfg.dag.dir.format(format=self.format))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def dag_file(self) -> Path:
        return self.dag_dir / self._cfg.dag.file

    @property
    def dag_recoexe(self) -> Path:
        return self.dag_dir / self._cfg.dag.recoexe

    @property
    def dag_milleexe(self) -> Path:
        return self.dag_dir / self._cfg.dag.milleexe

    def dag_iter_dir(self, iteration: int) -> Path:
        """DAG iteration directory (created if it does not exist)."""
        iter_str = f"{iteration:02d}"
        path = self.dag_dir / self._cfg.dag.iter.dir.format(iter=iter_str)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def dag_recojob(self, iteration: int, file_str: str) -> str:
        iter_str = f"{iteration:02d}"
        return self._cfg.dag.iter.recojob.format(iter=iter_str, file=file_str)

    def dag_recosub(self, iteration: int, file_str: str) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.dag_iter_dir(iteration) /
                self._cfg.dag.iter.recosub.format(iter=iter_str, file=file_str))

    def dag_millejob(self, iteration: int) -> str:
        iter_str = f"{iteration:02d}"
        return self._cfg.dag.iter.millejob.format(iter=iter_str)

    def dag_millesub(self, iteration: int) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.dag_iter_dir(iteration) /
                self._cfg.dag.iter.millesub.format(iter=iter_str))

    def logs_dir(self, iteration: int) -> Path:
        """Logs directory for a specific iteration (created if needed)."""
        iter_str = f"{iteration:02d}"
        path = (self.dag_iter_dir(iteration) /
                self._cfg.dag.iter.logs.dir.format(iter=iter_str))
        path.mkdir(parents=True, exist_ok=True)
        return path

    def logs_reco_err(self, iteration: int, file_str: str) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.logs_dir(iteration) /
                self._cfg.dag.iter.logs.recoerr.format(
                    iter=iter_str, file=file_str))

    def logs_reco_log(self, iteration: int, file_str: str) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.logs_dir(iteration) /
                self._cfg.dag.iter.logs.recolog.format(
                    iter=iter_str, file=file_str))

    def logs_reco_out(self, iteration: int, file_str: str) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.logs_dir(iteration) /
                self._cfg.dag.iter.logs.recoout.format(
                    iter=iter_str, file=file_str))

    def logs_mille_err(self, iteration: int) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.logs_dir(iteration) /
                self._cfg.dag.iter.logs.milleerr.format(iter=iter_str))

    def logs_mille_log(self, iteration: int) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.logs_dir(iteration) /
                self._cfg.dag.iter.logs.millelog.format(iter=iter_str))

    def logs_mille_out(self, iteration: int) -> Path:
        iter_str = f"{iteration:02d}"
        return (self.logs_dir(iteration) /
                self._cfg.dag.iter.logs.milleout.format(iter=iter_str))

    # ============================= Template info ============================

    @property
    def tpl_dir(self) -> Path:
        """Template directory (must exist)."""
        return self._check_exists(self._cfg.tpl.dir, "tpl.dir")

    @property
    def tpl_recosub(self) -> Path:
        return self._check_exists(self._cfg.tpl.recosub, "tpl.recosub")

    @property
    def tpl_recoexe(self) -> Path:
        return self._check_exists(self._cfg.tpl.recoexe, "tpl.recoexe")

    @property
    def tpl_millesub(self) -> Path:
        return self._check_exists(self._cfg.tpl.millesub, "tpl.millesub")

    @property
    def tpl_milleexe(self) -> Path:
        return self._check_exists(self._cfg.tpl.milleexe, "tpl.milleexe")

    # =========================== Environment info ===========================

    @property
    def env_calypso_asetup(self) -> Path:
        return self._check_exists(self._cfg.env.calypso.asetup,
                                  "env.calypso.asetup")

    @property
    def env_calypso_setup(self) -> Path:
        return self._check_exists(self._cfg.env.calypso.setup,
                                  "env.calypso.setup")

    @property
    def env_pede(self) -> Path:
        return self._check_exists(self._cfg.env.pede, "env.pede")

    @property
    def env_root(self) -> Path:
        return self._check_exists(self._cfg.env.root, "env.root")

    # ========================== Internal helpers ============================

    @staticmethod
    def _check_exists(path: Path, label: str) -> Path:
        """Raise FileNotFoundError if path does not exist."""
        if not path.exists():
            raise FileNotFoundError(
                f"{label}: path does not exist: {path}")
        return path
