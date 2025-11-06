#!/bin/bash
CURRENT_DIR=$(pwd)
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
cd /eos/user/c/chiw/FASER/Alignment/
asetup --input=calypso/asetup.faser Athena,24.0.41
source run/setup.sh
cd $CURRENT_DIR
source /eos/user/c/chiw/FASER/Alignment/run/setup.sh
