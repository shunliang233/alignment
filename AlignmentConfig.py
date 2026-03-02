#!/usr/bin/env python3
"""
Alignment-specific configuration manager for FASER alignment scripts.

This module extends the basic Config class with alignment-specific
configuration handling, including path validation, formatting, and
type checking for alignment workflow parameters.
"""

from pathlib import Path

from Config import Config
from RawList import RawList


# class IterSet():
#     """Set of iteration identifiers."""
    
#     def __init__(self, iters: int):
#         self._iters: int = iters
#         self._comment: str = 
    


class AlignmentConfig(Config):
    """Manages alignment configuration with validation and formatting."""
    
    def __init__(self, config_file: Path):
        """
        Initialize alignment configuration.
        
        Args:
            config_file: Path to JSON configuration file.
        
        Raises:
            FileNotFoundError: If config file or required paths don't exist
            TypeError: If configuration values have incorrect types
            ValueError: If configuration values are invalid
        """
        # NOTE: Never explicitly/implicitly invoke __getattr__ in __init__
        super().__init__(config_file)
    
    @property
    def _archive_dest(self) -> Path:
        return self.data_config

    # =============================== Raw info ===============================
    
    @property
    def year(self) -> str:
        """Get year string from configuration (4 digits)."""
        year = self._get_int(self.raw.year)
        return str(year).zfill(4)
    
    @property
    def run(self) -> str:
        """Get run string from configuration (6 digits)."""
        run = self._get_int(self.raw.run)
        return str(run).zfill(6)
    
    @property
    def files(self) -> RawList:
        """Get files list from configuration."""
        files = self._get_str(self.raw.files)
        return RawList(files)
    
    @property
    def iters(self) -> int:
        """Get iterations integer from configuration."""
        iters = self._get_int(self.raw.iters)
        return int(iters)
    
    @property
    def stations(self) -> int:
        """Get number of stations from configuration."""
        stations = self._get_int(self.raw.stations)
        if stations not in (3, 4):
            raise ValueError(f"raw.stations must be 3 or 4, got {stations}")
        return stations
    
    @property
    def format(self) -> str:
        """Get formatted string from configuration."""
        return self._get_str(self.raw.format,
                               year=self.year,
                               run=self.run,
                               files=self.files,
                               stations=self.stations)
    
    # ============================ Workflow info =============================
    # def workflow(self) 
    
    # ============================== Source info ==============================
    
    @property
    def src_dir(self) -> Path:
        """Get source directory path."""
        return self._get_path(self.src.dir, exist=True)
    
    # =============================== DAG info ===============================
    
    @property
    def dag_dir(self) -> Path:
        """Get directory for DAG files."""
        return self._get_path(self.dag.dir, ensure=True, format=self.format)
    
    @property
    def dag_file(self) -> Path:
        """Get path for DAG file."""
        return self._get_path(self.dag.file, base_path=self.dag_dir)
    
    @property
    def dag_recoexe(self) -> Path:
        """Get path for reconstruction executable."""
        return self._get_path(self.dag.recoexe, base_path=self.dag_dir)
    
    @property
    def dag_milleexe(self) -> Path:
        """Get path for millepede executable."""
        return self._get_path(self.dag.milleexe, base_path=self.dag_dir)
    
    def dag_iter_dir(self, iteration: int) -> Path:
        """Get directory for a specific iteration in the DAG."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.dir,
                              base_path=self.dag_dir,
                              ensure=True,
                              iter=iter_str)
    
    def dag_recojob(self, iteration: int, file_str: str) -> str:
        """Get job name for reconstruction."""
        iter_str = f"{iteration:02d}"
        return self._get_str(self.dag.iter.recojob,
                             iter=iter_str, file=file_str)
    
    def dag_recosub(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction submit file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.recosub,
                              base_path=self.dag_iter_dir(iteration),
                              iter=iter_str, file=file_str)
    
    def dag_millejob(self, iteration: int) -> str:
        """Get job name for millepede."""
        iter_str = f"{iteration:02d}"
        return self._get_str(self.dag.iter.millejob, iter=iter_str)
    
    def dag_millesub(self, iteration: int) -> Path:
        """Get path for millepede submit file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.millesub,
                              base_path=self.dag_iter_dir(iteration),
                              iter=iter_str)
    
    def logs_dir(self, iteration: int) -> Path:
        """Get logs directory for a specific iteration."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.logs.dir,
                              base_path=self.dag_iter_dir(iteration),
                              ensure=True,
                              iter=iter_str)
    
    def logs_reco_err(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction error log file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.logs.recoerr,
                              base_path=self.logs_dir(iteration),
                              iter=iter_str, file=file_str)
    
    def logs_reco_log(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction log file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.logs.recolog,
                              base_path=self.logs_dir(iteration),
                              iter=iter_str, file=file_str)
    
    def logs_reco_out(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction output log file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.logs.recoout,
                              base_path=self.logs_dir(iteration),
                              iter=iter_str, file=file_str)
    
    def logs_mille_err(self, iteration: int) -> Path:
        """Get path for millepede error log file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.logs.milleerr,
                              base_path=self.logs_dir(iteration),
                              iter=iter_str)
    
    def logs_mille_log(self, iteration: int) -> Path:
        """Get path for millepede log file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.logs.millelog,
                              base_path=self.logs_dir(iteration),
                              iter=iter_str)
    
    def logs_mille_out(self, iteration: int) -> Path:
        """Get path for millepede output log file."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.dag.iter.logs.milleout,
                              base_path=self.logs_dir(iteration),
                              iter=iter_str)
    
    # =============================== Data info ===============================
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return self._get_path(self.data.dir, ensure=True, format=self.format)
    
    @property
    def data_config(self) -> Path:
        """Get path to copied configuration file."""
        return self._get_path(self.data.config, base_path=self.data_dir)
    
    @property
    def data_initial(self) -> Path:
        """Get initial inputforalign data file path."""
        return self._get_path(self.data.initial, base_path=self.reco_dir(0))
    
    def data_iter_dir(self, iteration: int) -> Path:
        """Get iteration directory path."""
        iter_str = f"{iteration:02d}"
        return self._get_path(self.data.iter.dir,
                              base_path=self.data_dir,
                              ensure=True,
                              iter=iter_str)
    
    def reco_dir(self, iteration: int) -> Path:
        """Get reconstruction directory path for an iteration."""
        return self._get_path(self.data.iter.reco,
                              base_path=self.data_iter_dir(iteration),
                              ensure=True)
    
    def kfalign_dir(self, iteration: int) -> Path:
        """Get KF alignment directory path for an iteration."""
        return self._get_path(self.data.iter.kfalign,
                              base_path=self.data_iter_dir(iteration),
                              ensure=True)
    
    def millepede_dir(self, iteration: int) -> Path:
        """Get Millepede directory path for an iteration."""
        return self._get_path(self.data.iter.millepede,
                              base_path=self.data_iter_dir(iteration),
                              ensure=True)
    
    # ============================= Template info =============================
    
    @property
    def tpl_dir(self) -> Path:
        """Get template directory path."""
        return self._get_path(self.tpl.dir, exist=True)
    
    @property
    def tpl_inputforalign(self) -> Path:
        """Get inputforalign template path."""
        return self._get_path(self.tpl.inputforalign,
                              base_path=self.tpl_dir,
                              exist=True)
    
    @property
    def tpl_recosub(self) -> Path:
        """Get reco submit template path."""
        return self._get_path(self.tpl.recosub,
                              base_path=self.tpl_dir,
                              exist=True)
    
    @property
    def tpl_recoexe(self) -> Path:
        """Get reco executable template path."""
        return self._get_path(self.tpl.recoexe,
                              base_path=self.tpl_dir,
                              exist=True)
    
    @property
    def tpl_millesub(self) -> Path:
        """Get mille submit template path."""
        return self._get_path(self.tpl.millesub,
                              base_path=self.tpl_dir,
                              exist=True)
    
    @property
    def tpl_milleexe(self) -> Path:
        """Get mille executable template path."""
        return self._get_path(self.tpl.milleexe,
                              base_path=self.tpl_dir,
                              exist=True)
    
    # =========================== Environment info ===========================
    
    @property
    def env_calypso_asetup(self) -> Path:
        """Get Calypso asetup script path from configuration."""
        return self._get_path(self.env.calypso.asetup, exist=True)
    
    @property
    def env_calypso_setup(self) -> Path:
        """Get Calypso setup script path from configuration."""
        return self._get_path(self.env.calypso.setup, exist=True)
    
    @property
    def env_pede(self) -> Path:
        """Get Millepede installation directory path from configuration."""
        return self._get_path(self.env.pede, exist=True)
    
    @property
    def env_root(self) -> Path:
        """Get ROOT setup script path from configuration."""
        return self._get_path(self.env.root, exist=True)
