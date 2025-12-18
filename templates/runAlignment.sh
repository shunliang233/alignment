#!/bin/bash

# Usage: ./runAlignment.sh <YEAR> <RUN> <STATIONS> <FILE> <RECO_DIR> <KFALIGN_DIR> <SRC_DIR> <CALYPSO_ASETUP> <CALYPSO_SETUP>
YEAR=$1
RUN=$2
STATIONS=$3
FILE=$4
RECO_DIR=$5
KFALIGN_DIR=$6
SRC_DIR=$7
CALYPSO_ASETUP=$8
CALYPSO_SETUP=$9
echo "Running with parameters:"
echo " Year: $YEAR"
echo " Run: $RUN"
echo " Stations: $STATIONS"
echo " File: $FILE"
echo " RecoDir: $RECO_DIR"
echo " KFAlignDir: $KFALIGN_DIR"
echo " SrcDir: $SRC_DIR"
echo " CalypsoAsetup: $CALYPSO_ASETUP"
echo " CalypsoSetup: $CALYPSO_SETUP"
echo ""

# Dir for condor to store logs
mkdir -p logs
echo "=== Create logs directory on execute node ==="

# Setup environment
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase 
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
asetup --input=$CALYPSO_ASETUP Athena,24.0.41
source $CALYPSO_SETUP
echo "=== Sourced environment from ==="

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

# Build the command based on number of stations
FILE_PATH="/eos/experiment/faser/raw/${YEAR}/${RUN}/Faser-Physics-${RUN}-${FILE}.raw"
if [ "$STATIONS" = "3" ]; then
    CMD="python $SRC_DIR/faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward --noIFT"
elif [ "$STATIONS" = "4" ]; then
    CMD="python $SRC_DIR/faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward"
else
    echo "Error: STATIONS must be 3 or 4, got: $STATIONS"
    exit 1
fi
echo "=== Running command: $CMD ==="
eval $CMD

# Copy output files from execute node to final destination
# Create output directory if it doesn't exist
mkdir -p "$KFALIGN_DIR"

# Copy the kfalignment root file to the final destination
cp Faser-Physics-*kfalignment.root "$KFALIGN_DIR/kfalignment_${RUN}_${FILE}.root"
echo "=== Copied output file to $KFALIGN_DIR/kfalignment_${RUN}_${FILE}.root ==="

# Remove xAOD file (not needed)
rm -f Faser-Physics-*-xAOD.root

# Cleanup: Remove working directory on execute node
# This happens automatically when HTCondor cleans up, but we can do it explicitly
cd /tmp
rm -rf "$WORK_DIR"
echo "=== Cleaned up working directory on execute node ==="

echo "=== Finished alignment ==="