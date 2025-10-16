# Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration

#!/usr/bin/env python
import sys
from AthenaCommon.Constants import VERBOSE, INFO
from AthenaConfiguration.ComponentFactory import CompFactory

def WriteAlignmentCfg(flags, name="WriteAlignmentAlg", alignmentConstants={}, **kwargs):

    # Initialize GeoModel
    from FaserGeoModel.FaserGeoModelConfig import FaserGeometryCfg
    a = FaserGeometryCfg(flags)

    # This section is to allow alignment to be written to a conditions DB file
    from IOVDbSvc.IOVDbSvcConfig import IOVDbSvcCfg
    result = IOVDbSvcCfg(flags)
    iovDbSvc = result.getPrimary()
    iovDbSvc.dbConnection=flags.IOVDb.DBConnection
    a.merge(result)

    AthenaPoolCnvSvc=CompFactory.AthenaPoolCnvSvc
    apcs=AthenaPoolCnvSvc()
    a.addService(apcs)
    EvtPersistencySvc=CompFactory.EvtPersistencySvc
    a.addService(EvtPersistencySvc("EventPersistencySvc",CnvServices=[apcs.getFullJobOptName(),]))

    a.addService(CompFactory.IOVRegistrationSvc(PayloadTable=False,OutputLevel=VERBOSE))

    # Configure the algorithm itself
    WriteAlignmentAlg = CompFactory.WriteAlignmentAlg
    outputTool = CompFactory.AthenaOutputStreamTool("DbStreamTool", OutputFile = flags.WriteAlignment.PoolFileName, 
                                                                    PoolContainerPrefix="ConditionsContainer", 
                                                                    TopLevelContainerName = "<type>",
                                                                    SubLevelBranchName= "<key>" )

    trackerAlignDBTool = CompFactory.TrackerAlignDBTool("AlignDbTool", OutputTool = outputTool, 
                                                                       OutputLevel=VERBOSE,
                                                                       AlignmentConstants = {}) 
    kwargs.setdefault("AlignDbTool", trackerAlignDBTool)
    trackerAlignDBTool.AlignmentConstants = alignmentConstants 
    a.addEventAlgo(WriteAlignmentAlg(name, **kwargs))

    return a


if __name__ == "__main__":
    # from AthenaCommon.Logging import log, logging
    from AthenaCommon.Configurable import Configurable
    # from AthenaConfiguration.ComponentFactory import CompFactory
    from CalypsoConfiguration.AllConfigFlags import initConfigFlags

    Configurable.configurableRun3Behavior = True
    
# Flags for this job
    configFlags = initConfigFlags()
    configFlags.Input.isMC = False                                # Needed to bypass autoconfig
    configFlags.GeoModel.FaserVersion     = "FASER-01"           # Default FASER geometry
    configFlags.IOVDb.GlobalTag           = "OFLCOND-"+ configFlags.GeoModel.FaserVersion  # Always needed; must match FaserVersion
    configFlags.IOVDb.DBConnection        = "sqlite://;schema=" + configFlags.GeoModel.FaserVersion + "_ALLP200.db;dbname=OFLP200"
    configFlags.GeoModel.Align.Disable = True          # Hack to avoid loading alignment when we want to create it from scratch
    configFlags.addFlag("WriteAlignment.PoolFileName", configFlags.GeoModel.FaserVersion + "_Align.pool.root") 

# Parse flags from command line and lock
    configFlags.addFlag("AlignDbTool.AlignmentConstants", {}) 
    configFlags.fillFromArgs(sys.argv[1:])
    configFlags.lock()

# Configure components
    from CalypsoConfiguration.MainServicesConfig import MainServicesCfg
    acc = MainServicesCfg(configFlags)

# Set things up to create a conditions DB with neutral Tracker alignment transforms
    acc.merge(WriteAlignmentCfg(configFlags, alignmentConstants=configFlags.AlignDbTool.AlignmentConstants, ValidRunStart=1, ValidEvtStart=0, ValidRunEnd=9999999, ValidEvtEnd=9999999, CondTag=configFlags.GeoModel.FaserVersion.replace("FASER", "TRACKER-ALIGN"), ))

# Configure verbosity    
    # configFlags.dump()
    # logging.getLogger('forcomps').setLevel(VERBOSE)
    acc.foreach_component("*").OutputLevel = VERBOSE
    acc.foreach_component("*ClassID*").OutputLevel = INFO
    # log.setLevel(VERBOSE)
    
# Execute and finish
    sys.exit(int(acc.run(maxEvents=1).isFailure()))