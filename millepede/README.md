# Mille Converter
a
FASER 对齐数据转换工具，将 ROOT 文件转换为 Millepede-II 格式。

## 依赖

### 必需依赖
- **ROOT** (版本 6.x)
- **CMake** (版本 3.16+)
- **C++ 编译器** (支持 C++17)

```bash
git clone --recurse-submodules git@github.com:shunliang233/Mille.git
```


## 编译
### 标准 CMake 流程
```bash
# Setup necessary enviroment
cmake -B build # 配置项目
cmake --build build # 编译
cmake --install build # 安装
```
### 一步编译
```bash
cmake -B build && cmake --build build && cmake --install build
```
### VS Code IntelliSense Environment Setup
```bash
# Setup necessary enviroment
cmake -B build # Produce build/compile_commands.json
```
Then VS Code IntelliSense should use exactly same environment as `cmake --build`.


## 使用方法
```bash
# 基本用法
./build/convert -i <input_directory> -o <output_file>

# 输出文本格式（用于调试）
./build/convert -i input_dir -o output_file -t

# 包含零值数据
./build/convert -i input_dir -o output_file -z

# 完整示例
./build/convert -i /eos/experiment/faser/alignment/data/run010738 -o mp2input
```

### 参数说明
- `-i, --input`: 输入目录，包含 kfalignment_*.root 文件
- `-o, --output`: 输出文件名（不包括扩展名）
- `-t, --text`: 输出文本格式而非二进制格式
- `-z, --zero`: 包含零值导数和标签

## 输出文件

- **二进制模式**: `<output>.bin` - 用于 Millepede-II
- **文本模式**: `<output>.txt` - 用于调试和检查

## 项目结构
错的，要改。
```
3mille/
├── CMakeLists.txt      # CMake 配置文件
├── Makefile           # 原有 Makefile（备用）
├── main.cc            # 主程序
├── Mille.h            # Mille 类头文件
├── Mille.cc           # Mille 类实现
├── README.md          # 本文件
└── build/             # CMake 构建目录
    └── convert        # 编译生成的可执行文件
```

## 故障排除

### ROOT 未找到
```bash
# 设置 ROOT 环境
source /path/to/root/bin/thisroot.sh

# 验证 ROOT 可用
root-config --version
```


### CMake 配置失败
```bash
# 清理并重新配置
rm -rf build
cmake -B build

# 查看详细输出
cmake -B build --debug-output
```

## 开发说明

- 使用现代 CMake (3.16+) 最佳实践
- Target-based 依赖管理
- 支持 Debug/Release 构建类型
- 遵循 C++17 标准
- 保持与原有 Makefile 的兼容性
