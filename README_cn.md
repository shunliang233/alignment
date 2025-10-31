# How to use

## Source environment

### 事例重建环境配置
脚本会在环境脚本不存在时自动创建。运行 `main.py` 时使用 `--calypso_path` 参数提供 Calypso 安装路径即可。

如果环境脚本已存在，将直接使用现有脚本。可通过 `--env_script` 参数指定自定义路径（默认: `reco_condor_env.sh`）。

环境脚本所需包含内容如下：
```bash
#!/bin/bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase 
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
asetup --input=calypso/asetup.faser Athena,24.0.41
source /path/to/your/calypso/install/setup.sh
```

> :exclamation: 注意：使用 `--calypso_path` 参数时，请将 `/path/to/your/calypso/install` 替换为实际的 Calypso 安装路径。
>
以上脚本将会被用于在 HTCondor 计算节点中配置环境。

### 探测器对齐校准（Alignment）环境配置

所使用的软件工具为`Millepede II`，这一软件包由`Mille`和`pede`两个部分组成。在当前版本脚本中，`Mille`部分被链接在`millepede`目录下，且其调用已集成在`faser_alignment.py`脚本中；而`pede`部分则需要单独安装和配置。

#### 安装`pede`

`pede`的源代码可以通过Claus Kleinwort的DESY GitLab Repo获得，通过以下命令克隆：

```bash
git clone --depth 1 --branch V04-17-06 \
     https://gitlab.desy.de/claus.kleinwort/millepede-ii.git /path/to/your/pede/
cd /path/to/your/pede/
make pede
```

一般建议在安装后进行测试（大约10s）：

```bash
./pede -t
```

> :exclamation: 注意：请将`/path/to/your/pede/`替换为实际的`pede`安装路径。

#### 配置环境变量

在前面配置


## 借助`HTCondor`进行事例重建：`main.py`

### 基本用法
```bash
git clone git@github.com:shunliang233/raw2reco.git
```

```bash
python main.py --year 2023 --run 011705 --file 400 --calypso_path /path/to/calypso/install
# 或使用简短参数
python main.py -y 2023 -r 11705 -f 400 --calypso_path /path/to/calypso/install
```

### 批量处理多个 rawfile
```bash
# 使用范围格式 start-end
python main.py --year 2023 --run 011705 --file 400-450 --calypso_path /path/to/calypso/install

# 使用范围格式 start:end
python main.py --year 2023 --run 011705 --file 400:450 --calypso_path /path/to/calypso/install

# 简短参数形式
python main.py -y 2023 -r 11705 -f 400-450 --calypso_path /path/to/calypso/install
```

### 参数说明
- `--year, -y`: 年份 (必需，例如: 2022-2025)
- `--run, -r`: 运行编号 (必需，例如: 011705，会自动补零到6位)
- `--file, -f`: 单个原始文件编号 (如: 400) 或范围 (如: 400-450 或 400:450)
- `--fourst`: 运行4站模式 (可选，默认关闭)
- `--threest`: 运行3站模式 (可选，默认开启)
- `--env_script`: 环境配置脚本路径。如不存在将自动创建。（默认: reco_condor_env.sh）
- `--calypso_path`: Calypso 安装路径。当 env_script 不存在时必需。


## 整体工作流

### 执行初始事例重建
- 运行 `main.py` 项目主程序
  - 处理 `--file` 参数的类位于 `RawList.py` 中
- 生成 `submit_unbiased.sub` 文件，并以 `-spool` 形式提交到 Condor
  - 提交信息存储在 `main.log` 中
  - 每一个 Condor 节点中，单独运行 `runAlignment.sh` 脚本处理每个 `.raw` 文件
  - 脚本中包括 `aligndb_copy.sh` 参数配置，和 `faser_reco_alignment.py` 重建算法
  - 运行完成后用 `condor_transfer_data ${Cluster}` 获取日志文件
- 重建的 `.root` 文件存入 `../2root_file` 目录中

### 进行对齐校准（Alignment）
- 


### 日志文件
job执行后，日志文件会保存在 `logs/` 目录：
- `job_$(Cluster)_$(Process).out` - 标准输出
- `job_$(Cluster)_$(Process).err` - 错误输出  
- `job_$(Cluster)_$(Process).log` - Condor日志