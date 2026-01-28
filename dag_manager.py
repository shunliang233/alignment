#!/usr/bin/env python3
"""
HTCondor DAGman manager for FASER alignment workflow.

This module generates and manages HTCondor DAG files for iterative alignment,
replacing the daemon-based approach with a more robust DAGman-based solution.
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Optional

from AlignmentConfig import AlignmentConfig
import ColorfulPrint

# Test: python3 dag_manager.py --submit

# TODO: Ask claude to modify it according to Config.py and AlignmentConfig.py changes
# TODO: 运行前检查 config.json 中的路径是否存在，以及各种语法合理性
# TODO: 支持断点执行
class DAGManager:
    """Manages HTCondor DAG generation for alignment workflow."""
    
    def __init__(self, config: AlignmentConfig):
        """
        Initialize DAG manager.
        
        Args:
            config: AlignmentConfig instance
        """
        self.config = config

    def create_data_dirs(self) -> None:
        """Create data directories for all iterations."""
        data_dir = self.config.data_dir
        if data_dir.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Data directory already exists: {data_dir}")
        else:
            data_dir.mkdir(parents=True)
        for it in range(self.config.iters_int):
            iter_dir = self.config.data_iter_dir(it)
            if iter_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Iteration directory already exists: {iter_dir}")
            else:
                iter_dir.mkdir(parents=True)
            reco_dir = self.config.reco_dir(it)
            if reco_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Reconstruction directory already exists: {reco_dir}")
            else:
                reco_dir.mkdir(parents=True)
            kfalign_dir = self.config.kfalign_dir(it)
            if kfalign_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"KF alignment directory already exists: {kfalign_dir}")
            else:
                kfalign_dir.mkdir(parents=True)
            millepede_dir = self.config.millepede_dir(it)
            if millepede_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Millepede directory already exists: {millepede_dir}")
            else:
                millepede_dir.mkdir(parents=True)
    
    def creat_dag_dirs(self) -> None:
        """Create DAG working directories for all iterations."""
        dag_dir = self.config.dag_dir
        if dag_dir.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"DAG directory already exists: {dag_dir}")
        else:
            dag_dir.mkdir(parents=True)
        for it in range(self.config.iters_int):
            iter_dir = self.config.dag_iter_dir(it)
            if iter_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"DAG iteration directory already exists: {iter_dir}")
            else:
                iter_dir.mkdir(parents=True)
            logs_dir = self.config.logs_dir(it)
            if logs_dir.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Logs directory already exists: {logs_dir}")
            else:
                logs_dir.mkdir(parents=True)
    
    def copy_first_inputforalign(self) -> None:
        it = 0
        reco_dir = self.config.reco_dir(it)
        shutil.copy(self.config.tpl_inputforalign, reco_dir)
    
    def create_reco_exe_files(self) -> None:
        """Create reco executable script in DAG directory."""
        dag_recoexe = self.config.dag_recoexe
        if dag_recoexe.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting reco executable: {dag_recoexe}")
        shutil.copy(self.config.tpl_recoexe, dag_recoexe)
    
    def create_reco_submit_files(self) -> None:
        """Create reco submit files for all iterations and raw files."""
        for it in range(self.config.iters_int):
            for file_str in self.config.files:
                with open(self.config.tpl_recosub, 'r') as tpl_file:
                    tpl_content = tpl_file.read()
                if not self.config.dag_recoexe.exists():
                    raise FileNotFoundError(f"Reco executable not found: {self.config.dag_recoexe}")
                if not self.config.logs_dir(it).exists():
                    raise FileNotFoundError(f"Logs directory not found: {self.config.logs_dir(it)}")
                if not self.config.reco_dir(it).exists():
                    raise FileNotFoundError(f"Reco directory not found: {self.config.reco_dir(it)}")
                if not self.config.kfalign_dir(it).exists():
                    raise FileNotFoundError(f"KF alignment directory not found: {self.config.kfalign_dir(it)}")
                sub_content = tpl_content.format(
                    year=self.config.year,
                    run=self.config.run,
                    stations=self.config.stations,
                    file_str=file_str,
                    exe_path=self.config.dag_recoexe,
                    out_path=self.config.logs_reco_out(it, file_str),
                    err_path=self.config.logs_reco_err(it, file_str),
                    log_path=self.config.logs_reco_log(it, file_str),
                    reco_dir=self.config.reco_dir(it),
                    kfalign_dir=self.config.kfalign_dir(it),
                    src_dir=self.config.src_dir,
                    calypso_asetup=self.config.env_calypso_asetup,
                    calypso_setup=self.config.env_calypso_setup,
                )
                recosub = self.config.dag_recosub(it, file_str)
                if recosub.exists():
                    ColorfulPrint.print_yellow(f"Warning: ")
                    print(f"Overwritting reco submit file: {recosub}")
                with open(recosub, 'w') as sub_file:
                    sub_file.write(sub_content)

    def create_mille_exe_files(self) -> None:
        """Create millepede executable script in DAG directory."""
        dag_milleexe = self.config.dag_milleexe
        if dag_milleexe.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting millepede executable: {dag_milleexe}")
        shutil.copy(self.config.tpl_milleexe, dag_milleexe)
    
    def create_mille_submit_files(self) -> None:
        """Create millepede submit files for all iterations."""
        for it in range(self.config.iters_int):
            with open(self.config.tpl_millesub, 'r') as tpl_file:
                tpl_content = tpl_file.read()
            if not self.config.dag_milleexe.exists():
                raise FileNotFoundError(f"Millepede executable not found: {self.config.dag_milleexe}")
            if not self.config.logs_dir(it).exists():
                raise FileNotFoundError(f"Logs directory not found: {self.config.logs_dir(it)}")
            if not self.config.kfalign_dir(it).exists():
                raise FileNotFoundError(f"KF alignment directory not found: {self.config.kfalign_dir(it)}")
            sub_content = tpl_content.format(
                exe_path=self.config.dag_milleexe,
                out_path=self.config.logs_mille_out(it),
                err_path=self.config.logs_mille_err(it),
                log_path=self.config.logs_mille_log(it),
                to_next_iter=(it < self.config.iters_int - 1),
                src_dir=self.config.src_dir,
                kfalign_dir=self.config.kfalign_dir(it),
                next_reco_dir=self.config.reco_dir(it + 1) if it < self.config.iters_int - 1 else "",
                env_pede=self.config.env_pede,
                env_root=self.config.env_root
            )
            millesub = self.config.dag_millesub(it)
            if millesub.exists():
                ColorfulPrint.print_yellow(f"Warning: ")
                print(f"Overwritting millepede submit file: {millesub}")
            with open(millesub, 'w') as sub_file:
                sub_file.write(sub_content)

    def create_dag_file(self) -> Path:
        """Create DAG file for complete alignment workflow."""
        dag_file = self.config.dag_file
        if dag_file.exists():
            ColorfulPrint.print_yellow(f"Warning: ")
            print(f"Overwritting DAG file: {dag_file}")
        dag_content = "# HTCondor DAG for FASER alignment workflow\n\n"
        for it in range(self.config.iters_int):
            # reco jobs
            dag_content += f"# Iteration {it} reconstruction jobs\n"
            for file_str in self.config.files:
                reco_sub = self.config.dag_recosub(it, file_str)
                reco_job = self.config.dag_recojob(it, file_str)
                dag_content += f"JOB {reco_job} {reco_sub}\n"
            # mille jobs
            dag_content += f"\n# Iteration {it} millepede job\n"
            mille_sub = self.config.dag_millesub(it)
            mille_job = self.config.dag_millejob(it)
            dag_content += f"JOB {mille_job} {mille_sub}\n"
            # add dependencies
            dag_content += f"\n# Iteration {it} dependencies\n"
            for file_str in self.config.files:
                reco_job = self.config.dag_recojob(it, file_str)
                dag_content += f"PARENT {reco_job} CHILD {mille_job}\n"
                if it != 0:
                    last_mille_job = self.config.dag_millejob(it-1)
                    dag_content += f"PARENT {last_mille_job} CHILD {reco_job}\n"
            dag_content += "\n"
        # Add retry settings
        dag_content += "# Retry settings\n"
        for it in range(self.config.iters_int):
            for file_str in self.config.files:
                reco_job = self.config.dag_recojob(it, file_str)
                dag_content += f"RETRY {reco_job} 2\n"
            mille_job = self.config.dag_millejob(it)
            dag_content += f"RETRY {mille_job} 1\n"
        with open(dag_file, 'w') as f:
            f.write(dag_content)
        return dag_file



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
        config = AlignmentConfig(Path(args.config))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please check your configuration file.")
        return 1
    except (TypeError, ValueError) as e:
        print(f"Configuration error: {e}")
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
    dag_manager.create_reco_exe_files()
    dag_manager.create_reco_submit_files()
    dag_manager.create_mille_exe_files()
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
