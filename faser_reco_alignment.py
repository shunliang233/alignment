#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FASER 实验数据重建脚本
===================

本脚本基于 ATLAS Athena 框架，用于重建 FASER 探测器的原始数据，
将原始数据转换为物理分析所需的重建对象（如径迹、簇等）。

用法:
    ./faser_reco.py [--geom=runtype] filepath 
    
参数:
    filepath - 输入原始数据文件的完整路径，支持远程文件
    例如: "root://hepatl30//atlas/local/torrence/faser/commissioning/TestBeamData/Run-004150/Faser-Physics-004150-00000.raw"
    
    runtype - 可选的数据类型 (TI12Data, TI12Data02, TI12Data03, TestBeamData)

选项:
    --isMC - 处理蒙特卡罗模拟数据时需要
    --testBeam - 快捷方式，指定测试束流几何配置
    --alignment - 开启对准模式，仅允许一种跟踪算法

Copyright (C) 2002-2017 CERN for the benefit of the ATLAS collaboration
"""

# ====================================
# 必要模块导入和计时设置
# ====================================
import sys
import time
import argparse

# 记录脚本开始执行的时间，用于性能统计
a = time.time()

# ====================================
# 命令行参数解析器配置
# ====================================
# 设置命令行参数解析器，处理用户输入的各种配置选项
parser = argparse.ArgumentParser(description="Run FASER reconstruction")

# 必需参数：输入文件路径
parser.add_argument("file_path",
                    help="Fully qualified path of the raw input file")

# 几何配置选项
parser.add_argument("-g", "--geom", default="",
                    help="Specify geometry (if it can't be parsed from run number)\n Values: TI12Data03 (2022 TI12)")

# 条件数据库标签覆盖选项
parser.add_argument("-c", "--cond", default="",
                    help="Override global conditions tag (old alignment: --cond FASER-03)")

# 重建标签，用于输出文件命名
parser.add_argument("-r", "--reco", default="",
                    help="Specify reco tag (to append to output filename)")

# 事件处理数量控制
parser.add_argument("-n", "--nevents", type=int, default=-1,
                    help="Specify number of events to process (default: all)")
parser.add_argument("--skip", type=int, default=0,
                    help="Specify number of events to skip (default: none)")

# 调试和输出控制
parser.add_argument("-v", "--verbose", action='store_true', 
                    help="Turn on DEBUG output")

# 数据类型标识选项
parser.add_argument("--isMC", action='store_true',
                    help="Running on digitised MC rather than data")
parser.add_argument("--MC_calibTag", default="",
                    help="Specify tag used to reconstruct MC calo energy: (WAVE-Calibration-01-LG-nofilt, WAVE-Calibration-01-LG, WAVE-Calibration-01-HG-nofilt, or WAVE-Calibration-01-HG) ")
parser.add_argument("--testBeam", action='store_true',
                    help="Set geometry for 2021 test beam")
parser.add_argument("--isOverlay", action='store_true', 
                    help="Set overlaid data input")

# 算法开关选项，用于控制不同的重建算法
parser.add_argument("--noTracking", action='store_true',
                    help="Turn off tracking (for R24 debugging)")
parser.add_argument("--noIFT", action='store_true', default=False,
                    help="Turn off 4-station tracking")
parser.add_argument("--noForward", action='store_true', default=False,
                    help="Turn off forward CKF tracking")
parser.add_argument("--noBackward", action='store_true', default=False,
                    help="Turn off backward CKF tracking")
parser.add_argument("--alignment", action='store_true', default=False,
                    help="Turn on alignment: Only one tracking algorithm (3ST/4ST Forward/Backwards) allowed")
args = parser.parse_args()

# ====================================
# 几何配置自动识别
# ====================================
# 输入文件的路径处理
from pathlib import Path
filepath = Path(args.file_path)

# 确定 FASER 的几何版本，存储在 runtype 变量中
if len(args.geom) > 0:  # 用户已指定运行类型
    runtype = args.geom
elif args.testBeam:  # 测试束流的快捷方式
    print(f"Use 2021 TestBeam configuration")
    runtype = "TestBeamData"
else:
    print(f"Assuming 2024 TI12 geometry (TI12Data04)")
    runtype = "TI12Data04"
    
    """
    # 尝试从运行号自动选择正确的几何配置
    # 这对测试束流数据不起作用，
    # 所以暂时称之为一个临时解决方案
    """
    runname = filepath.parts[-1]
    try:
        # 从文件名中提取运行号（格式通常为：Faser-Physics-XXXXXX-XXXXX.raw）
        runnumber = int(runname.split('-')[2])
    except Exception as e:
        print(f"Failed to find run number in {filepath}")
        print(f"Couldn't parse {runname}")
        print(f"Leave runtype as {runtype}!")
    else:
        # 根据运行号范围确定几何配置版本
        if runnumber > 6700: # Not sure if this is exact
            print(f"Found run number {runnumber}, using TI12 configuration with IFT+faserNu")
            runtype = "TI12Data04"
        elif runnumber > 5302: # Last TI12 run on Nov. 23, 2021 without IFT
            print(f"Found run number {runnumber}, using TI12 configuration with IFT")
            runtype = "TI12Data02"
        else:
            print(f"Found run number {runnumber}, using original TI12 configuration")
            runtype = "TI12Data"

# 打印基础的重建信息
print(f"Starting reconstruction of {filepath.name} with type {runtype}")
if args.nevents > 0:
    print(f"Reconstructing {args.nevents} events by command-line option")
if args.skip > 0:
    print(f"Skipping {args.skip} events by command-line option")

# ====================================
# Athena 框架初始化和配置标志设置
# ====================================

"""基础框架组件导入"""
from AthenaConfiguration.ComponentAccumulator import ComponentAccumulator # 算法容器和流水线构建器
from AthenaConfiguration.ComponentFactory import CompFactory # 用于创建算法和服务的工厂
from AthenaCommon.Constants import VERBOSE, INFO # 日志记录级别
from AthenaCommon.Configurable import Configurable # 基类，用于所有可配置组件
from CalypsoConfiguration.AllConfigFlags import initConfigFlags # 初始化配置标志
Configurable.configurableRun3Behavior = True # 使用 Run 3 行为

"""    
configFlags 是 Athena 框架的全局配置标志，
用于控制整个 FASER 数据重建流水线的行为
"""
# 基础配置标志初始化
configFlags = initConfigFlags()
configFlags.Input.isMC = args.isMC               # Needed to bypass autoconfig
if args.isMC:
    configFlags.IOVDb.DatabaseInstance = "OFLP200"   # Use MC conditions
else:
    configFlags.IOVDb.DatabaseInstance = "CONDBR3" # Use data conditions

configFlags.Input.ProjectName = "data20"         # 指定项目名称
#configFlags.GeoModel.Align.Dynamic    = False   # 关闭动态几何对齐
configFlags.Exec.SkipEvents = args.skip          # 设置跳过的事件数

# ====================================
# 探测器几何配置和数据库标签设置
# ====================================
# 几何配置标志 - 控制使用哪些重建算法
useCKF = True   # 默认使用组合卡尔曼滤波跟踪算法 (Combinatorial Kalman Filter)
useCal = False  # 默认不使用量能器重建
useLHC = False  # 默认不使用 LHC 数据算法
if args.noTracking:
    useCKF = False

# 根据运行类型配置几何版本和条件数据库标签
if runtype == "TI12Data":  # TI12 宇宙线几何配置
    configFlags.GeoModel.FaserVersion = "FASER-01" 
    configFlags.IOVDb.GlobalTag = "OFLCOND-FASER-01"
elif runtype in ["TestBeamData", "TestBeamMC"]:  # 测试束流设置 
    configFlags.GeoModel.FaserVersion = "FASER-TB01" 
    configFlags.IOVDb.GlobalTag = "OFLCOND-FASER-TB01"
    print("Set global tag to OFLCOND-FASER-TB01")
    useCKF = False  # 测试束流几何不使用 CKF 跟踪
    useCal = True   # 测试束流使用量能器重建
elif runtype == "TI12Data02": # New TI12 geometry (ugh)
    configFlags.GeoModel.FaserVersion = "FASER-02" 
    configFlags.IOVDb.GlobalTag = "OFLCOND-FASER-03"
elif runtype in ["TI12Data03", "TI12MC03"]: # Final 2022 TI12 geometry
    configFlags.GeoModel.FaserVersion = "FASERNU-03"
    # Ugh, this is a horrible hack
    # and I am not sure it is even needed as there may not be a difference
    # in reco between the MC global tags...
    if args.isMC:
        configFlags.IOVDb.GlobalTag = "OFLCOND-FASER-03" # Consistent with sim/digi
    else:
        configFlags.IOVDb.GlobalTag = "OFLCOND-FASER-04" # Updated 2023 alignment
    useCal = True
    if not args.isMC:  # 实际数据使用 LHC 数据算法
        useLHC = True
elif runtype in ["TI12Data04", "TI12MC04"]: # Updated 2023 TI12 geometry
    configFlags.GeoModel.FaserVersion = "FASERNU-04" 
    configFlags.IOVDb.GlobalTag = "OFLCOND-FASER-05" # Latest 2025 alignment
    useCal = True   # 使用量能器重建
    if not args.isMC:
        useLHC = True   # 实际数据使用 LHC 数据算法
else:
    print("Invalid run type found:", runtype)
    print("Specify correct type or update list")
    sys.exit(1)

# 检查是否要覆盖全局条件标签（用于测试不同的对准）
if len(args.cond):
    configFlags.IOVDb.GlobalTag = args.cond
    print(f"Override global tag configFlags.IOVDb.GlobalTag = {args.cond}")

# 如果使用 CKF，启用 ACTS 物质修正
if useCKF:
    # Enable ACTS material corrections, this crashes testbeam geometries
    # Use alma-9 specific file
    print(">>> Using alma9 specific ACTS material file! <<<")
    configFlags.TrackingGeometry.MaterialSource = "/cvmfs/faser.cern.ch/repo/sw/database/DBRelease/current/acts/material-maps-alma9.json"

# ====================================
# 输出文件配置
# ====================================
# 设置输出文件名
# 必须使用原始输入字符串，因为 pathlib 会破坏路径名中的双斜杠 //
configFlags.Input.Files = [ args.file_path ]
filestem = filepath.stem

# 删除任何文件类型修饰符
if filestem[-4:] == "-RDO":
    filestem = filestem[:-4]
if len(args.reco) > 0:
    filestem += f"-{args.reco}"

# 配置输出文件名
configFlags.addFlag("Output.xAODFileName", f"{filestem}-xAOD.root")
configFlags.Output.ESDFileName = f"{filestem}-ESD.root"
configFlags.Output.doWriteESD = False  # 不写入 ESD 格式
configFlags.addFlag("Output.doWritexAOD", True)  # 写入 xAOD 格式
# Play around with this?
# configFlags.Concurrency.NumThreads = 2
# configFlags.Concurrency.NumConcurrentEvents = 2
configFlags.lock()  # 锁定配置，防止进一步修改

"""
acc.merge() 配置具体的服务和功能
"""
from CalypsoConfiguration.MainServicesConfig import MainServicesCfg # 配置 FASER 实验的核心服务
from AthenaPoolCnvSvc.PoolWriteConfig import PoolWriteCfg # 配置 ROOT 文件写入服务
acc = MainServicesCfg(configFlags)
acc.merge(PoolWriteCfg(configFlags))

# Set up RAW data access
if args.isMC or args.isOverlay:
    from AthenaPoolCnvSvc.PoolReadConfig import PoolReadCfg
    acc.merge(PoolReadCfg(configFlags))
else:    
    from FaserByteStreamCnvSvc.FaserByteStreamCnvSvcConfig import FaserByteStreamCnvSvcCfg
    acc.merge(FaserByteStreamCnvSvcCfg(configFlags))

# 几何配置
# Needed, or move to MainServicesCfg?
from FaserGeoModel.FaserGeoModelConfig import FaserGeometryCfg
acc.merge(FaserGeometryCfg(configFlags))

if useLHC and not args.isOverlay:
    from LHCDataAlgs.LHCDataAlgConfig import LHCDataAlgCfg
    acc.merge(LHCDataAlgCfg(configFlags))

# ====================================
# 重建算法链配置
# ====================================
if not args.isOverlay:
    # 波形重建算法 - 从原始电子学信号重建物理量
    from WaveRecAlgs.WaveRecAlgsConfig import WaveformReconstructionCfg    
    acc.merge(WaveformReconstructionCfg(configFlags))

    # 量能器能量重建
    if useCal:
        from CaloRecAlgs.CaloRecAlgsConfig import CalorimeterReconstructionCfg
        acc.merge(CalorimeterReconstructionCfg(configFlags, MC_calibTag=args.MC_calibTag))

# 跟踪器簇重建 - 将相邻的硅条信号聚集成簇
from TrackerPrepRawDataFormation.TrackerPrepRawDataFormationConfig import FaserSCT_ClusterizationCfg
# acc.merge(FaserSCT_ClusterizationCfg(configFlags, DataObjectName="Pos_SCT_RDOs"))
acc.merge(FaserSCT_ClusterizationCfg(configFlags, DataObjectName="SCT_RDOs", checkBadChannels=True))

# 空间点重建 - 从硅条簇计算三维空间点
from TrackerSpacePointFormation.TrackerSpacePointFormationConfig import TrackerSpacePointFinderCfg
acc.merge(TrackerSpacePointFinderCfg(configFlags))

# 径迹段拟合算法（Dave 的新拟合器）
# 放宽 ReducedChi2Cut 直到对准改善
from TrackerSegmentFit.TrackerSegmentFitConfig import SegmentFitAlgCfg
acc.merge(SegmentFitAlgCfg(configFlags,
                           ReducedChi2Cut=25.,      # 减少卡方阈值
                           SharedHitFraction=0.61,  # 共享击中比例阈值
                           MinClustersPerFit=5,     # 每次拟合的最小簇数
                           TanThetaXZCut=0.083))    # tan(角度) 阈值

# ====================================
# 组合卡尔曼滤波器（CKF）跟踪配置
# ====================================
# 开启 CKF 径迹寻找算法
if useCKF:
    # Ghost 径迹清理算法 - 移除虚假径迹
    from FaserActsKalmanFilter.GhostBustersConfig import GhostBustersCfg
    acc.merge(GhostBustersCfg(configFlags))

    # 卡尔曼滤波器用于径迹重建
    # 同时进行前向和后向跟踪
    from FaserActsKalmanFilter.CKF2Config import CKF2Cfg
    
    # 前向跟踪算法
    if not args.noForward:
        if args.noIFT:
            # 4-station forward (no IFT)
            acc.merge(CKF2Cfg(configFlags, maskedLayers=[0, 1, 2], name="CKF_woIFT",
                            actsOutputTag=f"{filestem}_3station_forward",
                            OutputCollection="CKFTrackCollectionWithoutIFT",
                            BackwardPropagation=False,
                            alignmentWriter=args.alignment,
                            noDiagnostics=True))
        else:
            # 4-station forward only if not overlay
            if not args.isOverlay:
                acc.merge(CKF2Cfg(configFlags,
                                actsOutputTag=f"{filestem}_4station_forward",
                                alignmentWriter=args.alignment,
                                noDiagnostics=True))

    # 后向跟踪算法
    if not args.noBackward:
        if args.noIFT:
            # 3-station backward (no IFT)
            acc.merge(CKF2Cfg(configFlags, maskedLayers=[0, 1, 2], name="CKF_Back_woIFT",
                            actsOutputTag=f"{filestem}_3station_backward",
                            OutputCollection="CKFTrackCollectionBackwardWithoutIFT",
                            BackwardPropagation=True,
                            alignmentWriter=args.alignment,
                            noDiagnostics=True))
        else:
            # 4-station backward only if not overlay
            if not args.isOverlay:
                acc.merge(CKF2Cfg(configFlags, name="CKF_Back",
                                actsOutputTag=f"{filestem}_4station_backward",
                                OutputCollection="CKFTrackCollectionBackward",
                                BackwardPropagation=True,
                                alignmentWriter=args.alignment,
                                noDiagnostics=True))

# ====================================
# 输出配置和数据对象定义
# ====================================
# 配置输出流
from OutputStreamAthenaPool.OutputStreamConfig import OutputStreamCfg
# 定义要输出到 xAOD 文件的数据对象
itemList = [ "xAOD::EventInfo#*"                      # 事件信息
             , "xAOD::EventAuxInfo#*"                  # 事件辅助信息
             , "xAOD::FaserTriggerData#*"              # FASER 触发数据
             , "xAOD::FaserTriggerDataAux#*"           # 触发数据辅助信息
             , "FaserSiHitCollection#*"                # Strip hits, do we want this?
             , "FaserSCT_RDO_Container#*"              # SCT 原始数据容器
             , "FaserSCT_SpacePointContainer#*"        # 空间点容器
             , "Tracker::FaserSCT_ClusterContainer#*"  # 跟踪器簇容器
             , "TrackCollection#*"                     # 径迹集合
             , "xAOD::FaserEventInfo#*"                # FASER 事件信息
             , "xAOD::FaserEventInfoAux#*"             # FASER 事件信息辅助
]

# 添加 LHC 数据对象（如果使用）
if useLHC and not args.isOverlay:
    itemList.extend( ["xAOD::FaserLHCData#*", "xAOD::FaserLHCDataAux#*"] )

# 为蒙特卡罗数据添加真实信息
if args.isMC and not args.isOverlay:
    # 创建 xAOD 版本的真实信息
    from Reconstruction.xAODTruthCnvAlgConfig import xAODTruthCnvAlgCfg
    acc.merge(xAODTruthCnvAlgCfg(configFlags))

    # 添加 MC 信息到输出列表
    itemList.extend( ["McEventCollection#*", "TrackerSimDataCollection#*"] )

# 输出流配置
acc.merge(OutputStreamCfg(configFlags, "xAOD", itemList, disableEventTag=True))

# 元数据配置（蒙特卡罗数据）
if args.isMC:
    from xAODMetaDataCnv.InfileMetaDataConfig import SetupMetaDataForStreamCfg
    acc.merge(SetupMetaDataForStreamCfg(configFlags, "xAOD"))

# Try to turn off annoying INFO message, as we don't use this
# disableEventTag=True doesn't seem to work...
tagBuilder = CompFactory.EventInfoTagBuilder()
tagBuilder.PropagateInput=False
acc.addEventAlgo(tagBuilder)

# 添加重建算法的输出配置
if not args.isOverlay:
    # 波形重建输出
    from WaveRecAlgs.WaveRecAlgsConfig import WaveformReconstructionOutputCfg    
    acc.merge(WaveformReconstructionOutputCfg(configFlags))

    # 量能器重建输出
    from CaloRecAlgs.CaloRecAlgsConfig import CalorimeterReconstructionOutputCfg
    acc.merge(CalorimeterReconstructionOutputCfg(configFlags))

# ====================================
# 服务配置和执行设置
# ====================================

# Check what we have
from OutputStreamAthenaPool.OutputStreamConfig import outputStreamName
print( "Writing out xAOD objects:" )
print( acc.getEventAlgo(outputStreamName("xAOD")).ItemList )

# Hack to avoid problem with our use of MC databases when isMC = False
if not args.isMC:
    replicaSvc = acc.getService("DBReplicaSvc")
    replicaSvc.COOLSQLiteVetoPattern = ""
    replicaSvc.UseCOOLSQLite = True
    replicaSvc.UseCOOLFrontier = False
    replicaSvc.UseGeomSQLite = True

# Configure verbosity    
if args.verbose:
    acc.foreach_component("*").OutputLevel = VERBOSE
    configFlags.dump()
    # Print out POOL conditions
    import os
    print(f"ATLAS_POOLCOND_PATH: {os.environ['ATLAS_POOLCOND_PATH']}")
    print(f"PoolSvc.ReadCatalog: {acc.getService('PoolSvc').ReadCatalog}")
    print(f"PoolSvc.WriteCatalog: {acc.getService('PoolSvc').WriteCatalog}")
else:
    acc.foreach_component("*").OutputLevel = INFO
    # Reduce event loop printout
    eventLoop = CompFactory.AthenaEventLoopMgr()
    eventLoop.EventPrintoutInterval = 100
    acc.addService(eventLoop)

acc.foreach_component("*ClassID*").OutputLevel = INFO

acc.getService("MessageSvc").Format = "% F%40W%S%7W%R%T %0W%M"

# ====================================
# 执行重建并完成
# ====================================
# 执行重建流水线
sc = acc.run(maxEvents=args.nevents)

# 计算执行时间
b = time.time()
from AthenaCommon.Logging import log
log.info(f"Finish execution in {b-a} seconds")

# 错误信号处理
if sc.isSuccess():
    log.info("Execution succeeded")
    sys.exit(0)
else:
    log.info("Execution failed, return 1")
    sys.exit(1)