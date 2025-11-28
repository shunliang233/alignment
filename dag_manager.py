#!/usr/bin/env python3
"""
HTCondor DAGman manager for FASER alignment workflow.

This module generates and manages HTCondor DAG files for iterative alignment,
replacing the daemon-based approach with a more robust DAGman-based solution.
"""

import os
import argparse
import shutil
from pathlib import Path
from typing import List, Optional
from RawList import RawList
from config import AlignmentConfig
import ColorfulPrint

# Test: python3 dag_manager.py -y 2025 -r 020633 -f 101-142 -i 10 --submit

# TODO: extract paths from self.config, rather than from arguments
# TODO: 运行前检查 config.json 中的路径是否存在，以及各种语法合理性
# TODO: 支持断点执行
class DAGManager:
    """Manages HTCondor DAG generation for alignment workflow."""
    
    # Default HTCondor requirements
    DEFAULT_REQUIREMENTS = "(Machine =!= LastRemoteHost) && (OpSysAndVer =?= \"AlmaLinux9\")"
    
    # Directory name for log files
    LOGS_DIR = "logs"
    
    def __init__(self, config: AlignmentConfig):
        """
        Initialize DAG manager.
        
        Args:
            config: AlignmentConfig instance
        """
        self.config = config
    
    """Format config values"""
    # Raw info
    @property
    def _year(self) -> str:
        """Get year string from configuration."""
        year = self.config.raw.year
        if isinstance(year, (str, int)):
            return str(year).zfill(4)
        raise TypeError(f"raw.year type: {type(year).__name__} not valid.")
    @property
    def _run(self) -> str:
        """Get run string from configuration."""
        run = self.config.raw.run
        if isinstance(run, (str, int)):
            return str(run).zfill(6)
        raise TypeError(f"raw.run type: {type(run).__name__} not valid.")
    @property
    def _files(self) -> RawList:
        """Get files string from configuration."""
        files = self.config.raw.files
        if isinstance(files, str):
            return RawList(files)
        raise TypeError(f"raw.files type: {type(files).__name__} not valid.")
    @property
    def _iters_str(self) -> str:
        """Get iters string from configuration."""
        iters = self.config.raw.iters
        if isinstance(iters, (str, int)):
            return str(iters).zfill(2)
        raise TypeError(f"raw.iters type: {type(iters).__name__} not valid.")
    @property
    def _iters_int(self) -> int:
        """Get iters integer from configuration."""
        iters = self.config.raw.iters
        if isinstance(iters, (str, int)):
            return int(iters)
        raise TypeError(f"raw.iters type: {type(iters).__name__} not valid.")
    @property
    def _format(self) -> str:
        """Get format string from configuration."""
        fmt = self.config.raw.format
        if isinstance(fmt, str):
            year = self._year
            run = self._run
            files = self._files
            return fmt.format(year=year, run=run, files=files)
        raise TypeError(f"raw.format type: {type(fmt).__name__} not valid.")
    @property
    def _fourst(self) -> bool:
        """Get fourst boolean from configuration."""
        fourst = self.config.raw.fourst
        if isinstance(fourst, bool):
            return fourst
        raise TypeError(f"raw.fourst type: {type(fourst).__name__} not valid.")
    @property
    def _threest(self) -> bool:
        """Get threest boolean from configuration."""
        threest = self.config.raw.threest
        if isinstance(threest, bool):
            return threest
        raise TypeError(f"raw.threest type: {type(threest).__name__} not valid.")
    # Template info
    @property
    def _tpl_dir(self) -> Path:
        """Get template directory path."""
        tpl_dir = self.config.tpl.dir
        if isinstance(tpl_dir, str):
            path = Path(tpl_dir)
            if not path.exists():
                raise FileNotFoundError(f"Template directory does not exist: {path}")
            return path
        raise TypeError(f"tpl.dir type: {type(tpl_dir).__name__} not valid.")
    @property
    def _tpl_inputforalign(self) -> Path:
        """Get inputforalign template path."""
        inputforalign = self.config.tpl.inputforalign
        if isinstance(inputforalign, str):
            path = self._tpl_dir / inputforalign
            if not path.exists():
                raise FileNotFoundError(f"Inputforalign template file does not exist: {path}")
            return path
        raise TypeError(f"tpl.inputforalign type: {type(inputforalign).__name__} not valid.")
    @property
    def _tpl_recosub(self) -> Path:
        """Get reco submit template path."""
        recosub = self.config.tpl.recosub
        if isinstance(recosub, str):
            path = self._tpl_dir / recosub
            if not path.exists():
                raise FileNotFoundError(f"Reco submit template file does not exist: {path}")
            return path
        raise TypeError(f"tpl.recosub type: {type(recosub).__name__} not valid.")
    @property
    def _tpl_recoexe(self) -> Path:
        """Get reco executable template path."""
        recoexe = self.config.tpl.recoexe
        if isinstance(recoexe, str):
            path = self._tpl_dir / recoexe
            if not path.exists():
                raise FileNotFoundError(f"Reco executable template file does not exist: {path}")
            return path
        raise TypeError(f"tpl.recoexe type: {type(recoexe).__name__} not valid.")
    @property
    def _tpl_recoenv(self) -> Path:
        """Get reco environment script template path."""
        recoenv = self.config.tpl.recoenv
        if isinstance(recoenv, str):
            path = self._tpl_dir / recoenv
            if not path.exists():
                raise FileNotFoundError(f"Reco environment script template file does not exist: {path}")
            return path
        raise TypeError(f"tpl.recoenv type: {type(recoenv).__name__} not valid.")
    @property
    def _tpl_millesub(self) -> Path:
        """Get mille submit template path."""
        millesub = self.config.tpl.millesub
        if isinstance(millesub, str):
            path = self._tpl_dir / millesub
            if not path.exists():
                raise FileNotFoundError(f"Mille submit template file does not exist: {path}")
            return path
        raise TypeError(f"tpl.millesub type: {type(millesub).__name__} not valid.")
    @property
    def _tpl_milleexe(self) -> Path:
        """Get mille executable template path."""
        milleexe = self.config.tpl.milleexe
        if isinstance(milleexe, str):
            path = self._tpl_dir / milleexe
            if not path.exists():
                raise FileNotFoundError(f"Mille executable template file does not exist: {path}")
            return path
        raise TypeError(f"tpl.milleexe type: {type(milleexe).__name__} not valid.")
    @property
    def _tpl_milleenv(self) -> Path:
        """Get mille environment script template path."""
        milleenv = self.config.tpl.milleenv
        if isinstance(milleenv, str):
            path = self._tpl_dir / milleenv
            if not path.exists():
                raise FileNotFoundError(f"Mille environment script template file does not exist: {path}")
            return path
        raise TypeError(f"tpl.milleenv type: {type(milleenv).__name__} not valid.")
    # src info
    @property
    def _src_dir(self) -> Path:
        """Get source directory path."""
        src_dir = self.config.src.dir
        if isinstance(src_dir, str):
            path = Path(src_dir)
            if not path.exists():
                raise FileNotFoundError(f"Source directory does not exist: {path}")
            return path
        raise TypeError(f"src.dir type: {type(src_dir).__name__} not valid.")
    # Dag info
    @property
    def _dag_dir(self) -> Path:
        """Get directory for DAG files."""
        dag_dir = self.config.dag.dir
        if isinstance(dag_dir, str):
            dag_dir_fmt = dag_dir.format(format=self._format)
            return Path(dag_dir_fmt)
        raise TypeError(f"dag.dir type: {type(dag_dir).__name__} not valid.")
    @property
    def _dag_file(self) -> Path:
        """Get path for DAG file."""
        dag_file = self.config.dag.file
        if isinstance(dag_file, str):
            return self._dag_dir / dag_file
        raise TypeError(f"dag.file type: {type(dag_file).__name__} not valid.")
    @property
    def _dag_recoexe(self) -> Path:
        """Get path for reconstruction executable."""
        reco_exe = self.config.dag.recoexe
        if isinstance(reco_exe, str):
            return self._dag_dir / reco_exe
        raise TypeError(f"dag.recoexe type: {type(reco_exe).__name__} not valid.")
    @property
    def _dag_recoenv(self) -> Path:
        """Get path for reconstruction environment script."""
        reco_env = self.config.dag.recoenv
        if isinstance(reco_env, str):
            return self._dag_dir / reco_env
        raise TypeError(f"dag.recoenv type: {type(reco_env).__name__} not valid.")
    @property
    def _dag_milleexe(self) -> Path:
        """Get path for millepede executable."""
        mille_exe = self.config.dag.milleexe
        if isinstance(mille_exe, str):
            return self._dag_dir / mille_exe
        raise TypeError(f"dag.milleexe type: {type(mille_exe).__name__} not valid.")
    @property
    def _dag_milleenv(self) -> Path:
        """Get path for millepede environment script."""
        mille_env = self.config.dag.milleenv
        if isinstance(mille_env, str):
            return self._dag_dir / mille_env
        raise TypeError(f"dag.milleenv type: {type(mille_env).__name__} not valid.")
    def _dag_iter_dir(self, iteration: int) -> Path:
        """Get directory for a specific iteration in the DAG."""
        iter_str = f"{iteration:02d}"
        iter_dir = self.config.dag.iter.dir
        if isinstance(iter_dir, str):
            iter_dir_fmt = iter_dir.format(iter=iter_str)
            return self._dag_dir / iter_dir_fmt
        raise TypeError(f"dag.iter.dir type: {type(iter_dir).__name__} not valid.")
    def _dag_recojob(self, iteration: int, file_str: str) -> str:
        """Get job name for reconstruction."""
        iter_str = f"{iteration:02d}"
        reco_job = self.config.dag.iter.recojob
        if isinstance(reco_job, str):
            return reco_job.format(iter=iter_str, file=file_str)
        raise TypeError(f"dag.iter.recojob type: {type(reco_job).__name__} not valid.")
    def _dag_recosub(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction submit file."""
        iter_str = f"{iteration:02d}"
        reco_sub = self.config.dag.iter.recosub
        if isinstance(reco_sub, str):
            reco_sub_fmt = reco_sub.format(iter=iter_str, file=file_str)
            return self._dag_iter_dir(iteration) / reco_sub_fmt
        raise TypeError(f"dag.iter.recosub type: {type(reco_sub).__name__} not valid.")
    def _dag_millejob(self, iteration: int) -> str:
        """Get job name for millepede."""
        iter_str = f"{iteration:02d}"
        mille_job = self.config.dag.iter.millejob
        if isinstance(mille_job, str):
            return mille_job.format(iter=iter_str)
        raise TypeError(f"dag.iter.millejob type: {type(mille_job).__name__} not valid.")
    def _dag_millesub(self, iteration: int) -> Path:
        """Get path for millepede submit file."""
        iter_str = f"{iteration:02d}"
        mille_sub = self.config.dag.iter.millesub
        if isinstance(mille_sub, str):
            mille_sub_fmt = mille_sub.format(iter=iter_str)
            return self._dag_iter_dir(iteration) / mille_sub_fmt
        raise TypeError(f"dag.iter.millesub type: {type(mille_sub).__name__} not valid.")
    def _logs_dir(self, iteration: int) -> Path:
        """Get logs directory for a specific iteration."""
        iter_str = f"{iteration:02d}"
        logs_dir = self.config.dag.iter.logs.dir
        if isinstance(logs_dir, str):
            logs_dir_fmt = logs_dir.format(iter=iter_str)
            return self._dag_iter_dir(iteration) / logs_dir_fmt
        raise TypeError(f"dag.iter.logs.dir type: {type(logs_dir).__name__} not valid.")
    def _logs_reco_err(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction error log file."""
        iter_str = f"{iteration:02d}"
        logs_err = self.config.dag.iter.logs.recoerr
        if isinstance(logs_err, str):
            logs_err_fmt = logs_err.format(iter=iter_str, file=file_str)
            return self._logs_dir(iteration) / logs_err_fmt
        raise TypeError(f"dag.iter.logs.recoerr type: {type(logs_err).__name__} not valid.")
    def _logs_reco_log(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction log file."""
        iter_str = f"{iteration:02d}"
        logs_log = self.config.dag.iter.logs.recolog
        if isinstance(logs_log, str):
            logs_log_fmt = logs_log.format(iter=iter_str, file=file_str)
            return self._logs_dir(iteration) / logs_log_fmt
        raise TypeError(f"dag.iter.logs.recolog type: {type(logs_log).__name__} not valid.")
    def _logs_reco_out(self, iteration: int, file_str: str) -> Path:
        """Get path for reconstruction output log file."""
        iter_str = f"{iteration:02d}"
        logs_out = self.config.dag.iter.logs.recoout
        if isinstance(logs_out, str):
            logs_out_fmt = logs_out.format(iter=iter_str, file=file_str)
            return self._logs_dir(iteration) / logs_out_fmt
        raise TypeError(f"dag.iter.logs.recoout type: {type(logs_out).__name__} not valid.")
    def _logs_mille_err(self, iteration: int) -> Path:
        """Get path for millepede error log file."""
        iter_str = f"{iteration:02d}"
        logs_err = self.config.dag.iter.logs.milleerr
        if isinstance(logs_err, str):
            logs_err_fmt = logs_err.format(iter=iter_str)
            return self._logs_dir(iteration) / logs_err_fmt
        raise TypeError(f"dag.iter.logs.milleerr type: {type(logs_err).__name__} not valid.")
    def _logs_mille_log(self, iteration: int) -> Path:
        """Get path for millepede log file."""
        iter_str = f"{iteration:02d}"
        logs_log = self.config.dag.iter.logs.millelog
        if isinstance(logs_log, str):
            logs_log_fmt = logs_log.format(iter=iter_str)
            return self._logs_dir(iteration) / logs_log_fmt
        raise TypeError(f"dag.iter.logs.millelog type: {type(logs_log).__name__} not valid.")
    def _logs_mille_out(self, iteration: int) -> Path:
        """Get path for millepede output log file."""
        iter_str = f"{iteration:02d}"
        logs_out = self.config.dag.iter.logs.milleout
        if isinstance(logs_out, str):
            logs_out_fmt = logs_out.format(iter=iter_str)
            return self._logs_dir(iteration) / logs_out_fmt
        raise TypeError(f"dag.iter.logs.milleout type: {type(logs_out).__name__} not valid.")
    # Data info
    @property
    def _data_dir(self) -> Path:
        """Get data directory path."""
        data_dir = self.config.data.dir
        if isinstance(data_dir, str):
            data_dir_fmt = data_dir.format(format=self._format)
            return Path(data_dir_fmt)
        raise TypeError(f"data.dir type: {type(data_dir).__name__} not valid.")
    def _data_iter_dir(self, iteration: int) -> Path:
        """Get iteration directory path."""
        iter_str = f"{iteration:02d}"
        iter_dir = self.config.data.iter.dir
        if isinstance(iter_dir, str):
            iter_dir_fmt = iter_dir.format(iter=iter_str)
            return self._data_dir / iter_dir_fmt
        raise TypeError(f"data.iter.dir type: {type(iter_dir).__name__} not valid.")
    def _reco_dir(self, iteration: int) -> Path:
        """Get reconstruction directory path for an iteration."""
        iter_dir = self._data_iter_dir(iteration)
        reco = self.config.data.iter.reco
        if isinstance(reco, str):
            return iter_dir / reco
        raise TypeError(f"data.iter.reco type: {type(reco).__name__} not valid.")
    def _kfalign_dir(self, iteration: int) -> Path:
        """Get KF alignment directory path for an iteration."""
        iter_dir = self._data_iter_dir(iteration)
        kfalign = self.config.data.iter.kfalign
        if isinstance(kfalign, str):
            return iter_dir / kfalign
        raise TypeError(f"data.iter.kfalign type: {type(kfalign).__name__} not valid.")
    def _millepede_dir(self, iteration: int) -> Path:
        """Get Millepede directory path for an iteration."""
        iter_dir = self._data_iter_dir(iteration)
        millepede = self.config.data.iter.millepede
        if isinstance(millepede, str):
            return iter_dir / millepede
        raise TypeError(f"data.iter.millepede type: {type(millepede).__name__} not valid.")


    

    def create_data_dirs(self) -> None:
        """Create data directories for all iterations."""
        data_dir = self._data_dir
        if data_dir.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Data directory already exists: {data_dir}")
        else:
            data_dir.mkdir(parents=True)
        for it in range(self._iters_int):
            iter_dir = self._data_iter_dir(it)
            if iter_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Iteration directory already exists: {iter_dir}")
            else:
                iter_dir.mkdir(parents=True)
            reco_dir = self._reco_dir(it)
            if reco_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Reconstruction directory already exists: {reco_dir}")
            else:
                reco_dir.mkdir(parents=True)
            kfalign_dir = self._kfalign_dir(it)
            if kfalign_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"KF alignment directory already exists: {kfalign_dir}")
            else:
                kfalign_dir.mkdir(parents=True)
            millepede_dir = self._millepede_dir(it)
            if millepede_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Millepede directory already exists: {millepede_dir}")
            else:
                millepede_dir.mkdir(parents=True)
    
    def creat_dag_dirs(self) -> None:
        """Create DAG working directories for all iterations."""
        dag_dir = self._dag_dir
        if dag_dir.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"DAG directory already exists: {dag_dir}")
        else:
            dag_dir.mkdir(parents=True)
        for it in range(self._iters_int):
            iter_dir = self._dag_iter_dir(it)
            if iter_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"DAG iteration directory already exists: {iter_dir}")
            else:
                iter_dir.mkdir(parents=True)
            logs_dir = self._logs_dir(it)
            if logs_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Logs directory already exists: {logs_dir}")
            else:
                logs_dir.mkdir(parents=True)
    
    def copy_first_inputforalign(self) -> None:
        it = 0
        reco_dir = self._reco_dir(it)
        shutil.copy(self._tpl_inputforalign, reco_dir)
    
    def create_reco_exeenv_files(self) -> None:
        """Create reco executable and environment script in DAG directory."""
        # Copy reco executable
        dag_recoexe = self._dag_recoexe
        if dag_recoexe.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting reco executable: {dag_recoexe}")
        shutil.copy(self._tpl_recoexe, dag_recoexe)
        # Copy reco environment script
        dag_recoenv = self._dag_recoenv
        if dag_recoenv.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting reco environment script: {dag_recoenv}")
        shutil.copy(self._tpl_recoenv, dag_recoenv)
    
    def create_reco_submit_files(self) -> None:
        """Create reco submit files for all iterations and raw files."""
        for it in range(self._iters_int):
            for file_str in self._files:
                with open(self._tpl_recosub, 'r') as tpl_file:
                    tpl_content = tpl_file.read()
                if not self._dag_recoexe.exists():
                    raise FileNotFoundError(f"Reco executable not found: {self._dag_recoexe}")
                if not self._logs_dir(it).exists():
                    raise FileNotFoundError(f"Logs directory not found: {self._logs_dir(it)}")
                if not self._reco_dir(it).exists():
                    raise FileNotFoundError(f"Reco directory not found: {self._reco_dir(it)}")
                if not self._kfalign_dir(it).exists():
                    raise FileNotFoundError(f"KF alignment directory not found: {self._kfalign_dir(it)}")
                if not self._dag_recoenv.exists():
                    raise FileNotFoundError(f"Reco environment script not found: {self._dag_recoenv}")
                sub_content = tpl_content.format(
                    year=self._year,
                    run=self._run,
                    file_str=file_str,
                    fourst=self._fourst,
                    threest=self._threest,
                    exe_path=self._dag_recoexe,
                    out_path=self._logs_reco_out(it, file_str),
                    err_path=self._logs_reco_err(it, file_str),
                    log_path=self._logs_reco_log(it, file_str),
                    reco_dir=self._reco_dir(it),
                    kfalign_dir=self._kfalign_dir(it),
                    src_dir=self._src_dir,
                    env_path=self._dag_recoenv
                )
                recosub = self._dag_recosub(it, file_str)
                if recosub.exists():
                    ColorfulPrint.print_yellow(f"Warning: ")
                    print(f"Overwritting reco submit file: {recosub}")
                with open(recosub, 'w') as sub_file:
                    sub_file.write(sub_content)


#     def create_reco_submit_file(
#         self, 
#         output_dir: Path,
#         iteration: int,
#         year: str,
#         run: str,
#         file_str: str,
#         fourst: bool,
#         threest: bool,
#         src_dir: Path,
#         env_path: Path,
#         work_dir: Path
#     ) -> Path:
#         """
#         Create HTCondor submit file for a single reconstruction job.
        
#         Args:
#             output_dir: Main output directory for job data
#             iteration: Iteration number
#             year: Year of data taking
#             run: Run number (6 digits)
#             file_str: File number as string (e.g., "00400")
#             fourst: Enable 4-station mode
#             threest: Enable 3-station mode
#             src_dir: Source directory path
#             env_path: Environment script path
#             work_dir: Work directory for DAG and log files
            
#         Returns:
#             Path to created submit file
#         """
#         iter_str = f"iter{iteration:02d}"
#         reco_dir = self._reco_dir(iteration)
#         kfalign_dir = self._kfalign_dir(iteration)
        
#         # Create individual submit file for this file in work_dir
#         submit_file = work_dir / iter_str / f"reco_{iter_str}_{file_str}.sub"
#         exe_path = work_dir / iter_str / "runAlignment.sh"
#         exe_path.parent.mkdir(parents=True, exist_ok=True)
#         shutil.copy(src_dir / "runAlignment.sh", exe_path)
        
#         # Log files go in work_dir to avoid collisions between parallel DAGs
#         log_dir = work_dir / iter_str / self.LOGS_DIR
#         log_dir.mkdir(parents=True, exist_ok=True)
        
#         submit_content = f"""# HTCondor submit file for reconstruction job (file {file_str})
# universe = vanilla
# executable = {exe_path}

# output = {log_dir}/reco_{iter_str}_{file_str}.out
# error  = {log_dir}/reco_{iter_str}_{file_str}.err
# log    = {log_dir}/reco_{iter_str}_{file_str}.log

# request_cpus = {self.config.get('htcondor.reco.request_cpus', 1)}
# request_memory = {self.config.get('htcondor.reco.request_memory', '2 GB')}
# request_disk = {self.config.get('htcondor.reco.request_disk', '2 GB')}
# should_transfer_files = YES
# when_to_transfer_output = ON_EXIT
# transfer_output_files = logs/

# +JobFlavour = "{self.config.get('htcondor.reco.job_flavour', 'workday')}"
# on_exit_remove = (ExitBySignal == False) && (ExitCode == 0)
# max_retries = {self.config.get('htcondor.reco.max_retries', 3)}
# requirements = {self.config.get('htcondor.requirements', self.DEFAULT_REQUIREMENTS)}

# arguments = {year} {run} {file_str} {fourst} {threest} {reco_dir} {kfalign_dir} {src_dir} {env_path}
# queue
# """
        
#         # Write submit file
#         submit_file.parent.mkdir(parents=True, exist_ok=True)
#         with open(submit_file, 'w') as f:
#             f.write(submit_content)
        
#         return submit_file



    # def _create_setup_job_script(self, output_dir: Path, iteration: int) -> None:
    #     """
    #     Create setup script for an iteration (prepare directories and input files).
        
    #     Args:
    #         output_dir: Main output directory
    #         iteration: Iteration number
    #     """
    #     iter_str = f"iter{iteration:02d}"
    #     iter_dir = output_dir / iter_str
    #     reco_dir = iter_dir / "1reco"
    #     kfalign_dir = iter_dir / "2kfalignment"
    #     millepede_dir = iter_dir / "3millepede"
        
    #     # Create directories
    #     reco_dir.mkdir(parents=True, exist_ok=True)
    #     kfalign_dir.mkdir(parents=True, exist_ok=True)
    #     millepede_dir.mkdir(parents=True, exist_ok=True)
        
    #     # Prepare inputforalign.txt
    #     # For iteration 1, create empty file
    #     # For subsequent iterations, create empty placeholder
    #     # (actual alignment constants will be copied by pre-script during job execution)
    #     input_path = reco_dir / "inputforalign.txt"
    #     template_path = Path(__file__).parent / "templates" / "inputforalign.txt"
    #     shutil.copy(template_path, input_path)


    def create_mille_exeenv_files(self) -> None:
        """Create millepede executable and environment script in DAG directory."""
        # Copy millepede executable
        dag_milleexe = self._dag_milleexe
        if dag_milleexe.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting millepede executable: {dag_milleexe}")
        shutil.copy(self._tpl_milleexe, dag_milleexe)
        # Copy millepede environment script
        dag_milleenv = self._dag_milleenv
        if dag_milleenv.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting millepede environment script: {dag_milleenv}")
        shutil.copy(self._tpl_milleenv, dag_milleenv)
    
    def create_mille_submit_files(self) -> None:
        """Create millepede submit files for all iterations."""
        for it in range(self._iters_int):
            with open(self._tpl_millesub, 'r') as tpl_file:
                tpl_content = tpl_file.read()
            if not self._dag_milleexe.exists():
                raise FileNotFoundError(f"Millepede executable not found: {self._dag_milleexe}")
            if not self._logs_dir(it).exists():
                raise FileNotFoundError(f"Logs directory not found: {self._logs_dir(it)}")
            if not self._kfalign_dir(it).exists():
                raise FileNotFoundError(f"KF alignment directory not found: {self._kfalign_dir(it)}")
            if not self._dag_milleenv.exists():
                raise FileNotFoundError(f"Millepede environment script not found: {self._dag_milleenv}")
            sub_content = tpl_content.format(
                exe_path=self._dag_milleexe,
                out_path=self._logs_mille_out(it),
                err_path=self._logs_mille_err(it),
                log_path=self._logs_mille_log(it),
                to_next_iter=(it < self._iters_int - 1),
                env_path=self._dag_milleenv,
                src_dir=self._src_dir,
                kfalign_dir=self._kfalign_dir(it),
                next_reco_dir=self._reco_dir(it + 1) if it < self._iters_int - 1 else ""
            )
            millesub = self._dag_millesub(it)
            if millesub.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Overwritting millepede submit file: {millesub}")
            with open(millesub, 'w') as sub_file:
                sub_file.write(sub_content)





#     def create_millepede_submit_file(
#         self,
#         output_dir: Path,
#         iteration: int,
#         src_dir: Path,
#         env_path: Path,
#         work_dir: Path,
#         to_next_iter: bool = True
#     ) -> Path:
#         """
#         Create HTCondor submit file for Millepede job.
        
#         Args:
#             output_dir: Main output directory for job data
#             iteration: Iteration number
#             src_dir: Source directory path
#             env_path: Environment script path
#             work_dir: Work directory for DAG and log files
#             to_next_iter: Whether to copy results to next iteration
            
#         Returns:
#             Path to created submit file
#         """
#         iter_str = f"iter{iteration:02d}"
#         millepede_dir = output_dir / iter_str / "3millepede"
#         kfalign_dir = output_dir / iter_str / "2kfalignment"
        
#         # Submit file and wrapper script go in work_dir
#         submit_file = work_dir / iter_str / "millepede.sub"
#         wrapper_script = work_dir / iter_str / "run_millepede.sh"
        
#         # Log files go in work_dir to avoid collisions between parallel DAGs
#         log_dir = work_dir / iter_str / self.LOGS_DIR
#         log_dir.mkdir(parents=True, exist_ok=True)
#         wrapper_content = f"""#!/bin/bash
# set -e

# echo "Setting up environment..."
# source {env_path}

# echo "Running Millepede..."
# python3 {src_dir}/millepede/bin/millepede.py -i {kfalign_dir}

# echo "Millepede completed successfully."
# """
#         if to_next_iter:
#             next_iter_str = f"iter{iteration+1:02d}"
#             next_input = output_dir / next_iter_str / "1reco" / "inputforalign.txt"
#             wrapper_content += f"""
# echo "Transferring alignment constants to next iteration..."
# if [ -f "{output_dir / iter_str}/inputforalign.txt" ]; then
#     cp "{output_dir / iter_str}/inputforalign.txt" "{next_input}"
#     echo "Alignment constants transferred successfully."
# else
#     echo "Warning: Alignment constants not found. Using empty file."
#     touch "{next_input}"
# fi
# """
#         wrapper_script.parent.mkdir(parents=True, exist_ok=True)
#         with open(wrapper_script, 'w') as f:
#             f.write(wrapper_content)
#         os.chmod(wrapper_script, 0o755)
        
#         submit_content = f"""# HTCondor submit file for Millepede job
# universe = vanilla
# executable = {wrapper_script}

# output = {log_dir}/millepede.out
# error  = {log_dir}/millepede.err
# log    = {log_dir}/millepede.log

# request_cpus = {self.config.get('htcondor.millepede.request_cpus', 1)}
# request_memory = {self.config.get('htcondor.millepede.request_memory', '2 GB')}
# request_disk = {self.config.get('htcondor.millepede.request_disk', '2 GB')}
# should_transfer_files = YES
# when_to_transfer_output = ON_EXIT

# +JobFlavour = "{self.config.get('htcondor.millepede.job_flavour', 'workday')}"
# on_exit_remove = (ExitBySignal == False) && (ExitCode == 0)
# max_retries = {self.config.get('htcondor.millepede.max_retries', 2)}

# queue
# """
        
#         with open(submit_file, 'w') as f:
#             f.write(submit_content)
        
#         return submit_file


    def create_dag_file(self) -> Path:
        """Create DAG file for complete alignment workflow."""
        dag_file = self._dag_file
        if dag_file.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting DAG file: {dag_file}")
        dag_content = "# HTCondor DAG for FASER alignment workflow\n\n"
        for it in range(self._iters_int):
            # reco jobs
            dag_content += f"# Iteration {it} reconstruction jobs\n"
            for file_str in self._files:
                reco_sub = self._dag_recosub(it, file_str)
                reco_job = self._dag_recojob(it, file_str)
                dag_content += f"JOB {reco_job} {reco_sub}\n"
            # mille jobs
            dag_content += f"\n# Iteration {it} millepede job\n"
            mille_sub = self._dag_millesub(it)
            mille_job = self._dag_millejob(it)
            dag_content += f"JOB {mille_job} {mille_sub}\n"
            # add dependencies
            dag_content += f"\n# Iteration {it} dependencies\n"
            for file_str in self._files:
                reco_job = self._dag_recojob(it, file_str)
                dag_content += f"PARENT {reco_job} CHILD {mille_job}\n"
                if it != 0:
                    last_mille_job = self._dag_millejob(it-1)
                    dag_content += f"PARENT {last_mille_job} CHILD {reco_job}\n"
            dag_content += "\n"
        # Add retry settings
        dag_content += "# Retry settings\n"
        for it in range(self._iters_int):
            for file_str in self._files:
                reco_job = self._dag_recojob(it, file_str)
                dag_content += f"RETRY {reco_job} 2\n"
            mille_job = self._dag_millejob(it)
            dag_content += f"RETRY {mille_job} 1\n"
        with open(dag_file, 'w') as f:
            f.write(dag_content)
        return dag_file

    # def create_dag_file(
    #     self,
    #     output_dir: Path,
    #     year: str,
    #     run: str,
    #     file_list: RawList,
    #     iterations: int,
    #     fourst: bool,
    #     threest: bool,
    #     src_dir: Path,
    #     reco_env_path: Path,
    #     millepede_env_path: Path,
    #     work_dir: Path
    # ) -> Path:
    #     """
    #     Create HTCondor DAG file for complete alignment workflow.
        
    #     Args:
    #         output_dir: Main output directory for job data
    #         year: Year of data taking
    #         run: Run number (6 digits)
    #         file_list: RawList object with file numbers
    #         iterations: Number of iterations to perform
    #         fourst: Enable 4-station mode
    #         threest: Enable 3-station mode
    #         src_dir: Source directory path
    #         reco_env_path: Reconstruction environment script path
    #         millepede_env_path: Millepede environment script path
    #         work_dir: Work directory for DAG and log files
            
    #     Returns:
    #         Path to created DAG file
    #     """
    #     dag_file = self._dag_file
        
    #     dag_content = "# HTCondor DAG for FASER alignment workflow\n\n"
        
    #     # Create jobs for each iteration
    #     for it in range(1, iterations + 1):
    #         # Setup job script for each iteration
    #         self._create_setup_job_script(output_dir, it)
            
    #         # Create individual reconstruction jobs for each file
    #         dag_content += f"# Iteration {it} reconstruction jobs\n"
    #         reco_jobs = []
    #         for file_str in file_list:
    #             job_name = f"reco_{it:02d}_{file_str}"
    #             reco_jobs.append(job_name)
    #             reco_submit = self.create_reco_submit_file(
    #                 output_dir, it, year, run, file_str, fourst, threest, src_dir, reco_env_path, work_dir
    #             )
    #             dag_content += f"JOB {job_name} {reco_submit}\n"
            
    #         # Millepede job
    #         dag_content += f"\n# Iteration {it} millepede job\n"
    #         mille_submit = self.create_millepede_submit_file(
    #             output_dir, it, src_dir, millepede_env_path, work_dir,
    #             to_next_iter=(it < iterations)
    #         )
    #         dag_content += f"JOB millepede_{it:02d} {mille_submit}\n"
            
    #         # Add dependencies
    #         dag_content += f"\n# Iteration {it} dependencies\n"
    #         # All reconstruction jobs must complete before millepede
    #         for reco_job in reco_jobs:
    #             dag_content += f"PARENT {reco_job} CHILD millepede_{it:02d}\n"
            
    #         # Link iterations - millepede from previous iteration must complete
    #         # before any reconstruction job in the current iteration starts
    #         if it > 1:
    #             for reco_job in reco_jobs:
    #                 dag_content += f"PARENT millepede_{it-1:02d} CHILD {reco_job}\n"
            
    #         dag_content += "\n"
        
    #     # Add retry settings
    #     dag_content += "# Retry settings\n"
    #     for it in range(1, iterations + 1):
    #         for file_str in file_list:
    #             job_name = f"reco_{it:02d}_{file_str}"
    #             dag_content += f"RETRY {job_name} 2\n"
    #         dag_content += f"RETRY millepede_{it:02d} 1\n"
        
    #     # Write DAG file
    #     with open(dag_file, 'w') as f:
    #         f.write(dag_content)
        
    #     print(f"Created DAG file: {dag_file}")
    #     return dag_file

    



def main():
    """Main entry point for DAG manager."""
    parser = argparse.ArgumentParser(
        description="Generate HTCondor DAG for FASER alignment workflow"
    )
    
    # parser.add_argument('--year', '-y', type=str, required=True,
    #                     help='Year (e.g., 2022-2025)')
    # parser.add_argument('--run', '-r', type=str, required=True,
    #                     help='Run number (e.g., 011705, will be padded to 6 digits)')
    # parser.add_argument('--files', '-f', type=str, required=True,
    #                     help='Raw file number or range (e.g., 400, 400-500, 400:500)')
    # parser.add_argument('--iterations', '-i', type=int, required=True,
    #                     help='Number of iterations to perform')
    # parser.add_argument('--fourst', action='store_true', default=False,
    #                     help='Enable 4-station mode')
    # parser.add_argument('--threest', action='store_true', default=True,
    #                     help='Enable 3-station mode')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to configuration file')
    parser.add_argument('--submit', action='store_true', default=False,
                        help='Automatically submit DAG to HTCondor')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = AlignmentConfig(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run 'python config.py' to create a default configuration file.")
        return 1
    
    # # Format arguments
    # year_str = args.year.zfill(4)
    # run_str = args.run.zfill(6)
    
    # try:
    #     file_list = RawList(args.files)
    # except ValueError as e:
    #     print(f"Error: {e}")
    #     return 1
    
    # print(f"Generating DAG for Year: {year_str}, Run: {run_str}, Files: {file_list}, Iterations: {args.iterations}")
    
    # # Setup paths
    # src_dir = Path(__file__).parent.resolve()
    # reco_env_path = Path(config.reco_env_script).resolve()
    # millepede_env_path = Path(config.millepede_env_script).resolve()
    
    # # Determine output directory based on configuration
    # # Use EOS output directory if configured and enabled, otherwise use work_dir or src_dir
    # main_str = f"Y{year_str}_R{run_str}_F{str(file_list)}"
    # if config.use_eos_storage and config.eos_output_dir:
    #     # Use EOS for large output files
    #     main_dir = Path(config.eos_output_dir) / main_str
    #     print(f"Using EOS output directory: {main_dir}")
    # elif config.work_dir:
    #     # Use configured work directory
    #     main_dir = Path(config.work_dir) / main_str
    #     print(f"Using work directory: {main_dir}")
    # else:
    #     # Fallback to script directory
    #     main_dir = src_dir / main_str
    #     print(f"Using script directory: {main_dir}")
    # dag_dir = (
    #     Path(config.work_dir) / "dag_files" / main_str
    #     ) if config.work_dir else main_dir
    # main_dir.mkdir(parents=True, exist_ok=True)
    # dag_dir.mkdir(parents=True, exist_ok=True)
    
    # Create DAG
    dag_manager = DAGManager(config)
    dag_manager.create_data_dirs()
    dag_manager.creat_dag_dirs()
    dag_manager.copy_first_inputforalign()
    dag_manager.create_reco_exeenv_files()
    dag_manager.create_reco_submit_files()
    dag_manager.create_mille_exeenv_files()
    dag_manager.create_mille_submit_files()
    dag_path = dag_manager.create_dag_file()
    dag_dir = dag_path.parent
    # dag_file = dag_manager.create_dag_file(
    #     main_dir, year_str, run_str, file_list, args.iterations,
    #     args.fourst, args.threest, src_dir, reco_env_path, millepede_env_path, dag_dir
    # )
    
    # print(f"\nDAG file created successfully: {dag_file}")
    # print(f"\nTo submit the DAG, run:")
    # print(f"  condor_submit_dag {dag_file}")
    
    if args.submit:
        import subprocess
        print("\nSubmitting DAG to HTCondor...")
        
        try:
            result = subprocess.run(
                ["condor_submit_dag", str(dag_path)],
                cwd=dag_dir,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.returncode != 0:
                print(f"Error submitting DAG: {result.stderr}")
                return 1
        except Exception as e:
            print(f"Exception occurred while submitting DAG: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
