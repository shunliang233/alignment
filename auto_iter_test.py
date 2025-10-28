import os
import re
import shutil
import argparse
import subprocess
import time
import sys
from datetime import datetime, timezone, timedelta
from RawList import RawList

# 设置标准输出无缓冲
sys.stdout.reconfigure(line_buffering=True)

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Iteration for FASER alignment.")

parser.add_argument('--remain', '--continue', '-c', action='store_true', default=False,
                    help='Continue remaining iteration.')
parser.add_argument('--year', '-y', type=str, required=True,
                    help='Year (e.g., 2022-2025)')
parser.add_argument('--run', '-r', type=str, required=True,
                    help='Run number (e.g., 011705, will be padded to 6 digits)')
parser.add_argument('--files', '-f', type=str, required=True,
                    help='Raw file number or range. Single file: 400; Range: 400-500 or 400:500')
parser.add_argument('--iterations', '-i', type=str, required=True,
                    help='Required iteration times (integer, required)')
parser.add_argument('--fourst', action='store_true', default=False,
                    help='Run 4 Stations')
parser.add_argument('--threest', action='store_true', default=True,
                    help='Run 3 Stations')
args = parser.parse_args()
# --- Format arguments  ---
year_str = args.year.zfill(4)
run_str = args.run.zfill(6)
try:
    file_list = RawList(args.files)
except ValueError as e:
    parser.error(str(e))
iter_int = int(args.iterations)
print(f"Processing ...")
print(f"\tYear: {year_str} Run: {run_str}, Files: {file_list}, Iterations: {iter_int}")

# --- Env Path ---
env_path = "/eos/home-s/shunlian/Alignment/env.sh"
if not os.path.isfile(env_path):
    raise FileNotFoundError(f"Environment script not found: {env_path}")

# --- Make work dir ---
main_str = f"Y{year_str}_R{run_str}_F{str(file_list)}"
src_dir = os.path.dirname(os.path.abspath(__file__))
main_dir = os.path.join(src_dir, main_str)
iter_str = "iter"
reco_str = "1reco"
kfalign_str = "2kfalignment"
pede_str = "3millepede"
exe_str = "runAlignment.sh"
exe_path = os.path.join(src_dir, exe_str)
input_str = "inputforalign.txt"
sub_str = "submit_unbiased.sub"
sub_tmp_path = os.path.join(src_dir, sub_str)
os.makedirs(main_dir, exist_ok=args.remain)
print(f"Main directory created at: {main_dir}")

for it in range(1, iter_int + 1):
    # 0. Work dir for this iteration
    print("\nStarting iteration: ", it)
    iter_dir = os.path.join(main_dir, f"{iter_str}{str(it).zfill(2)}")
    reco_dir = os.path.join(iter_dir, reco_str)
    kfalign_dir =  os.path.join(iter_dir, kfalign_str)
    pede_dir = os.path.join(iter_dir, pede_str)
    os.makedirs(reco_dir, exist_ok=True)
    os.makedirs(kfalign_dir, exist_ok=True)
    os.makedirs(pede_dir, exist_ok=True)
    
    # 1. reco
    os.chdir(reco_dir) # prepare files
    shutil.copy2(exe_path, reco_dir)
    input_path = os.path.join(reco_dir, input_str)
    if it == 1:
        open(input_path, "w").close()
    else:
        last_iter_str = f"{iter_str}{it-1:02d}"
        last_iter_dir = os.path.join(main_dir, last_iter_str)
        cp_path = os.path.join(last_iter_dir, input_str)
        try:
            shutil.copy2(cp_path, input_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Alignment file not found: {cp_path}")
    sub_path = shutil.copy2(sub_tmp_path, reco_dir)
    with open(sub_path, "a") as f:
        f.write("\n")
        for file_str in file_list:
            exe_args = f"{year_str} {run_str} {file_str} {args.fourst} {args.threest} {reco_dir} {src_dir} {env_path}"
            f.write(f"arguments = {exe_args}\nqueue\n\n")
    
    cluster_id = None # submit to condor
    try:
        result = subprocess.run(
            ["condor_submit", "-spool", sub_path],
            check=True,
            capture_output=True,
            text=True,
            stderr=subprocess.STDOUT
        )
        with open("condor.log", "w") as log_file:
            log_file.write(result.stdout)
        m = re.search(r"(\d+) job\(s\) submitted to cluster (\d+)\.", result.stdout)
        if m:
            job_count = int(m.group(1))
            cluster_id = int(m.group(2))
            print(f"Submitted {job_count} jobs to cluster {cluster_id}.")
        else:
            raise ValueError(f"Could not parse condor output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error: submitting job to Condor:\n{e.stderr}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if cluster_id is None: # monitor condor jobs
        print("Error: cluster_id not set")
        sys.exit(1)
    print(f"Monitoring cluster {cluster_id}...")
    while True:
        time.sleep(300)
        idle_str = subprocess.getoutput(f"condor_q {cluster_id} -idle")
        run_str = subprocess.getoutput(f"condor_q {cluster_id} -run")
        hold_str = subprocess.getoutput(f"condor_q {cluster_id} -hold")
        pattern = rf"{cluster_id}\.\d+"
        idle_count = len(re.findall(pattern, idle_str))
        run_count = len(re.findall(pattern, run_str))
        wait_count = idle_count + run_count
        hold_count = len(re.findall(pattern, hold_str))
        utc8_time = datetime.now(timezone(timedelta(hours=8)))
        time_str = f"Beijing Time: {utc8_time.strftime('%Y-%m-%d %H:%M:%S')}"
        if hold_count == 0 and wait_count == 0:
            print(f"{time_str} Finished: All jobs completed successfully.")
            break
        elif hold_count != 0 and wait_count == 0:
            print(f"{time_str} Warning Finished: {hold_count} jobs hold.")
            break
        elif hold_count == 0 and wait_count != 0:
            print(f"{time_str} Info: {wait_count} jobs running.")
        elif hold_count != 0 and wait_count != 0:
            print(f"{time_str} Warning: {hold_count} jobs hold.")
    if hold_count != 0:
        print("Error: Some jobs are on hold.")
        sys.exit(1)
    
    # 3. millepede
    os.chdir(pede_dir)
    # subprocess.run([exe_path, "millepede", input_str, output_str], check=True)

    # 4. 合并50个输出文件
    subprocess.run(f"cat outputs_{it}/output_* > merged_{it}.txt", shell=True)  # 举例
    # 5. 用 merged_{it}.txt 生成下一轮参数