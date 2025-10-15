#!/bin/bash

# Usage: ./runAlignment.sh <YEAR> <RUN> <FILE> <FOURST> <THREEST> <IT> <ALIGN_PATH>
YEAR=$1
RUN=$2
FILE=$3
FOURST=$4
THREEST=$5
IT=$6
ALIGN_PATH=$7
echo "Running with parameters:"
echo " Year: $YEAR"
echo " Run: $RUN"
echo " File: $FILE"
echo " FOURST: $FOURST"
echo " THREEST: $THREEST"
echo " Iteration: $IT"
echo " Align: $ALIGN_PATH"
echo ""

# Dir for condor to store logs
mkdir -p logs${IT}
echo "=== Create logs directory ==="

# Setup environment
cd /eos/home-s/shunlian/Alignment #Your Directory to Calypso
source env.sh
echo "=== Setup Environment ==="

# Create working directory
cd align/2.1raw2reco #Your Directory to runAlignment.sh
RUN_DIR="${RUN}-${IT}"
mkdir -p "$RUN_DIR/$FILE"
cd "$RUN_DIR/$FILE"
WORK_DIR=$(pwd)
echo "=== Work directory: $WORK_DIR ==="

# Setup poolcond path
export ATLAS_POOLCOND_PATH="$WORK_DIR/data"
export EOS_MGM_URL=root://eosuser.cern.ch
echo "=== Setup pool path ${ATLAS_POOLCOND_PATH} ==="

# Copy templates and database
cp ../../../templates/aligndb_copy.sh ./
cp ../../../templates/aligndb_template_head.sh ./
cp ../../../templates/aligndb_template_tail.sh ./
cp ../../../templates/WriteAlignment* ./
rm -rf data
mkdir -p data/sqlite200
mkdir -p data/poolcond
cp /cvmfs/faser.cern.ch/repo/sw/database/DBRelease/current/sqlite200/ALLP200.db data/sqlite200
echo "=== Copied templates ==="

# Run aligndb_copy.sh
rm aligndb_copy.sh
touch aligndb_copy.sh
cat aligndb_template_head.sh >./aligndb_copy.sh
ALIGN_VAR=$(cat $ALIGN_PATH)
echo "python WriteAlignmentConfig_Faser04.py 'AlignDbTool.AlignmentConstants={$ALIGN_VAR}' >& writeAlignment_Faser04.log" >>./aligndb_copy.sh
cat aligndb_template_tail.sh >>./aligndb_copy.sh
chmod 755 ./aligndb_copy.sh
./aligndb_copy.sh >& aligndb_copy.log
echo "=== Finished aligndb_copy.sh ==="

# Build the command based on THREEST and FOURST flags
FILE_PATH="/eos/experiment/faser/raw/${YEAR}/${RUN}/Faser-Physics-${RUN}-${FILE}.raw"
if [ "$THREEST" = "True" ]; then
    CMD="python ../../faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward --noIFT"
elif [ "$FOURST" = "True" ]; then
    CMD="python ../../faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward"
fi
echo "=== Running command: $CMD ==="
eval $CMD

# Move output files to kfalignment directory
mkdir -p ../../kfalignment${IT}
mv Faser-Physics-*kfalignment.root "../../kfalignment${IT}/kfalignment_${RUN}_${FILE}.root"
rm Faser-Physics-*-xAOD.root
echo "=== Finished alignment ==="