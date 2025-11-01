#!/bin/bash

# Usage: ./runAlignment.sh <YEAR> <RUN> <FILE> <FOURST> <THREEST> <IT> <ALIGN_PATH>
YEAR=$1
RUN=$2
FILE=$3
FOURST=$4
THREEST=$5
RECO_DIR=$6
SRC_DIR=$7
ENV_PATH=$8
echo "Running with parameters:"
echo " Year: $YEAR"
echo " Run: $RUN"
echo " File: $FILE"
echo " FOURST: $FOURST"
echo " THREEST: $THREEST"
echo " RecoDir: $RECO_DIR"
echo " SrcDir: $SRC_DIR"
echo " EnvPath: $ENV_PATH"
echo ""

# Dir for condor to store logs
mkdir -p logs
echo "=== Create logs directory on execute node ==="

# Setup environment
source $ENV_PATH
echo "=== Sourced environment from $ENV_PATH ==="

# Create working directory
mkdir -p "$RECO_DIR/$RUN/$FILE"
cd "$RECO_DIR/$RUN/$FILE"
WORK_DIR=$(pwd)
echo "=== Work directory for this job: $WORK_DIR ==="

# Setup poolcond path
export ATLAS_POOLCOND_PATH="$WORK_DIR/data"
export EOS_MGM_URL=root://eosuser.cern.ch
echo "=== Setup pool path ${ATLAS_POOLCOND_PATH} ==="

# Copy templates and database
cp $SRC_DIR/templates/aligndb_copy.sh ./
cp $SRC_DIR/templates/aligndb_template_head.sh ./
cp $SRC_DIR/templates/aligndb_template_tail.sh ./
cp $SRC_DIR/templates/WriteAlignment* ./
rm -rf data
mkdir -p data/sqlite200
mkdir -p data/poolcond
cp /cvmfs/faser.cern.ch/repo/sw/database/DBRelease/current/sqlite200/ALLP200.db data/sqlite200
echo "=== Copied templates ==="

# Run aligndb_copy.sh
rm aligndb_copy.sh
touch aligndb_copy.sh
cat aligndb_template_head.sh >./aligndb_copy.sh
ALIGN_VAR=$(cat "$RECO_DIR/inputforalign.txt")
echo "python WriteAlignmentConfig_Faser04.py 'AlignDbTool.AlignmentConstants={$ALIGN_VAR}' >& writeAlignment_Faser04.log" >>./aligndb_copy.sh
cat aligndb_template_tail.sh >>./aligndb_copy.sh
chmod 755 ./aligndb_copy.sh
./aligndb_copy.sh >& aligndb_copy.log
echo "=== Finished aligndb_copy.sh ==="

# Build the command based on THREEST and FOURST flags
FILE_PATH="/eos/experiment/faser/raw/${YEAR}/${RUN}/Faser-Physics-${RUN}-${FILE}.raw"
if [ "$THREEST" = "True" ]; then
    CMD="python $SRC_DIR/faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward --noIFT"
elif [ "$FOURST" = "True" ]; then
    CMD="python $SRC_DIR/faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward"
fi
echo "=== Running command: $CMD ==="
eval $CMD

# Move output files to kfalignment directory
mv Faser-Physics-*kfalignment.root "$RECO_DIR/../2kfalignment/kfalignment_${RUN}_${FILE}.root"
rm Faser-Physics-*-xAOD.root
echo "=== Finished alignment ==="