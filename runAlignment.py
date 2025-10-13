import argparse
import subprocess

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Generate and submit Condor job for FASER alignment")

parser.add_argument('--year', '-y', type=str, required=True,
                    help='Year (e.g., 2022-2025)')
parser.add_argument('--run', '-r', type=str, required=True,
                    help='Run number (e.g., 011705, will be padded to 6 digits)')
parser.add_argument('--rawfile', '-f', type=str, required=True,
                    help='Raw file number (e.g., 00400)')
parser.add_argument('--fourst', action='store_true', default=False,
                    help='Run 4 Stations')
parser.add_argument('--threest', action='store_true', default=True,
                    help='Run 3 Stations')
args = parser.parse_args()

# --- Format run/raw file numbers ---
run_str = args.run.zfill(6)
raw_str = args.rawfile.zfill(5)

# --- Build the arguments string for the .sh script ---
script_args = f"{args.year} {run_str} {raw_str} {args.fourst} {args.threest}"

# --- Condor submit file template ---
submit_content = f"""executable = runAlignment.sh
arguments = {script_args}
output = logs/job_$(Cluster)_$(Process).out
error  = logs/job_$(Cluster)_$(Process).err
log    = logs/job_$(Cluster)_$(Process).log
request_cpus = 1
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
+JobFlavour           = "longlunch"
#+AccountingGroup = "group_u_FASER.users" #Add when you have access to faser computing group
on_exit_remove          = (ExitBySignal == False) && (ExitCode == 0)
max_retries             = 3
requirements = (Machine =!= LastRemoteHost) && (OpSysAndVer =?= "AlmaLinux9")
queue
"""

# --- Save to file ---
submit_filename = "submit_unbiased.sub"
with open(submit_filename, "w") as f:
    f.write(submit_content)

print(f"Condor submit file '{submit_filename}' created.")
print(f"Submitting job with arguments: {script_args}")

# --- Submit the job to Condor ---
try:
    result = subprocess.run(["condor_submit", "-spool", submit_filename], check=True, capture_output=True, text=True)
    print("Condor submission successful.")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error submitting job to Condor:")
    print(e.stderr)