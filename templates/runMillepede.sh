#!/bin/bash
TO_NEXT_ITER=$1
ENV_PATH=$2
SRC_DIR=$3
KFALIGN_DIR=$4
NEXT_RECO_DIR=$5

set -e

echo "Setting up environment..."
source ${ENV_PATH}

echo "Running Millepede..."
python3 ${SRC_DIR}/millepede/bin/millepede.py -i ${KFALIGN_DIR}

echo "Millepede completed successfully."

if [ "${TO_NEXT_ITER}" = "True" ]; then
    echo "Transferring alignment constants to next iteration..."
    cp ${KFALIGN_DIR}/../inputforalign.txt ${NEXT_RECO_DIR}
    echo "Alignment constants transferred successfully."
fi