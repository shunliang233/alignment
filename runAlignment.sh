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

# Create working directory on HTCondor execute node (local disk, not AFS)
# Use $_CONDOR_SCRATCH_DIR if available, otherwise use /tmp
if [ -n "$_CONDOR_SCRATCH_DIR" ]; then
    WORK_DIR="$_CONDOR_SCRATCH_DIR/work_${RUN}_${FILE}"
else
    WORK_DIR="/tmp/faser_align_${RUN}_${FILE}_$$"
fi
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
echo "=== Work directory for this job (on execute node): $WORK_DIR ==="

# Setup poolcond path
export ATLAS_POOLCOND_PATH="$WORK_DIR/data"
export EOS_MGM_URL=root://eosuser.cern.ch
echo "=== Setup pool path ${ATLAS_POOLCOND_PATH} ==="

# Copy templates and database to local execute node
cp $SRC_DIR/templates/aligndb_copy.sh ./
cp $SRC_DIR/templates/aligndb_template_head.sh ./
cp $SRC_DIR/templates/aligndb_template_tail.sh ./
cp $SRC_DIR/templates/WriteAlignment* ./
rm -rf data
mkdir -p data/sqlite200
mkdir -p data/poolcond
cp /cvmfs/faser.cern.ch/repo/sw/database/DBRelease/current/sqlite200/ALLP200.db data/sqlite200
echo "=== Copied templates and database to execute node ==="

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

# Copy output files from execute node to final destination
# Create output directory if it doesn't exist
mkdir -p "$RECO_DIR/../2kfalignment"

# Copy the kfalignment root file to the final destination
cp Faser-Physics-*kfalignment.root "$RECO_DIR/../2kfalignment/kfalignment_${RUN}_${FILE}.root"
echo "=== Copied output file to $RECO_DIR/../2kfalignment/kfalignment_${RUN}_${FILE}.root ==="

# Remove xAOD file (not needed)
rm -f Faser-Physics-*-xAOD.root

# Cleanup: Remove working directory on execute node
# This happens automatically when HTCondor cleans up, but we can do it explicitly
cd /tmp
rm -rf "$WORK_DIR"
echo "=== Cleaned up working directory on execute node ==="

echo "=== Finished alignment ==="