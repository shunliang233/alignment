#!/usr/bin/env python3
"""
HTCondor DAGman manager for FASER alignment workflow.

This module generates and manages HTCondor DAG files for iterative alignment,
replacing the daemon-based approach with a more robust DAGman-based solution.
"""

import os
import argparse
from pathlib import Path
from typing import List, Optional
from RawList import RawList
from config import AlignmentConfig


class DAGManager:
    """Manages HTCondor DAG generation for alignment workflow."""
    
    # Default HTCondor requirements
    DEFAULT_REQUIREMENTS = "(Machine =!= LastRemoteHost) && (OpSysAndVer =?= \"AlmaLinux9\")"
    
    def __init__(self, config: AlignmentConfig):
        """
        Initialize DAG manager.
        
        Args:
            config: AlignmentConfig instance
        """
        self.config = config
    
    def create_reco_submit_file(
        self, 
        output_dir: Path,
        iteration: int,
        year: str,
        run: str,
        file_str: str,
        fourst: bool,
        threest: bool,
        src_dir: Path,
        env_path: Path,
        work_dir: Path
    ) -> Path:
        """
        Create HTCondor submit file for a single reconstruction job.
        
        Args:
            output_dir: Main output directory for job data
            iteration: Iteration number
            year: Year of data taking
            run: Run number (6 digits)
            file_str: File number as string (e.g., "00400")
            fourst: Enable 4-station mode
            threest: Enable 3-station mode
            src_dir: Source directory path
            env_path: Environment script path
            work_dir: Work directory for DAG and log files
            
        Returns:
            Path to created submit file
        """
        iter_str = f"iter{iteration:02d}"
        reco_dir = output_dir / iter_str / "1reco"
        kfalign_dir = output_dir / iter_str / "2kfalignment"
        
        # Create individual submit file for this file in work_dir
        submit_file = work_dir / iter_str / f"reco_{iter_str}_{file_str}.sub"
        
        # Log files go in work_dir to avoid collisions between parallel DAGs
        log_dir = work_dir / iter_str / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        submit_content = f"""# HTCondor submit file for reconstruction job (file {file_str})
universe = vanilla
executable = {src_dir}/runAlignment.sh

output = {log_dir}/reco_{iter_str}_{file_str}.out
error  = {log_dir}/reco_{iter_str}_{file_str}.err
log    = {log_dir}/reco_{iter_str}_{file_str}.log

request_cpus = {self.config.get('htcondor.reco.request_cpus', 1)}
request_memory = {self.config.get('htcondor.reco.request_memory', '2 GB')}
request_disk = {self.config.get('htcondor.reco.request_disk', '2 GB')}
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_output_files = logs/

+JobFlavour = "{self.config.get('htcondor.reco.job_flavour', 'longlunch')}"
on_exit_remove = (ExitBySignal == False) && (ExitCode == 0)
max_retries = {self.config.get('htcondor.reco.max_retries', 3)}
requirements = {self.config.get('htcondor.requirements', self.DEFAULT_REQUIREMENTS)}

arguments = {year} {run} {file_str} {fourst} {threest} {reco_dir} {kfalign_dir} {src_dir} {env_path}
queue
"""
        
        # Write submit file
        submit_file.parent.mkdir(parents=True, exist_ok=True)
        with open(submit_file, 'w') as f:
            f.write(submit_content)
        
        return submit_file

    def create_millepede_submit_file(
        self,
        output_dir: Path,
        iteration: int,
        src_dir: Path,
        env_path: Path,
        work_dir: Path,
        to_next_iter: bool = True
    ) -> Path:
        """
        Create HTCondor submit file for Millepede job.
        
        Args:
            output_dir: Main output directory for job data
            iteration: Iteration number
            src_dir: Source directory path
            env_path: Environment script path
            work_dir: Work directory for DAG and log files
            to_next_iter: Whether to copy results to next iteration
            
        Returns:
            Path to created submit file
        """
        iter_str = f"iter{iteration:02d}"
        millepede_dir = output_dir / iter_str / "3millepede"
        kfalign_dir = output_dir / iter_str / "2kfalignment"
        
        # Submit file and wrapper script go in work_dir
        submit_file = work_dir / iter_str / "millepede.sub"
        wrapper_script = work_dir / iter_str / "run_millepede.sh"
        
        # Log files go in work_dir to avoid collisions between parallel DAGs
        log_dir = work_dir / iter_str / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        wrapper_content = f"""#!/bin/bash
set -e

echo "Setting up environment..."
source {env_path}

echo "Running Millepede..."
python3 {src_dir}/millepede/bin/millepede.py -i {kfalign_dir}

echo "Millepede completed successfully."
"""
        if to_next_iter:
            next_iter_str = f"iter{iteration+1:02d}"
            next_input = output_dir / next_iter_str / "1reco" / "inputforalign.txt"
            wrapper_content += f"""
echo "Transferring alignment constants to next iteration..."
if [ -f "{output_dir / iter_str}/inputforalign.txt" ]; then
    cp "{output_dir / iter_str}/inputforalign.txt" "{next_input}"
    echo "Alignment constants transferred successfully."
else
    echo "Warning: Alignment constants not found. Using empty file."
    touch "{next_input}"
fi
"""
        wrapper_script.parent.mkdir(parents=True, exist_ok=True)
        with open(wrapper_script, 'w') as f:
            f.write(wrapper_content)
        os.chmod(wrapper_script, 0o755)
        
        submit_content = f"""# HTCondor submit file for Millepede job
universe = vanilla
executable = {wrapper_script}

output = {log_dir}/millepede.out
error  = {log_dir}/millepede.err
log    = {log_dir}/millepede.log

request_cpus = {self.config.get('htcondor.millepede.request_cpus', 1)}
request_memory = {self.config.get('htcondor.millepede.request_memory', '2 GB')}
request_disk = {self.config.get('htcondor.millepede.request_disk', '2 GB')}
should_transfer_files = YES
when_to_transfer_output = ON_EXIT

+JobFlavour = "{self.config.get('htcondor.millepede.job_flavour', 'espresso')}"
on_exit_remove = (ExitBySignal == False) && (ExitCode == 0)
max_retries = {self.config.get('htcondor.millepede.max_retries', 2)}

queue
"""
        
        with open(submit_file, 'w') as f:
            f.write(submit_content)
        
        return submit_file
    
    def create_dag_file(
        self,
        output_dir: Path,
        year: str,
        run: str,
        file_list: RawList,
        iterations: int,
        fourst: bool,
        threest: bool,
        src_dir: Path,
        reco_env_path: Path,
        millepede_env_path: Path,
        work_dir: Path
    ) -> Path:
        """
        Create HTCondor DAG file for complete alignment workflow.
        
        Args:
            output_dir: Main output directory for job data
            year: Year of data taking
            run: Run number (6 digits)
            file_list: RawList object with file numbers
            iterations: Number of iterations to perform
            fourst: Enable 4-station mode
            threest: Enable 3-station mode
            src_dir: Source directory path
            reco_env_path: Reconstruction environment script path
            millepede_env_path: Millepede environment script path
            work_dir: Work directory for DAG and log files
            
        Returns:
            Path to created DAG file
        """
        dag_file = work_dir / "alignment.dag"

        dag_content = "# HTCondor DAG for FASER alignment workflow\n\n"
        
        # Create jobs for each iteration
        for it in range(1, iterations + 1):
            # Setup job script for each iteration
            self._create_setup_job_script(output_dir, it)
            
            # Create individual reconstruction jobs for each file
            dag_content += f"# Iteration {it} reconstruction jobs\n"
            reco_jobs = []
            for file_str in file_list:
                job_name = f"reco_{it:02d}_{file_str}"
                reco_jobs.append(job_name)
                reco_submit = self.create_reco_submit_file(
                    output_dir, it, year, run, file_str, fourst, threest, src_dir, reco_env_path, work_dir
                )
                dag_content += f"JOB {job_name} {reco_submit}\n"
            
            # Millepede job
            dag_content += f"\n# Iteration {it} millepede job\n"
            mille_submit = self.create_millepede_submit_file(
                output_dir, it, src_dir, millepede_env_path, work_dir,
                to_next_iter=(it < iterations)
            )
            dag_content += f"JOB millepede_{it:02d} {mille_submit}\n"
            
            # Add dependencies
            dag_content += f"\n# Iteration {it} dependencies\n"
            # All reconstruction jobs must complete before millepede
            for reco_job in reco_jobs:
                dag_content += f"PARENT {reco_job} CHILD millepede_{it:02d}\n"
            
            # Link iterations - millepede from previous iteration must complete
            # before any reconstruction job in the current iteration starts
            if it > 1:
                for reco_job in reco_jobs:
                    dag_content += f"PARENT millepede_{it-1:02d} CHILD {reco_job}\n"
            
            dag_content += "\n"
        
        # Add retry settings
        dag_content += "# Retry settings\n"
        for it in range(1, iterations + 1):
            for file_str in file_list:
                job_name = f"reco_{it:02d}_{file_str}"
                dag_content += f"RETRY {job_name} 2\n"
            dag_content += f"RETRY millepede_{it:02d} 1\n"
        
        # Write DAG file
        with open(dag_file, 'w') as f:
            f.write(dag_content)
        
        print(f"Created DAG file: {dag_file}")
        return dag_file

    def _create_setup_job_script(self, output_dir: Path, iteration: int) -> None:
        """
        Create setup script for an iteration (prepare directories and input files).
        
        Args:
            output_dir: Main output directory
            iteration: Iteration number
        """
        iter_str = f"iter{iteration:02d}"
        iter_dir = output_dir / iter_str
        reco_dir = iter_dir / "1reco"
        kfalign_dir = iter_dir / "2kfalignment"
        millepede_dir = iter_dir / "3millepede"
        
        # Create directories
        reco_dir.mkdir(parents=True, exist_ok=True)
        kfalign_dir.mkdir(parents=True, exist_ok=True)
        millepede_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare inputforalign.txt
        # For iteration 1, create empty file
        # For subsequent iterations, create empty placeholder
        # (actual alignment constants will be copied by pre-script during job execution)
        input_path = reco_dir / "inputforalign.txt"
        input_path.touch()


def main():
    """Main entry point for DAG manager."""
    parser = argparse.ArgumentParser(
        description="Generate HTCondor DAG for FASER alignment workflow"
    )
    
    parser.add_argument('--year', '-y', type=str, required=True,
                        help='Year (e.g., 2022-2025)')
    parser.add_argument('--run', '-r', type=str, required=True,
                        help='Run number (e.g., 011705, will be padded to 6 digits)')
    parser.add_argument('--files', '-f', type=str, required=True,
                        help='Raw file number or range (e.g., 400, 400-500, 400:500)')
    parser.add_argument('--iterations', '-i', type=int, required=True,
                        help='Number of iterations to perform')
    parser.add_argument('--fourst', action='store_true', default=False,
                        help='Enable 4-station mode')
    parser.add_argument('--threest', action='store_true', default=True,
                        help='Enable 3-station mode')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to configuration file')
    parser.add_argument('--submit', action='store_true',
                        help='Automatically submit DAG to HTCondor')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = AlignmentConfig(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run 'python config.py' to create a default configuration file.")
        return 1
    
    # Format arguments
    year_str = args.year.zfill(4)
    run_str = args.run.zfill(6)
    
    try:
        file_list = RawList(args.files)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    print(f"Generating DAG for Year: {year_str}, Run: {run_str}, Files: {file_list}, Iterations: {args.iterations}")
    
    # Setup paths
    src_dir = Path(__file__).parent.absolute()
    reco_env_path = Path(config.reco_env_script).absolute()
    millepede_env_path = Path(config.millepede_env_script).absolute()
    
    # Determine output directory based on configuration
    # Use EOS output directory if configured and enabled, otherwise use work_dir or src_dir
    main_str = f"Y{year_str}_R{run_str}_F{str(file_list)}"
    
    if config.use_eos_storage and config.eos_output_dir:
        # Use EOS for large output files
        main_dir = Path(config.eos_output_dir) / main_str
        print(f"Using EOS output directory: {main_dir}")
    elif config.work_dir:
        # Use configured work directory
        main_dir = Path(config.work_dir) / main_str
        print(f"Using work directory: {main_dir}")
    else:
        # Fallback to script directory
        main_dir = src_dir / main_str
        print(f"Using script directory: {main_dir}")

    dag_dir = os.path.join(
        config.work_dir,
        "dag_files",
        main_str,
    ) if config.work_dir else main_dir
    
    main_dir.mkdir(parents=True, exist_ok=True)
    Path(dag_dir).mkdir(parents=True, exist_ok=True)
    
    # Create DAG
    dag_manager = DAGManager(config)
    dag_file = dag_manager.create_dag_file(
        main_dir, year_str, run_str, file_list, args.iterations,
        args.fourst, args.threest, src_dir, reco_env_path, millepede_env_path, Path(dag_dir)
    )
    
    print(f"\nDAG file created successfully: {dag_file}")
    print(f"\nTo submit the DAG, run:")
    print(f"  condor_submit_dag {dag_file}")
    
    if args.submit:
        import subprocess
        print("\nSubmitting DAG to HTCondor...")
        result = subprocess.run(
            ["condor_submit_dag", str(dag_file)],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"Error submitting DAG: {result.stderr}")
            return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
