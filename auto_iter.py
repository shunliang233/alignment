import os
import re
import shutil
import argparse
import subprocess
import time
import sys
from datetime import datetime, timezone, timedelta
from RawList import RawList

# source /eos/home-s/shunlian/Alignment/py_env.sh
# nohup python3 auto_iter.py -y 2023 -r 011705 -f 450-500 -i 10 &>>auto_iter.log &

# 设置标准输出无缓冲
sys.stdout.reconfigure(line_buffering=True)

# Some Absolute Paths temporarily for convenience
env_path = "/eos/home-s/shunlian/Alignment/env.sh" # Environment for faser_reco_alignment.py

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

# --- 检查日志文件，决定是否断点续跑 ---
resume_it = 1
resume_cluster = None
log_path = "./auto_iter.log"
if args.remain and os.path.exists(log_path) and os.path.getsize(log_path) != 0:
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    # 找到最后一个以"Starting iteration:"开头的行的索引
    start_idx = None
    for idx in range(len(lines)-1, -1, -1):
        if lines[idx].strip().startswith("Starting iteration:"):
            start_idx = idx
            break
    if start_idx is not None and start_idx+1 < len(lines):
        # 下一行应包含 iter 和 cluster
        next_line = lines[start_idx+1]
        m = re.search(r"iter: (\d+), cluster: (\d+), jobs: (\d+).", next_line)
        if m:
            resume_it = int(m.group(1))
            resume_cluster = int(m.group(2))
            resume_jobs = int(m.group(3))
            print(f"\n[RESUME] iter: {resume_it}, cluster: {resume_cluster}, jobs: {resume_jobs} ...")
        else:
            resume_it = 1
            resume_cluster = None
    else:
        resume_it = 1
        resume_cluster = None
else:
    resume_it = 1
    resume_cluster = None

# 记录进程 ID
print(f"Process ID: {os.getpid()}")

# --- Format arguments  ---
year_str = args.year.zfill(4)
run_str = args.run.zfill(6)
try:
    file_list = RawList(args.files)
except ValueError as e:
    parser.error(str(e))
iter_int = int(args.iterations)
print(f"Year: {year_str} Run: {run_str}, Files: {file_list}, Iterations: {iter_int}")

# --- Env Path ---
if not os.path.isfile(env_path):
    raise FileNotFoundError(f"Environment script not found: {env_path}")

# --- Make work dir ---
main_str = f"Y{year_str}_R{run_str}_F{str(file_list)}"
src_dir = os.path.dirname(os.path.abspath(__file__))
main_dir = os.path.join(src_dir, main_str)
iter_str = "iter"
reco_str = "1reco"
kfalign_str = "2kfalignment"
millepede_str = "3millepede"
mille_str = "millepede"
mille_path = os.path.join(src_dir, mille_str, "bin", f"{mille_str}.py")
exe_str = "runAlignment.sh"
exe_path = os.path.join(src_dir, exe_str)
input_str = "inputforalign.txt"
sub_str = "submit_unbiased.sub"
sub_tmp_path = os.path.join(src_dir, sub_str)
os.makedirs(main_dir, exist_ok=args.remain)
print(f"Main directory created at: {main_dir}")

# --- Iterations ---
for it in range(1, iter_int + 1):
    
    # Skip already completed iterations
    if it < resume_it:
        continue
    
    # Start a new iteration
    elif it > resume_it or it == resume_it and resume_cluster is None:
        # 0. Work dir for this iteration
        print("\nStarting iteration:")
        iter_dir = os.path.join(main_dir, f"{iter_str}{str(it).zfill(2)}")
        reco_dir = os.path.join(iter_dir, reco_str)
        kfalign_dir =  os.path.join(iter_dir, kfalign_str)
        millepede_dir = os.path.join(iter_dir, millepede_str)
        os.makedirs(reco_dir, exist_ok=True)
        os.makedirs(kfalign_dir, exist_ok=True)
        os.makedirs(millepede_dir, exist_ok=True)

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
                text=True
            )
            with open("condor.log", "w") as log_file:
                log_file.write(result.stdout)
            m = re.search(r"(\d+) job\(s\) submitted to cluster (\d+)\.", result.stdout)
            if m:
                job_count = int(m.group(1))
                cluster_id = int(m.group(2))
                print(f"\titer: {it}, cluster: {cluster_id}, jobs: {job_count}.")
            else:
                raise ValueError(f"Could not parse condor output:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Error: submitting job to Condor:\n{e.stderr}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # 断点运行前置设置
    elif it == resume_it and resume_cluster is not None:
        cluster_id = resume_cluster
        job_count = resume_jobs
        resume_cluster = None  # 只用一次
        resume_jobs = None  # 只用一次
        # 0. Work dir for this iteration
        print("\nStarting iteration:")
        print(f"\titer: {it}, cluster: {cluster_id}, jobs: {job_count}.")
        iter_dir = os.path.join(main_dir, f"{iter_str}{str(it).zfill(2)}")
        reco_dir = os.path.join(iter_dir, reco_str)
        kfalign_dir =  os.path.join(iter_dir, kfalign_str)
        millepede_dir = os.path.join(iter_dir, millepede_str)
        os.makedirs(reco_dir, exist_ok=True)
        os.makedirs(kfalign_dir, exist_ok=True)
        os.makedirs(millepede_dir, exist_ok=True)
    
    # Suitable for both new and resuming
    if cluster_id is None: # monitor condor jobs
        print("Error: cluster_id not set")
        sys.exit(1)
    print(f"Monitoring ...")
    while True:
        time.sleep(300)
        utc8_time = datetime.now(timezone(timedelta(hours=8)))
        time_str = f"Beijing Time: {utc8_time.strftime('%Y-%m-%d %H:%M:%S')}"
        idle_res = subprocess.run(["condor_q", str(cluster_id), "-idle"], capture_output=True, text=True)
        idle_stat = idle_res.stdout
        idle_err = idle_res.stderr
        idle_code = idle_res.returncode
        work_res = subprocess.run(["condor_q", str(cluster_id), "-run"], capture_output=True, text=True)
        work_stat = work_res.stdout
        work_err = work_res.stderr
        work_code = work_res.returncode
        hold_res = subprocess.run(["condor_q", str(cluster_id), "-hold"], capture_output=True, text=True)
        hold_stat = hold_res.stdout
        hold_err = hold_res.stderr
        hold_code = hold_res.returncode
        if idle_code != 0 or work_code != 0 or hold_code != 0:
            print(f"{time_str} Warning: condor_q failed:")
            print(f"\tidle={idle_code}, work={work_code}, hold={hold_code}")
            print(f"\tidle_err: {idle_err}")
            continue
        pattern = rf"{cluster_id}\.\d+"
        idle_count = len(re.findall(pattern, idle_stat))
        work_count = len(re.findall(pattern, work_stat))
        wait_count = idle_count + work_count
        hold_count = len(re.findall(pattern, hold_stat))
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
    os.chdir(millepede_dir)
    try:
        result = subprocess.run(
            ["python3", mille_path, "-i", kfalign_dir],
            check=True,
            capture_output=True,
            text=True
        )
        with open("mymille.log", "w") as log_file:
            log_file.write(result.stdout)
        print("Millepede completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Millepede failed:\n{e.stdout}")
        sys.exit(1)