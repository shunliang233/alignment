#!/usr/bin/env python3
"""
Millepede workflow entry point — called from HTCondor DAGMan.

This script is executed by runMillepede.sh once per alignment iteration,
after all reco + kfalign Condor jobs for that iteration have finished.
By the time this script runs:
  - kfalign_dir (2kfalignment) already contains the binary output files
    produced by the tracking + Kalman-filter alignment jobs.
  - reco_dir/inputforalign.txt already exists (either the template initial
    file for iter 0, or the result copied from the previous iteration).

What this script does:
  1. Run 1convert  : convert kfalign binary output -> mp2input.bin
  2. Copy .txt files: copy steering / constraint files to work_dir
  3. Load params   : read the initial presigma file (mp2par_ss.txt)
  4. Run AlignmentSet: multiple PedeStep instances driven by config.workflow
  5. Generate DB   : 5.1PedetoDB_ss + 5.2add_param -> new inputforalign.txt
  6. Write output  : copy inputforalign.txt to iter root for next iteration

All runtime parameters are baked in by dag_manager.py at DAG generation time
and passed via runMillepede.sh — no config.json is read at execution time.

Usage (called by runMillepede.sh):
  python3 <src_dir>/Workflow/millepede.py \
      --input_dir <kfalign_dir> \
      --bin_dir   <src_dir>/millepede/bin \
      --tpl_dir   <src_dir>/templates \
      --steps     "IFT,210,410|IFT,200,220,300,310,320,400,420"
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# Allow importing Workflow-local modules
sys.path.insert(0, str(Path(__file__).parent))

from ParamIO import ParamIO
from Workflow.PedeAlg import PedeStep
from FixRule import FixRule
from BinAlg import BinAlg
from MergeAlg import MergeAlg

# ─────────────────────────────── Path helpers ──────────────────────────────

def work_paths(input_dir: Path) -> Tuple[Path, Path, Path, Path]:
    """Derive all working paths from the kfalign directory.

    Args:
        input_dir: Path to the kfalign output directory (2kfalignment).

    Returns:
        (work_dir, reco_dir, inputforalign_in, inputforalign_out)

        work_dir          - input_dir/../3millepede  (created if absent)
        reco_dir          - input_dir/../1reco
        inputforalign_in  - reco_dir/inputforalign.txt
        inputforalign_out - input_dir/../inputforalign.txt

    Raises:
        FileNotFoundError: If input_dir does not exist.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    iter_root         = (input_dir / '..').resolve()
    work_dir          = (iter_root / '3millepede').resolve()
    reco_dir          = (iter_root / '1reco').resolve()
    inputforalign_in  = reco_dir / 'inputforalign.txt'
    inputforalign_out = iter_root / 'inputforalign.txt'
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir, reco_dir, inputforalign_in, inputforalign_out


# ─────────────────────────────── Step helpers ──────────────────────────────

def parse_steps(steps_str: str) -> List[PedeStep]:
    """Parse the CLI steps string into a list of PedeStep instances.

    Format: pipe-separated steps, each step is comma-separated fix descriptors.
    Integer descriptors are parsed as int (component labels); others as str.
    Example: "IFT,210,410|IFT,200,220,300,310,320,400,420"

    Args:
        steps_str: Serialized steps string produced by dag_manager.py.

    Returns:
        Ordered list of PedeStep instances.
    """
    steps = []
    for step_str in steps_str.split('|'):
        items = []
        for token in step_str.split(','):
            token = token.strip()
            try:
                items.append(int(token))
            except ValueError:
                items.append(token)
        steps.append(PedeStep(FixRule(*items)))
    return steps


def run_convert(input_dir: Path, work_dir: Path, bin_dir: Path) -> None:
    """Run 1convert to produce mp2input.bin from kfalign output.

    Args:
        input_dir: kfalign output directory (source of binary track data).
        work_dir:  Millepede working directory (destination).
        bin_dir:   Directory containing the custom alignment binaries.
    """
    BinAlg(input_dir, work_dir, bin_dir).run()


def copy_txt_files(tpl_dir: Path, work_dir: Path) -> None:
    """Copy all .txt steering / constraint files from tpl_dir to work_dir.

    Args:
        tpl_dir:  Directory containing template text files
                  (mp2str_ss.txt, mp2con_ss.txt, mp2par_ss.txt, ...).
        work_dir: Millepede working directory.
    """
    for txt_file in tpl_dir.glob('*.txt'):
        dest = work_dir / txt_file.name
        shutil.copy2(txt_file, dest)


def generate_inputforalign(
        work_dir: Path,
        inputforalign_in: Path,
        inputforalign_out: Path,
        bin_dir: Path) -> None:
    """Convert millepede.res to the FASER DB inputforalign.txt format.

    Args:
        work_dir:          Millepede working directory.
        inputforalign_in:  Current inputforalign.txt (from reco_dir).
        inputforalign_out: Destination for the updated inputforalign.txt.
        bin_dir:           Directory containing 5.1PedetoDB_ss and 5.2add_param.
    """
    MergeAlg(work_dir, inputforalign_in, inputforalign_out, bin_dir).run()


# ───────────────────────────────── main ────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Millepede workflow entry point (called from DAGMan).',
    )
    parser.add_argument(
        '--input_dir', '-i', required=True,
        help='Path to kfalign output directory (2kfalignment)',
    )
    parser.add_argument(
        '--bin_dir', required=True,
        help='Directory containing 1convert, 5.1PedetoDB_ss, 5.2add_param',
    )
    parser.add_argument(
        '--tpl_dir', required=True,
        help='Templates directory containing *.txt steering/constraint files',
    )
    parser.add_argument(
        '--steps', required=True,
        help='Pipe-separated pede steps, e.g. "IFT,210,410|IFT,200,220"',
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    bin_dir   = Path(args.bin_dir).resolve()
    tpl_dir   = Path(args.tpl_dir).resolve()

    # ── Derive paths ────────────────────────────────────────────────────
    try:
        work_dir, reco_dir, inputforalign_in, inputforalign_out = \
            work_paths(input_dir)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    if not inputforalign_in.exists():
        print(f"Error: inputforalign.txt not found: {inputforalign_in}",
              file=sys.stderr)
        return 1

    # Pede executable is on PATH (runMillepede.sh exports env_pede to PATH).
    steering = work_dir / 'mp2str_ss.txt'

    # ── Step 1: convert kfalign output → mp2input.bin ───────────────────
    run_convert(input_dir, work_dir, bin_dir)

    # ── Step 2: copy steering / constraint .txt files to work_dir ───────
    copy_txt_files(tpl_dir, work_dir)

    # ── Step 3: load initial presigma parameters ────────────────────────
    mp2par_tpl = work_dir / 'mp2par_ss.txt'   # copied from templates/
    params = ParamIO(mp2par_tpl, mp2par_tpl)

    # ── Step 4: parse and run PedeAlg chain ─────────────────────────────
    try:
        rules = parse_steps(args.steps)
    except (TypeError, ValueError) as e:
        print(f"Steps parse error: {e}", file=sys.stderr)
        return 1

    n = len(rules)
    try:
        current = params
        for i, rule in enumerate(rules):
            print(f"[pede] step {i}/{n - 1} ...")
            current = PedeAlg(rule, work_dir, steering).run(current)
            if i < n - 1:
                (work_dir / 'millepede.res').rename(
                    work_dir / f'millepede.res.step{i:02d}')
    except subprocess.CalledProcessError as e:
        print(f"pede failed with exit code {e.returncode}", file=sys.stderr)
        return e.returncode

    # ── Step 5: generate new inputforalign.txt from millepede.res ────────
    try:
        generate_inputforalign(work_dir, inputforalign_in,
                               inputforalign_out, bin_dir)
    except subprocess.CalledProcessError as e:
        print(f"DB conversion failed: {e}", file=sys.stderr)
        return e.returncode

    print("Millepede processing completed successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
