import os
import sys
import argparse
import shutil
import subprocess
from RawList import RawList

# python3 main.py -y 2023 -r 011705 -f 400-450 -i 5 &>main.log

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Generate and submit Condor job for FASER alignment")

parser.add_argument('--year', '-y', type=str, required=True,
                    help='Year (e.g., 2022-2025)')
parser.add_argument('--run', '-r', type=str, required=True,
                    help='Run number (e.g., 011705, will be padded to 6 digits)')
parser.add_argument('--file', '-f', type=str, required=True,
                    help='Raw file number or range. Single file: 400; Range: 400-500 or 400:500')
parser.add_argument('--iteration', '-i', type=str, required=True,
                    help='Iteration number (integer, required)')
parser.add_argument('--fourst', action='store_true', default=False,
                    help='Run 4 Stations')
parser.add_argument('--threest', action='store_true', default=True,
                    help='Run 3 Stations')
args = parser.parse_args()

# --- Format run, file, iter number  ---
try:
    file_list = RawList(args.file)
except ValueError as e:
    parser.error(str(e))
run_str = args.run.zfill(6)
iter_str = args.iteration.zfill(2)
print(f"Processing ...")
print(f"\tYear: {args.year} Run: {run_str}, File: {file_list}, Iteration: {iter_str}")

# --- Env Path ---
env_path = "/eos/home-s/shunlian/Alignment/env.sh"
if not os.path.isfile(env_path):
    raise FileNotFoundError(f"Environment script not found: {env_path}")

# --- Make work dir ---
main_str = f"Y{args.year}_R{run_str}_F{str(file_list)}"
src_dir = os.path.dirname(os.path.abspath(__file__))
main_dir = os.path.join(src_dir, main_str)
iter_dir = os.path.join(main_dir, f"iter{iter_str}")
reco_dir = os.path.join(iter_dir, "1reco")
kfalign_dir = os.path.join(iter_dir, "2kfalignment")
os.makedirs(reco_dir, exist_ok=True)
os.makedirs(kfalign_dir, exist_ok=True)
os.chdir(reco_dir)
print(f"Changed cwd to: {reco_dir}")
# --- Prepare executable ---
exe_str = "runAlignment.sh"
exe_path = os.path.join(src_dir, exe_str)
shutil.copy2(exe_path, reco_dir)
print(f"Copied {exe_str} to: {reco_dir}")
# --- Prepare inputforalign.txt ---
input_str = "inputforalign.txt"
input_path = os.path.join(reco_dir, input_str)
if int(iter_str) == 1:
    open(input_path, 'w').close()
else:
    last_iter_str = f"iter{int(iter_str)-1:02d}"
    last_iter_dir = os.path.join(main_dir, last_iter_str)
    cp_path = os.path.join(last_iter_dir, input_str)
    try:
        shutil.copy2(cp_path, input_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Alignment file not found: {cp_path}")
print(f"Prepared {input_str} at: {input_path}")

# --- Condor submit file template ---
submit_content = f"""executable = runAlignment.sh

output = logs/job_$(Cluster)_$(Process).out
error  = logs/job_$(Cluster)_$(Process).err
log    = logs/job_$(Cluster)_$(Process).log

request_cpus = 1
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_output_files = logs/

+JobFlavour           = "longlunch"
#+AccountingGroup = "group_u_FASER.users" #Add when you have access to faser computing group
on_exit_remove          = (ExitBySignal == False) && (ExitCode == 0)
max_retries             = 3
requirements = (Machine =!= LastRemoteHost) && (OpSysAndVer =?= "AlmaLinux9")

"""

# --- Add job entries to .sub ---
for file_str in file_list:
    script_args = f"{args.year} {run_str} {file_str} {args.fourst} {args.threest} {reco_dir} {src_dir} {env_path}"
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