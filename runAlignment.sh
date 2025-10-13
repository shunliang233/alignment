#!/bin/bash
YEAR=$1
RUN=$2
RAW_FILE=$3
FOURST=$4
THREEST=$5

echo "Running with parameters:"
echo " Year: $YEAR"
echo " Run: $RUN"
echo " Raw file: $RAW_FILE"
echo ""

cd /eos/home-s/shunlian/Alignment #Your Directory to Calypso
source env.sh


echo "=== Setup Environment ==="
export ATLAS_POOLCOND_PATH="/eos/home-s/shunlian/Alignment/align/$RUN/$RAW_FILE/data"
echo "pool path ${ATLAS_POOLCOND_PATH}"
export EOS_MGM_URL=root://eosuser.cern.ch

cd align
RUN_SUFFIX="${RUN}"
mkdir -p "$RUN_SUFFIX/$RAW_FILE"
cd "$RUN_SUFFIX/$RAW_FILE"
echo ""


echo "=== Starting alignment ==="

cp ../../templates/aligndb_copy.sh ./
cp ../../templates/aligndb_template_head.sh ./
cp ../../templates/aligndb_template_tail.sh ./
cp ../../templates/WriteAlignment* ./
cp ../../templates/inputforalign.txt ./

rm -rf data
mkdir -p data/sqlite200
mkdir -p data/poolcond
cp /cvmfs/faser.cern.ch/repo/sw/database/DBRelease/current/sqlite200/ALLP200.db data/sqlite200

rm aligndb_copy.sh
touch aligndb_copy.sh
cat aligndb_template_head.sh >./aligndb_copy.sh
echo "python WriteAlignmentConfig_Faser04.py 'AlignDbTool.AlignmentConstants={$(cat inputforalign.txt)}' >& writeAlignment_Faser04.log" >>./aligndb_copy.sh
cat aligndb_template_tail.sh >>./aligndb_copy.sh
chmod 755 ./aligndb_copy.sh
./aligndb_copy.sh >& aligndb_copy.log

RAW_FILE_PATH="/eos/experiment/faser/raw/${YEAR}/${RUN}/Faser-Physics-${RUN}-${RAW_FILE}.raw"

# Build the command based on THREEST and FOURST flags
if [ "$THREEST" = "True" ]; then
    CMD="python ../../faser_reco_alignment.py \"$RAW_FILE_PATH\" --alignment --noBackward --noIFT"
elif [ "$FOURST" = "True" ]; then
    CMD="python ../../faser_reco_alignment.py \"$RAW_FILE_PATH\" --alignment --noBackward"
fi

# Run the final command
echo "Running command: $CMD"
eval $CMD

mv Faser-Physics-*kfalignment.root "../../2root_file/kfalignment_${RUN}_${RAW_FILE}.root"
rm Faser-Physics-*-xAOD.root

echo "=== Finished alignment ==="