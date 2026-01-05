#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import shutil
import glob
from typing import Tuple

# Set by CMake configure_file
BIN_DIR = "@MILLEPEDE_BIN_DIR@"
TXT_DIR = "@MILLEPEDE_TXT_DIR@"

def work_paths(input_dir: str) -> Tuple[str, str]:
    """解析并准备路径。
    参数:
        input_dir: 输入目录路径
    返回:
        (work_dir, output_path)
        work_dir: input_dir/../3millepede 的绝对路径（目录会被创建）
        output_path: input_dir/../inputforalign.txt 的绝对路径
    如果 input_dir 不存在，抛出 FileNotFoundError。
    """
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    work_dir = os.path.realpath(os.path.join(input_dir, '..', '3millepede'))
    os.makedirs(work_dir, exist_ok=True)
    output_path = os.path.realpath(os.path.join(input_dir, '..', 'inputforalign.txt'))
    return work_dir, output_path

def process_chain(input_dir: str, work_dir: str, output_path: str):
    """执行 millepede 处理链的各个步骤。
    参数:
        input_dir: 输入目录路径
        work_dir: 工作目录路径
        output_path: 输出文件路径
    """
    # 拷贝 TXT_DIR 中的所有 .txt 文件到 work_dir
    txt_files = glob.glob(os.path.join(TXT_DIR, "*.txt"))
    for txt_file in txt_files:
        dest = os.path.join(work_dir, os.path.basename(txt_file))
        shutil.copy2(txt_file, dest)
        # print(f"Copied: {txt_file} -> {dest}")
    
    commands = [
        f"{os.path.join(BIN_DIR, '1convert')} -i {input_dir} -o {work_dir}/mp2input",
        f"pede mp2str-noIFT-2layersfixed_v2_ss.txt",
        f"{os.path.join(BIN_DIR, '3fixanotherlayers')} <./millepede.res >./Fixanotherlayers.txt",
        f"pede mp2str-noIFT-anotherlayersfixed_v2_ss.txt",
        f"cp ../1reco/inputforalign.txt ./inputforalign_temp.txt",
        f"{os.path.join(BIN_DIR, '5.1PedetoDB_ss')} <./millepede.res >>./inputforalign_temp.txt",
        f"{os.path.join(BIN_DIR, '5.2add_param')} <./inputforalign_temp.txt >./inputforalign_new.txt",
        f"cp ./inputforalign_new.txt ../inputforalign.txt"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=True, cwd=work_dir, 
                                  capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}: {cmd}", file=sys.stderr)
            if e.stderr:
                print(f"Error output: {e.stderr}", file=sys.stderr)
            sys.exit(e.returncode)
    print("Millepede processing completed successfully.")

if __name__ == '__main__':
    # argument parser
    parser = argparse.ArgumentParser(description='Millepede Chain.')
    parser.add_argument('--input_dir', '-i', type=str,
                        required=True, help='Path to input directory')
    args = parser.parse_args()
    input_dir = os.path.realpath(args.input_dir)
    try:
        work_dir, output_path = work_paths(input_dir)
    except FileNotFoundError as e:
        parser.error(str(e))
    
    # Execute the chain of commands
    process_chain(input_dir, work_dir, output_path)
