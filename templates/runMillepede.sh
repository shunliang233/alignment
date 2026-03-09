#!/bin/bash
# Arguments (fixed positions, baked in by dag_manager.py at submit time):
#   $1  TO_NEXT_ITER   - "True" / "False"
#   $2  KFALIGN_DIR    - path to 2kfalignment output directory
#   $3  NEXT_RECO_DIR  - path to next iter's 1reco dir (empty string if last iter)
#   $4  ENV_PEDE       - directory prepended to PATH for the pede executable
#   $5  ENV_ROOT       - ROOT setup script to source
#   $6  SRC_DIR        - alignment source directory (for locating millepede.py)
#   $7  BIN_DIR        - directory containing 1convert, 5.1PedetoDB_ss, 5.2add_param
#   $8  TPL_DIR        - templates directory (*.txt steering/constraint files)
#   $9  STEPS          - pipe-separated pede steps, e.g. "IFT,210,410|IFT,200,220"
TO_NEXT_ITER=$1
KFALIGN_DIR=$2
NEXT_RECO_DIR=$3
ENV_PEDE=$4
ENV_ROOT=$5
SRC_DIR=$6
BIN_DIR=$7
TPL_DIR=$8
STEPS=$9

set -e

echo "Setting up environment..."
export PATH="$ENV_PEDE:$PATH"
source $ENV_ROOT

echo "Running Millepede..."
python3 ${SRC_DIR}/Workflow/millepede.py \
    --input_dir ${KFALIGN_DIR} \
    --bin_dir   ${BIN_DIR} \
    --tpl_dir   ${TPL_DIR} \
    --steps     "${STEPS}"

echo "Millepede completed successfully."

if [ "${TO_NEXT_ITER}" = "True" ]; then
    echo "Transferring alignment constants to next iteration..."
    cp ${KFALIGN_DIR}/../inputforalign.txt ${NEXT_RECO_DIR}
    echo "Alignment constants transferred successfully."
fi