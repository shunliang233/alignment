import os
import argparse
import subprocess
from RawList import RawList

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Generate and submit Condor job for FASER alignment")

parser.add_argument('--year', '-y', type=str, required=True,
                    help='Year (e.g., 2022-2025)')
parser.add_argument('--run', '-r', type=str, required=True,
                    help='Run number (e.g., 011705, will be padded to 6 digits)')
parser.add_argument('--file', '-f', type=str, required=True,
                    help='Raw file number or range. Single file: 400; Range: 400-500 or 400:500')
parser.add_argument('--iteration', '-i', type=int, required=True,
                    help='Iteration number (integer, required)')
parser.add_argument('--align', '-a', type=str, required=True,
                    help='Path to inputforalign.txt file (required)')
parser.add_argument('--fourst', action='store_true', default=False,
                    help='Run 4 Stations')
parser.add_argument('--threest', action='store_true', default=True,
                    help='Run 3 Stations')
args = parser.parse_args()

# --- Format run, file number, align path  ---
try:
    file_list = RawList(args.file)
except ValueError as e:
    parser.error(str(e))
run_str = args.run.zfill(6)
try:
    align_path = os.path.abspath(args.align)
    if not os.path.isfile(align_path):
        raise FileNotFoundError(f"Alignment parameter file not found: {align_path}")
except Exception as e:
    parser.error(str(e))
print(f"Processing ...")
print(f"\tYear: {args.year} Run: {run_str}, File: {file_list}, Iteration: {args.iteration}")
print(f"\tAlignment Parameters: {align_path}")

# --- Condor submit file template ---
submit_content = f"""executable = runAlignment.sh

output = logs{args.iteration}/job_$(Cluster)_$(Process).out
error  = logs{args.iteration}/job_$(Cluster)_$(Process).err
log    = logs{args.iteration}/job_$(Cluster)_$(Process).log

request_cpus = 1
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_output_files = logs{args.iteration}/

+JobFlavour           = "longlunch"
#+AccountingGroup = "group_u_FASER.users" #Add when you have access to faser computing group
on_exit_remove          = (ExitBySignal == False) && (ExitCode == 0)
max_retries             = 3
requirements = (Machine =!= LastRemoteHost) && (OpSysAndVer =?= "AlmaLinux9")

"""

# --- Add job entries to .sub ---
for file_str in file_list:
    script_args = f"{args.year} {run_str} {file_str} {args.fourst} {args.threest} {args.iteration} {align_path}"
    submit_content += f"arguments = {script_args}\nqueue\n\n"

# --- Save to .sub file ---
submit_filename = "submit_unbiased.sub"
with open(submit_filename, "w") as f:
    f.write(submit_content)
print(f"Condor submit file '{submit_filename}' created.")

# --- Submit the job to Condor ---
try:
    result = subprocess.run(["condor_submit", "-spool", submit_filename], check=True, capture_output=True, text=True)
    print("Condor submission successful.")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error submitting job to Condor:")
    print(e.stderr)