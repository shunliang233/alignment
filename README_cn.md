# How to use

## Source environment
```bash
#!/bin/bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase 
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
asetup --input=calypso/asetup.faser Athena,24.0.41
source /eos/home-s/shunlian/Alignment/install/setup.sh
```

## Run `main.py`

### 基本用法
```bash
git clone git@github.com:shunliang233/raw2reco.git
```

```bash
python main.py --year 2023 --run 011705 --file 400
# 或使用简短参数
python main.py -y 2023 -r 11705 -f 400
```

### 批量处理多个 rawfile
```bash
# 使用范围格式 start-end
python main.py --year 2023 --run 011705 --file 400-450

# 使用范围格式 start:end
python main.py --year 2023 --run 011705 --file 400:450

# 简短参数形式
python main.py -y 2023 -r 11705 -f 400-450
```

### 参数说明
- `--year, -y`: 年份 (必需，例如: 2022-2025)
- `--run, -r`: 运行编号 (必需，例如: 011705，会自动补零到6位)
- `--file, -f`: 单个原始文件编号 (如: 400) 或范围 (如: 400-450 或 400:450)
- `--fourst`: 运行4站模式 (可选，默认关闭)
- `--threest`: 运行3站模式 (可选，默认开启)


## 文件说明
- 运行 `main.py` 项目主程序
- 处理 `--file` 参数的类位于 `RawList.py` 中
- 生成 `submit_unbiased.sub` 文件，并以 `-spool` 形式提交到 Condor
- 提交信息存储在 `main.log` 中
- 每一个 Condor 节点单独运行 `runAlignment.sh` 脚本处理每个 `.raw` 文件
- 脚本中包括 `aligndb_copy.sh` 参数配置，和 `faser_reco_alignment.py` 重建算法
- 重建的 `.root` 文件存入 `../2root_file` 目录中
- 运行完成后用 `condor_transfer_data ${Cluster}` 获取日志文件


### 日志文件
job执行后，日志文件会保存在 `logs/` 目录：
- `job_$(Cluster)_$(Process).out` - 标准输出
- `job_$(Cluster)_$(Process).err` - 错误输出  
- `job_$(Cluster)_$(Process).log` - Condor日志