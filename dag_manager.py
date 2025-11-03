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
        year: str,
        run: str,
        file_list: RawList,
        iteration: int,
        fourst: bool,
        threest: bool,
        src_dir: Path,
        env_path: Path
    ) -> Path:
        """
        Create HTCondor submit file for reconstruction jobs.
        
        Args:
            output_dir: Directory where to create submit file
            year: Year of data taking
            run: Run number (6 digits)
            file_list: RawList object with file numbers
            iteration: Iteration number
            fourst: Enable 4-station mode
            threest: Enable 3-station mode
            src_dir: Source directory path
            env_path: Environment script path
            
        Returns:
            Path to created submit file
        """
        iter_str = f"iter{iteration:02d}"
        reco_dir = output_dir / iter_str / "1reco"
        
        submit_file = reco_dir / "reco.sub"
        
        submit_content = f"""# HTCondor submit file for reconstruction jobs
universe = vanilla
executable = {src_dir}/runAlignment.sh

output = logs/reco_$(Process).out
error  = logs/reco_$(Process).err
log    = logs/reco_$(Process).log

request_cpus = {self.config.get('htcondor.request_cpus', 1)}
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_output_files = logs/

+JobFlavour = "{self.config.get('htcondor.job_flavour', 'longlunch')}"
on_exit_remove = (ExitBySignal == False) && (ExitCode == 0)
max_retries = {self.config.get('htcondor.max_retries', 3)}
requirements = {self.config.get('htcondor.requirements', '(Machine =!= LastRemoteHost) && (OpSysAndVer =?= "AlmaLinux9")')}

"""
        
        # Add job entries for each file
        for file_str in file_list:
            script_args = f"{year} {run} {file_str} {fourst} {threest} {reco_dir} {src_dir} {env_path}"
            submit_content += f"arguments = {script_args}\nqueue\n\n"
        
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
        env_path: Path
    ) -> Path:
        """
        Create HTCondor submit file for Millepede job.
        
        Args:
            output_dir: Directory where to create submit file
            iteration: Iteration number
            src_dir: Source directory path
            env_path: Environment script path
            
        Returns:
            Path to created submit file
        """
        iter_str = f"iter{iteration:02d}"
        millepede_dir = output_dir / iter_str / "3millepede"
        kfalign_dir = output_dir / iter_str / "2kfalignment"
        
        submit_file = millepede_dir / "millepede.sub"
        
        # Create wrapper script for millepede
        wrapper_script = millepede_dir / "run_millepede.sh"
        wrapper_content = f"""#!/bin/bash
set -e

echo "Setting up environment..."
source {env_path}

echo "Running Millepede..."
python3 {src_dir}/millepede/bin/millepede.py -i {kfalign_dir}

echo "Millepede completed successfully."
"""
        
        wrapper_script.parent.mkdir(parents=True, exist_ok=True)
        with open(wrapper_script, 'w') as f:
            f.write(wrapper_content)
        os.chmod(wrapper_script, 0o755)
        
        submit_content = f"""# HTCondor submit file for Millepede job
universe = vanilla
executable = {wrapper_script}

output = millepede.out
error  = millepede.err
log    = millepede.log

request_cpus = 1
should_transfer_files = YES
when_to_transfer_output = ON_EXIT

+JobFlavour = "espresso"
on_exit_remove = (ExitBySignal == False) && (ExitCode == 0)
max_retries = 2

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
        env_path: Path
    ) -> Path:
        """
        Create HTCondor DAG file for complete alignment workflow.
        
        Args:
            output_dir: Main output directory
            year: Year of data taking
            run: Run number (6 digits)
            file_list: RawList object with file numbers
            iterations: Number of iterations to perform
            fourst: Enable 4-station mode
            threest: Enable 3-station mode
            src_dir: Source directory path
            env_path: Environment script path
            
        Returns:
            Path to created DAG file
        """
        dag_file = output_dir / "alignment.dag"
        
        dag_content = "# HTCondor DAG for FASER alignment workflow\n\n"
        
        # Create jobs for each iteration
        for it in range(1, iterations + 1):
            # Reconstruction job
            reco_submit = self.create_reco_submit_file(
                output_dir, year, run, file_list, it, fourst, threest, src_dir, env_path
            )
            dag_content += f"JOB reco_{it:02d} {reco_submit}\n"
            
            # Millepede job
            mille_submit = self.create_millepede_submit_file(
                output_dir, it, src_dir, env_path
            )
            dag_content += f"JOB millepede_{it:02d} {mille_submit}\n"
            
            # Setup job script for each iteration
            self._create_setup_job_script(output_dir, it)
            
            # Add PRE script for iterations > 1 to copy alignment constants
            if it > 1:
                pre_script = self._create_pre_script(output_dir, it)
                dag_content += f"SCRIPT PRE reco_{it:02d} {pre_script}\n"
            
            # Add dependencies
            dag_content += f"\n# Iteration {it} dependencies\n"
            dag_content += f"PARENT reco_{it:02d} CHILD millepede_{it:02d}\n"
            
            # Link iterations
            if it > 1:
                dag_content += f"PARENT millepede_{it-1:02d} CHILD reco_{it:02d}\n"
            
            dag_content += "\n"
        
        # Add retry settings
        dag_content += "# Retry settings\n"
        for it in range(1, iterations + 1):
            dag_content += f"RETRY reco_{it:02d} 2\n"
            dag_content += f"RETRY millepede_{it:02d} 1\n"
        
        # Write DAG file
        with open(dag_file, 'w') as f:
            f.write(dag_content)
        
        print(f"Created DAG file: {dag_file}")
        return dag_file
    
    def _create_pre_script(self, output_dir: Path, iteration: int) -> Path:
        """
        Create PRE script for copying alignment constants from previous iteration.
        
        Args:
            output_dir: Main output directory
            iteration: Current iteration number
            
        Returns:
            Path to pre script
        """
        iter_str = f"iter{iteration:02d}"
        iter_dir = output_dir / iter_str
        
        pre_script = iter_dir / "pre_reco.sh"
        
        prev_iter = f"iter{iteration-1:02d}"
        prev_input = output_dir / prev_iter / "inputforalign.txt"
        curr_input = iter_dir / "1reco" / "inputforalign.txt"
        
        script_content = f"""#!/bin/bash
# PRE script to copy alignment constants from previous iteration

set -e

echo "Copying alignment constants from iteration {iteration-1} to {iteration}..."

if [ -f "{prev_input}" ]; then
    cp "{prev_input}" "{curr_input}"
    echo "Alignment constants copied successfully."
else
    echo "Warning: Previous alignment constants not found. Using empty file."
    touch "{curr_input}"
fi

exit 0
"""
        
        with open(pre_script, 'w') as f:
            f.write(script_content)
        os.chmod(pre_script, 0o755)
        
        return pre_script
    
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
    env_path = Path(config.env_script).absolute()
    
    # Create main directory
    main_str = f"Y{year_str}_R{run_str}_F{str(file_list)}"
    main_dir = src_dir / main_str
    main_dir.mkdir(exist_ok=True)
    
    # Create DAG
    dag_manager = DAGManager(config)
    dag_file = dag_manager.create_dag_file(
        main_dir, year_str, run_str, file_list, args.iterations,
        args.fourst, args.threest, src_dir, env_path
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
