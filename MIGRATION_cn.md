# 迁移指南：从守护进程到 DAGman

本指南帮助用户从旧的基于守护进程的方法（`auto_iter.py`）过渡到新的基于 HTCondor DAGman 的方法（`dag_manager.py`）。

## 为什么要迁移？

使用 `nohup` 的 `auto_iter.py` 守护进程方法在 CERN lxplus 上**不受官方支持**。HTCondor DAGman 是管理作业工作流的推荐和支持方法。

### 对比

| 方面 | 守护进程（`auto_iter.py`） | DAGman（`dag_manager.py`） |
|--------|------------------------|---------------------------|
| **lxplus 支持** | ❌ 非官方 | ✅ 官方支持 |
| **设置复杂度** | 中等 | 低（自动化） |
| **作业依赖** | 手动轮询 | 自动管理 |
| **故障恢复** | 基于脚本 | 内置重试 + 挽救 DAG |
| **监控** | 自定义日志 | 标准 HTCondor 工具 |
| **资源使用** | 持久守护进程 | 无持久进程 |
| **可扩展性** | 有限 | 优秀 |

## 迁移步骤

### 步骤 1：初始设置

**创建配置文件：**

```bash
# 交互式设置（推荐）
bash setup_config.sh

# 或手动设置
python config.py
# 然后编辑 config.json 设置您的路径
```

配置文件替代了 `auto_iter.py` 中的硬编码路径。

### 步骤 2：转换您的命令

**旧命令：**
```bash
nohup python3 auto_iter.py -y 2023 -r 011705 -f 450-500 -i 10 &>>auto_iter.log &
```

**新命令：**
```bash
python dag_manager.py -y 2023 -r 011705 -f 450-500 -i 10 --submit
```

### 步骤 3：命令行参数

所有参数保持不变：

| 旧标志 | 新标志 | 描述 |
|----------|----------|-------------|
| `-y`, `--year` | `-y`, `--year` | 年份 |
| `-r`, `--run` | `-r`, `--run` | 运行编号 |
| `-f`, `--files` | `-f`, `--files` | 文件范围 |
| `-i`, `--iterations` | `-i`, `--iterations` | 迭代次数 |
| `--fourst` | `--fourst` | 4站模式 |
| `--threest` | `--threest` | 3站模式 |

**新功能：**
- `--config`：指定自定义配置文件
- `--submit`：生成后自动提交 DAG

### 步骤 4：监控您的作业

**旧方法：**
```bash
# 监控守护进程日志
tail -f auto_iter.log

# 检查守护进程是否在运行
ps aux | grep auto_iter.py
```

**新方法：**
```bash
# 检查整体状态
condor_q

# 查看详细 DAG 状态
condor_q -dag

# 监控 DAGman 日志
tail -f Y2023_R011705_F450-500/alignment.dag.dagman.out

# 检查作业历史
condor_history <username>
```

### 步骤 5：处理问题

**旧方法：**
```bash
# 如果守护进程崩溃，手动重启
# 检查日志，修复问题，然后重新运行
```

**新方法：**
```bash
# HTCondor 自动重试失败的作业
# 如果 DAG 失败，使用挽救 DAG
condor_submit_dag Y2023_R011705_F450-500/alignment.dag.rescue001
```

## 目录结构对比

### 旧结构（auto_iter.py）

```
Y2023_R011705_F450-500/
├── iter01/
│   ├── 1reco/
│   ├── 2kfalignment/
│   └── 3millepede/
└── ...
```

### 新结构（dag_manager.py）

```
Y2023_R011705_F450-500/
├── alignment.dag              # 主 DAG 文件（新）
├── alignment.dag.dagman.out   # DAGman 日志（新）
├── iter01/
│   ├── pre_reco.sh           # PRE 脚本（新）
│   ├── 1reco/
│   │   ├── reco.sub          # 提交文件（新）
│   │   └── logs/             # 作业日志（新）
│   ├── 2kfalignment/
│   └── 3millepede/
│       ├── millepede.sub     # 提交文件（新）
│       └── run_millepede.sh  # 包装脚本（新）
└── ...
```

## 关键差异

### 1. 配置

**旧：** 路径硬编码在脚本中
```python
env_path = "/eos/home-s/shunlian/Alignment/env.sh"
```

**新：** 路径在 config.json 中
```json
{
  "paths": {
    "env_script": "reco_condor_env.sh"
  }
}
```

### 2. 作业提交

**旧：** 守护进程循环内手动提交
```python
subprocess.run(["condor_submit", "-spool", sub_path])
# 然后轮询完成
```

**新：** DAG 处理提交和依赖关系
```python
# DAG 自动管理所有作业提交
# 无需轮询
```

### 3. 作业依赖

**旧：** 带睡眠的手动轮询
```python
while True:
    time.sleep(300)
    # 检查作业是否完成
```

**新：** 通过 DAG 自动
```
PARENT reco_01 CHILD millepede_01
PARENT millepede_01 CHILD reco_02
```

### 4. 故障处理

**旧：** 脚本在失败时退出
```python
if hold_count != 0:
    print("Error: Some jobs are on hold.")
    sys.exit(1)
```

**新：** 自动重试 + 挽救 DAG
```
RETRY reco_01 2
RETRY millepede_01 1
# 加上自动挽救 DAG 生成
```

## 测试您的迁移

在迁移生产工作流之前：

```bash
# 1. 运行测试以验证设置
bash tests/test_integration.sh

# 2. 使用小数据集测试
python dag_manager.py -y 2023 -r 011705 -f 400-403 -i 2 --submit

# 3. 监控测试运行
condor_q -dag

# 4. 验证结果
ls -la Y2023_R011705_F400-403/
```

## 常见问题和解决方案

### 问题 1：找不到配置

**错误：** `FileNotFoundError: Configuration file not found: config.json`

**解决方案：**
```bash
python config.py
# 编辑 config.json 设置您的路径
```

### 问题 2：缺少环境脚本

**错误：** 找不到环境脚本

**解决方案：**
```bash
# 确保您的 config.json 指向正确的 env_script
# 脚本将使用它进行作业执行
```

### 问题 3：旧守护进程仍在运行

**警告：** 如果旧守护进程仍在运行，请先停止它

```bash
# 查找守护进程进程
ps aux | grep auto_iter.py

# 终止守护进程
kill <pid>

# 验证它已停止
ps aux | grep auto_iter.py
```

## 常见问题

**问：我还能使用 auto_iter.py 吗？**
答：可以，但不推荐。DAGman 是 lxplus 上官方支持的方法。

**问：我现有的工作流会受到影响吗？**
答：不会，现有完成的工作流不受影响。只有新工作流应使用 DAGman。

**问：我需要更改代码吗？**
答：不需要更改代码。只需切换命令并使用配置文件。

**问：如果我有旧守护进程在运行会怎样？**
答：先停止它以避免冲突。DAGman 是自包含的，不需要守护进程。

**问：我可以恢复失败的工作流吗？**
答：可以！DAGman 自动创建挽救 DAG：
```bash
condor_submit_dag Y2023_R011705_F450-500/alignment.dag.rescue001
```

**问：如何监控多个 DAG 工作流？**
答：使用标准 HTCondor 命令：
```bash
condor_q                  # 您的所有作业
condor_q -dag            # DAG 结构
condor_q -nobatch        # 详细视图
```

## 获取帮助

1. **文档：**
   - [README.md](README.md) - 概述
   - [USAGE_GUIDE.md](USAGE_GUIDE.md) - 详细用法
   - [tests/README.md](tests/README.md) - 测试

2. **先测试：**
   ```bash
   bash tests/test_integration.sh
   ```

3. **检查日志：**
   - DAGman 日志：`alignment.dag.dagman.out`
   - 作业日志：`iter*/1reco/logs/`

4. **HTCondor 资源：**
   - [HTCondor 文档](https://htcondor.readthedocs.io/)
   - [DAGMan 指南](https://htcondor.readthedocs.io/en/latest/users-manual/dagman-workflows.html)

## 总结

**迁移很简单：**
1. ✅ 设置配置：`bash setup_config.sh`
2. ✅ 替换命令：`dag_manager.py` 而不是 `auto_iter.py`
3. ✅ 监控方式：`condor_q -dag`

**好处：**
- ✅ 官方支持
- ✅ 更好的可靠性
- ✅ 更容易监控
- ✅ 自动恢复
- ✅ 无需守护进程

新的 DAGman 方法为 FASER 对齐工作流提供了更强大、可维护和官方支持的解决方案。
