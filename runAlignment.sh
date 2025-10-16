#!/bin/bash

# Usage: ./runAlignment.sh <YEAR> <RUN> <FILE> <FOURST> <THREEST> <IT> <ALIGN_PATH>
YEAR=$1
RUN=$2
FILE=$3
FOURST=$4
THREEST=$5
IT_DIR=$6
ALIGN_PATH=$7
echo "Running with parameters:"
echo " Year: $YEAR"
echo " Run: $RUN"
echo " File: $FILE"
echo " FOURST: $FOURST"
echo " THREEST: $THREEST"
echo " Work: $IT_DIR"
echo " Align: $ALIGN_PATH"
echo ""

# Dir for condor to store logs
mkdir -p logs
echo "=== Create logs directory ==="

# Setup environment
cd /eos/home-s/shunlian/Alignment #Your Directory to Calypso
source env.sh
cd align/2.1raw2reco #Your Directory to runAlignment.sh
TEMP_DIR=$(pwd)
echo "=== Setup Environment ==="

# Create working directory
mkdir -p "$IT_DIR/1reco/$FILE"
cd "$IT_DIR/1reco/$FILE"
WORK_DIR=$(pwd)
cp $ALIGN_PATH $IT_DIR/1reco/inputforalign.txt
echo "=== Work directory for this job: $WORK_DIR ==="

# Setup poolcond path
export ATLAS_POOLCOND_PATH="$WORK_DIR/data"
export EOS_MGM_URL=root://eosuser.cern.ch
echo "=== Setup pool path ${ATLAS_POOLCOND_PATH} ==="

# Copy templates and database
cp $TEMP_DIR/templates/aligndb_copy.sh ./
cp $TEMP_DIR/templates/aligndb_template_head.sh ./
cp $TEMP_DIR/templates/aligndb_template_tail.sh ./
cp $TEMP_DIR/templates/WriteAlignment* ./
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
    CMD="python $TEMP_DIR/faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward --noIFT"
elif [ "$FOURST" = "True" ]; then
    CMD="python $TEMP_DIR/faser_reco_alignment.py \"$FILE_PATH\" --alignment --noBackward"
fi
echo "=== Running command: $CMD ==="
eval $CMD

# Move output files to kfalignment directory
mkdir -p ../../2kfalignment
mv Faser-Physics-*kfalignment.root "../../2kfalignment/kfalignment_${RUN}_${FILE}.root"
rm Faser-Physics-*-xAOD.root
echo "=== Finished alignment ==="