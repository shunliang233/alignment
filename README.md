# How to use

## Source environment
```bash
#!/bin/bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase 
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
asetup --input=calypso/asetup.faser Athena,24.0.41
source /eos/home-s/shunlian/Alignment/install/setup.sh
```

## Run `runAlignment.py`

### 基本用法
```bash
python runAlignment.py --year 2023 --run 011705 --rawfile 400
# 或使用简短参数
python runAlignment.py -y 2023 -r 11705 -f 400
```

### 参数说明
- `--year, -y`: 年份 (必需，例如: 2022-2025)
- `--run, -r`: 运行编号 (必需，例如: 011705，会自动补零到6位)
- `--rawfile, -f`: 单个原始文件编号 (例如: 400，会自动补零到5位)
- `--fourst`: 运行4站模式 (可选，默认关闭)
- `--threest`: 运行3站模式 (可选，默认开启)

### 输出文件
脚本会生成 `submit_unbiased.sub` 文件并自动提交到 Condor：
- **单个文件模式：** 提交1个job

### 示例
```bash
# 处理单个文件
python runAlignment.py -y 2023 -r 11705 -f 400

# 4站模式处理
python runAlignment.py -y 2023 -r 11705 -f 400 --fourst

# 查看帮助
python runAlignment.py --help
```

### 日志文件
job执行后，日志文件会保存在 `logs/` 目录：
- `job_$(Cluster)_$(Process).out` - 标准输出
- `job_$(Cluster)_$(Process).err` - 错误输出  
- `job_$(Cluster)_$(Process).log` - Condor日志
