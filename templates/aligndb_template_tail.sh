
echo "End WriteAlignmentConfig_Faser04.py"
echo ""

echo "Begin AtlCoolConsole.py"
echo "exit" | AtlCoolConsole.py "sqlite://;schema=FASER-04_ALLP200.db;dbname=CONDBR3"
echo "End AtlCoolConsole.py"
echo ""

#AtlCoolCopy "sqlite://;schema=./FASER-01_ALLP200.db;dbname=CONDBR3" "sqlite://;schema=data/sqlite200/ALLP200.db;dbname=CONDBR3" -fnp -ot "TRACKER-ALIGN-01"
AtlCoolCopy "sqlite://;schema=./FASER-04_ALLP200.db;dbname=CONDBR3" "sqlite://;schema=data/sqlite200/ALLP200.db;dbname=CONDBR3" -fnp -ot "TRACKER-ALIGN-05"

#AtlCoolConsole.py "sqlite://;schema=data/sqlite200/ALLP200.db;dbname=CONDBR3" < AtlCoolConsole_CONDBR3_input.txt

#AtlCoolConsole.py "sqlite://;schema=data/sqlite200/ALLP200.db;dbname=OFLP200" < AtlCoolConsole_OFLP200_input.txt

cp PoolFileCatalog.xml data/poolcond/
ln -s ${PWD}/data/poolcond/PoolFileCatalog.xml ${PWD}/data/poolcond/PoolCat_oflcond.xml
cp *_Align.pool.root data/poolcond/

#cp PoolFileCatalog.xml /afs/cern.ch/work/t/tarai/202404_calypso/run/data/poolcond/
#ln -s /afs/cern.ch/work/t/tarai/202404_calypso/run/data/poolcond/PoolFileCatalog.xml /afs/cern.ch/work/t/tarai/202404_calypso/run/data/poolcond/PoolCat_oflcond.xml
#cp *_Align.pool.root /afs/cern.ch/work/t/tarai/202404_calypso/run/data/poolcond/
