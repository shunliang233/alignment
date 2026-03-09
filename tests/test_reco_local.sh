#!/bin/bash
# ---------------------------------------------------------------------------
# Local reconstruction smoke-test for faser_reco_alignment.py
#
# Purpose:
#   Run a single-event reconstruction on ONE raw file and verify that the
#   expected output files are produced.  Use this before submitting the full
#   alignment workflow to HTCondor.
#
#   Mirrors the environment setup and alignment-DB steps from runAlignment.sh.
#
# Usage:
#   bash tests/test_reco_local.sh [--config <path>] [--nevents <N>] [--file <FILE>]
#
# Options:
#   --config   Path to config.json  (default: config.json next to this repo)
#   --nevents  Events to process    (default: 1  – minimal smoke-test)
#   --file     Raw file index, zero-padded to 5 digits  (default: 00100)
#
# Exit codes:
#   0  all checks passed
#   1  a check failed
# ---------------------------------------------------------------------------
# set -uo pipefail

# ---- locate repo root -------------------------------------------------------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )"

# ---- defaults ---------------------------------------------------------------
CONFIG_FILE="${ROOT_DIR}/config.json"
NEVENTS=1
FILE_IDX="00100"

# ---- argument parsing -------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)   CONFIG_FILE="$2"; shift 2 ;;
        --nevents)  NEVENTS="$2";     shift 2 ;;
        --file)     FILE_IDX="$2";    shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "==========================================="
echo "  FASER Reco Local Smoke-Test"
echo "==========================================="
echo "  Config  : ${CONFIG_FILE}"
echo "  Events  : ${NEVENTS}"
echo "  File    : ${FILE_IDX}"
echo ""

# ---- read all needed fields from config.json --------------------------------
eval "$(python3 - "${CONFIG_FILE}" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1]))
raw = cfg["raw"]
env = cfg["env"]
tpl = cfg["tpl"]
src = cfg["src"]
data = cfg["data"]
fmt = raw["format"].format(
    year=str(raw["year"]).zfill(4),
    run=str(raw["run"]).zfill(6),
    files=raw["files"],
    stations=raw["stations"]
)
tpl_dir = tpl["dir"]
iter00_reco = (data["dir"].format(format=fmt)
               + "/" + data["iter"]["dir"].format(iter="00")
               + "/" + data["iter"]["reco"])
print(f'YEAR={raw["year"]}')
print(f'RUN={str(raw["run"]).zfill(6)}')
print(f'STATIONS={raw["stations"]}')
print(f'VERBOSITY={raw.get("verbosity","INFO")}')
print(f'CALYPSO_ASETUP={env["calypso"]["asetup"]}')
print(f'CALYPSO_SETUP={env["calypso"]["setup"]}')
print(f'SRC_DIR={src["dir"]}')
print(f'TPL_DIR={tpl_dir}')
print(f'TPL_INPUTFORALIGN={tpl_dir}/{tpl["inputforalign"]}')
print(f'ITER00_RECO_DIR={iter00_reco}')
PYEOF
)"

echo "  Year           : ${YEAR}"
echo "  Run            : ${RUN}"
echo "  Stations       : ${STATIONS}"
echo "  Verbosity      : ${VERBOSITY}"
echo "  CalypsoAsetup  : ${CALYPSO_ASETUP}"
echo "  CalypsoSetup   : ${CALYPSO_SETUP}"
echo ""

FILE_PATH="/eos/experiment/faser/raw/${YEAR}/${RUN}/Faser-Physics-${RUN}-${FILE_IDX}.raw"

# ---- pre-flight checks ------------------------------------------------------
echo "--- Pre-flight checks ---"

if [ ! -f "${FILE_PATH}" ]; then
    echo "FAIL: Raw file not found: ${FILE_PATH}"
    exit 1
fi
echo "OK  : Raw file exists: ${FILE_PATH}"

if [ ! -f "${CALYPSO_ASETUP}" ]; then
    echo "FAIL: Calypso asetup file not found: ${CALYPSO_ASETUP}"
    exit 1
fi
echo "OK  : Calypso asetup found"

if [ ! -f "${CALYPSO_SETUP}" ]; then
    echo "FAIL: Calypso setup script not found: ${CALYPSO_SETUP}"
    exit 1
fi
echo "OK  : Calypso setup script found"

# Choose inputforalign.txt: prefer iter00 (real constants), fall back to template
INPUTFORALIGN_SRC=""
if [ -f "${ITER00_RECO_DIR}/inputforalign.txt" ]; then
    INPUTFORALIGN_SRC="${ITER00_RECO_DIR}/inputforalign.txt"
    echo "OK  : Using iter00 inputforalign: ${INPUTFORALIGN_SRC}"
elif [ -f "${TPL_INPUTFORALIGN}" ]; then
    INPUTFORALIGN_SRC="${TPL_INPUTFORALIGN}"
    echo "OK  : Using template inputforalign: ${INPUTFORALIGN_SRC}"
else
    echo "FAIL: No inputforalign.txt found (iter00 reco dir or template)"
    exit 1
fi
echo ""

# ---- create isolated working directory --------------------------------------
WORK_DIR=$(mktemp -d)
cleanup() {
    echo ""
    echo "--- Cleaning up work dir: ${WORK_DIR} ---"
    rm -rf "${WORK_DIR}"
}
trap cleanup EXIT

cd "${WORK_DIR}"
echo "--- Work directory: ${WORK_DIR} ---"
echo ""

# ---- environment setup (mirrors runAlignment.sh) ----------------------------
echo "--- Setting up ATLAS environment ---"
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source "${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh"
asetup --input="${CALYPSO_ASETUP}" Athena,24.0.41
source "${CALYPSO_SETUP}"
echo "=== Sourced environment ==="

# ---- pool conditions and EOS (mirrors runAlignment.sh) ----------------------
export ATLAS_POOLCOND_PATH="${WORK_DIR}/data"
export EOS_MGM_URL=root://eosuser.cern.ch
echo "=== Setup pool path ${ATLAS_POOLCOND_PATH} ==="

# ---- copy templates and database (mirrors runAlignment.sh) ------------------
mkdir -p logs
cp "${SRC_DIR}/templates/aligndb_copy.sh" ./
cp "${SRC_DIR}/templates/aligndb_template_head.sh" ./
cp "${SRC_DIR}/templates/aligndb_template_tail.sh" ./
cp "${SRC_DIR}/templates/WriteAlignment"* ./
rm -rf data
mkdir -p data/sqlite200
mkdir -p data/poolcond
cp /cvmfs/faser.cern.ch/repo/sw/database/DBRelease/current/sqlite200/ALLP200.db data/sqlite200
echo "=== Copied templates and database ==="

# ---- build aligndb_copy.sh (mirrors runAlignment.sh) ------------------------
rm aligndb_copy.sh
touch aligndb_copy.sh
cat aligndb_template_head.sh > ./aligndb_copy.sh
ALIGN_VAR=$(cat "${INPUTFORALIGN_SRC}")
echo "python WriteAlignmentConfig_Faser04.py 'AlignDbTool.AlignmentConstants={${ALIGN_VAR}}' >& writeAlignment_Faser04.log" >> ./aligndb_copy.sh
cat aligndb_template_tail.sh >> ./aligndb_copy.sh
chmod 755 ./aligndb_copy.sh
./aligndb_copy.sh >& aligndb_copy.log
echo "=== Finished aligndb_copy.sh ==="

# ---- build reconstruction command (mirrors runAlignment.sh) -----------------
VERBOSITY_UPPER=$(echo "${VERBOSITY}" | tr '[:lower:]' '[:upper:]')
RECO_SCRIPT="${SRC_DIR}/faser_reco_alignment.py"

if [ "${STATIONS}" = "3" ]; then
    CMD="python \"${RECO_SCRIPT}\" \"${FILE_PATH}\" --alignment --noBackward --noIFT --nevents ${NEVENTS} --output_level ${VERBOSITY_UPPER}"
elif [ "${STATIONS}" = "4" ]; then
    CMD="python \"${RECO_SCRIPT}\" \"${FILE_PATH}\" --alignment --noBackward --nevents ${NEVENTS} --output_level ${VERBOSITY_UPPER}"
else
    echo "FAIL: raw.stations must be 3 or 4, got: ${STATIONS}"
    exit 1
fi

echo ""
echo "--- Running: ${CMD} ---"
echo ""
eval "${CMD}"
RECO_RC=$?

echo ""
if [ ${RECO_RC} -ne 0 ]; then
    echo "FAIL: Reconstruction exited with code ${RECO_RC}"
    exit 1
fi
echo "OK  : Reconstruction completed (exit 0)"

# ---- verify expected outputs ------------------------------------------------
echo ""
echo "--- Checking output files ---"

KFALIGN_FILE=$(ls Faser-Physics-*kfalignment.root 2>/dev/null | head -1)
if [ -z "${KFALIGN_FILE}" ]; then
    echo "FAIL: No *kfalignment.root output file found"
    exit 1
fi
echo "OK  : KF alignment output: ${KFALIGN_FILE}"

XAOD_FILE=$(ls Faser-Physics-*-xAOD.root 2>/dev/null | head -1)
if [ -z "${XAOD_FILE}" ]; then
    echo "FAIL: No *-xAOD.root output file found"
    exit 1
fi
echo "OK  : xAOD output        : ${XAOD_FILE}"

echo ""
echo "==========================================="
echo "  Smoke-test PASSED"
echo "==========================================="
