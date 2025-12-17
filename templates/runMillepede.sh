#!/bin/bash
TO_NEXT_ITER=$1
SRC_DIR=$2
KFALIGN_DIR=$3
    
# Check if we need the next iteration directory
if [ "${TO_NEXT_ITER}" = "True" ]; then
    NEXT_RECO_DIR=$4
    ENV_PEDE=$5
    ENV_ROOT=$6
else
    # Skip the 4th parameter (empty NEXT_RECO_DIR)
    ENV_PEDE=$4
    ENV_ROOT=$5
fi

set -e

echo "Setting up environment..."
export PATH="$ENV_PEDE:$PATH" # millipede2 directory
source $ENV_ROOT

echo "Running Millepede..."
python3 ${SRC_DIR}/millepede/bin/millepede.py -i ${KFALIGN_DIR}

echo "Millepede completed successfully."

if [ "${TO_NEXT_ITER}" = "True" ]; then
    echo "Transferring alignment constants to next iteration..."
    cp ${KFALIGN_DIR}/../inputforalign.txt ${NEXT_RECO_DIR}
    echo "Alignment constants transferred successfully."
fi