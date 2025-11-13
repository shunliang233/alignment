#!/bin/bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase 
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
asetup --input=/eos/home-s/shunlian/Alignment/calypso/asetup.faser Athena,24.0.41
source /eos/home-s/shunlian/Alignment/install/setup.sh