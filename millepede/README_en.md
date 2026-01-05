# Mille Converter

A tool for converting FASER alignment data: convert ROOT files to Millepede-II format.

## Dependencies

### Required
- **ROOT** (version 6.x)
- **CMake** (version 3.16+)
- **C++ Compiler** (with C++17 support)

## Build
### Standard CMake Workflow
```bash
# Setup necessary environment
cmake -B build # Configure project
cmake --build build # Build
cmake --install build # Install
```
### One-step build
```bash
cmake -B build && cmake --build build && cmake --install build
```
### VS Code IntelliSense Environment Setup
```bash
# Setup necessary environment
cmake -B build # Produce build/compile_commands.json
```
Then VS Code IntelliSense should use exactly the same environment as `cmake --build`.

## Usage
```bash
# Basic usage
./build/convert -i <input_directory> -o <output_file>

# Output in text format (for debugging)
./build/convert -i input_dir -o output_file -t

# Include zero-value data
./build/convert -i input_dir -o output_file -z

# Full example
./build/convert -i /eos/experiment/faser/alignment/data/run010738 -o mp2input
```

### Parameter Description
- `-i, --input`: Input directory containing kfalignment_*.root files
- `-o, --output`: Output file name (without extension)
- `-t, --text`: Output in text format instead of binary
- `-z, --zero`: Include zero-value derivatives and labels

## Output Files

- **Binary mode**: `<output>.bin` - for Millepede-II
- **Text mode**: `<output>.txt` - for debugging and inspection

## Project Structure
(To be updated)
```
3mille/
├── CMakeLists.txt      # CMake configuration file
├── Makefile           # Legacy Makefile (for reference)
├── main.cc            # Main program
├── Mille.h            # Mille class header
├── Mille.cc           # Mille class implementation
├── README.md          # This file
└── build/             # CMake build directory
    └── convert        # Built executable
```

## Troubleshooting

### ROOT Not Found
```bash
# Set up ROOT environment
source /path/to/root/bin/thisroot.sh

# Verify ROOT is available
root-config --version
```

### CMake Configuration Failure
```bash
# Clean and reconfigure
rm -rf build
cmake -B build

# Show detailed output
cmake -B build --debug-output
```

## Development Notes

- Uses modern CMake (3.16+) best practices
- Target-based dependency management
- Supports Debug/Release build types
- Follows C++17 standard
- Maintains compatibility with the legacy Makefile
