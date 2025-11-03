#!/bin/bash
# Integration test script for FASER alignment DAGman workflow
# This script tests the complete workflow without actually submitting to HTCondor

set -e  # Exit on error

echo "=========================================="
echo "FASER Alignment DAGman Integration Test"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )"

# Create temporary test directory
TEST_DIR=$(mktemp -d -t faser-test-XXXXXX)
echo "Created temporary test directory: ${TEST_DIR}"

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up test directory..."
    rm -rf "${TEST_DIR}"
    echo "Done."
}
trap cleanup EXIT

# Change to test directory
cd "${TEST_DIR}"

echo ""
echo "Test 1: Configuration Management"
echo "--------------------------------"

# Copy config.py to test directory
cp "${ROOT_DIR}/config.py" .
cp "${ROOT_DIR}/RawList.py" .

# Create test config
python3 config.py test_config.json << EOF
y
EOF

if [ -f "test_config.json" ]; then
    echo "✓ Config file created successfully"
else
    echo "✗ Failed to create config file"
    exit 1
fi

# Validate config structure
python3 << 'EOF'
import json
with open('test_config.json', 'r') as f:
    config = json.load(f)
assert 'paths' in config, "Missing 'paths' section"
assert 'htcondor' in config, "Missing 'htcondor' section"
assert 'alignment' in config, "Missing 'alignment' section"
print("✓ Config structure validated")
EOF

echo ""
echo "Test 2: DAG Generation (Dry Run)"
echo "--------------------------------"

# Update config with test paths
python3 << 'EOF'
import json
with open('test_config.json', 'r') as f:
    config = json.load(f)

config['paths']['calypso_install'] = '/test/calypso'
config['paths']['pede_install'] = '/test/pede'
config['paths']['env_script'] = 'test_env.sh'

with open('test_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Config updated with test paths")
EOF

# Copy required files
cp "${ROOT_DIR}/dag_manager.py" .
cp "${ROOT_DIR}/config.py" .
cp "${ROOT_DIR}/RawList.py" .

# Create dummy millepede structure
mkdir -p millepede/bin
touch millepede/bin/millepede.py

# Create dummy scripts
touch runAlignment.sh
chmod +x runAlignment.sh
touch test_env.sh

# Generate DAG
echo "Generating DAG for 2 iterations with files 400-402..."
python3 dag_manager.py -y 2023 -r 011705 -f 400-402 -i 2 --config test_config.json

# Check DAG file was created
if [ -f "Y2023_R011705_F400-402/alignment.dag" ]; then
    echo "✓ DAG file generated successfully"
else
    echo "✗ Failed to generate DAG file"
    exit 1
fi

# Verify DAG structure
echo "Validating DAG structure..."
DAG_FILE="Y2023_R011705_F400-402/alignment.dag"

# Check for required job definitions
if grep -q "JOB reco_01" "${DAG_FILE}" && \
   grep -q "JOB millepede_01" "${DAG_FILE}" && \
   grep -q "JOB reco_02" "${DAG_FILE}" && \
   grep -q "JOB millepede_02" "${DAG_FILE}"; then
    echo "✓ All job definitions present"
else
    echo "✗ Missing job definitions"
    exit 1
fi

# Check for dependencies
if grep -q "PARENT reco_01 CHILD millepede_01" "${DAG_FILE}" && \
   grep -q "PARENT millepede_01 CHILD reco_02" "${DAG_FILE}"; then
    echo "✓ Job dependencies correctly defined"
else
    echo "✗ Missing or incorrect job dependencies"
    exit 1
fi

# Check submit files were created
if [ -f "Y2023_R011705_F400-402/iter01/1reco/reco.sub" ] && \
   [ -f "Y2023_R011705_F400-402/iter01/3millepede/millepede.sub" ]; then
    echo "✓ Submit files created"
else
    echo "✗ Missing submit files"
    exit 1
fi

echo ""
echo "Test 3: Submit File Validation"
echo "-------------------------------"

# Validate reconstruction submit file
RECO_SUB="Y2023_R011705_F400-402/iter01/1reco/reco.sub"
if grep -q "executable" "${RECO_SUB}" && \
   grep -q "queue" "${RECO_SUB}" && \
   grep -q "arguments" "${RECO_SUB}"; then
    echo "✓ Reconstruction submit file structure valid"
else
    echo "✗ Invalid reconstruction submit file"
    exit 1
fi

# Count number of jobs (should be 2 for files 400-402, which is 400 and 401)
QUEUE_COUNT=$(grep -c "^queue" "${RECO_SUB}")
if [ "${QUEUE_COUNT}" -eq 2 ]; then
    echo "✓ Correct number of reconstruction jobs (2)"
else
    echo "✗ Incorrect number of reconstruction jobs (expected 2, got ${QUEUE_COUNT})"
    exit 1
fi

# Validate millepede submit file
MILLE_SUB="Y2023_R011705_F400-402/iter01/3millepede/millepede.sub"
if grep -q "executable" "${MILLE_SUB}" && \
   grep -q "queue" "${MILLE_SUB}"; then
    echo "✓ Millepede submit file structure valid"
else
    echo "✗ Invalid millepede submit file"
    exit 1
fi

echo ""
echo "Test 4: Directory Structure"
echo "---------------------------"

# Check iteration directories
for iter in 01 02; do
    ITER_DIR="Y2023_R011705_F400-402/iter${iter}"
    if [ -d "${ITER_DIR}/1reco" ] && \
       [ -d "${ITER_DIR}/2kfalignment" ] && \
       [ -d "${ITER_DIR}/3millepede" ]; then
        echo "✓ Iteration ${iter} directory structure correct"
    else
        echo "✗ Iteration ${iter} directory structure incorrect"
        exit 1
    fi
    
    # Check inputforalign.txt exists
    if [ -f "${ITER_DIR}/1reco/inputforalign.txt" ]; then
        echo "✓ inputforalign.txt created for iteration ${iter}"
    else
        echo "✗ inputforalign.txt missing for iteration ${iter}"
        exit 1
    fi
done

echo ""
echo "Test 5: RawList Functionality"
echo "-----------------------------"

python3 << 'EOF'
from RawList import RawList

# Test single file
rl = RawList('400')
assert len(rl) == 1, "Single file count incorrect"
assert list(rl)[0] == '00400', "Single file format incorrect"
print("✓ Single file processing")

# Test range with dash
rl = RawList('400-403')
assert len(rl) == 3, "Range count incorrect"
assert list(rl) == ['00400', '00401', '00402'], "Range values incorrect"
print("✓ Range with dash processing")

# Test range with colon
rl = RawList('400:403')
assert len(rl) == 3, "Colon range count incorrect"
print("✓ Range with colon processing")

# Test string representation
assert str(RawList('400')) == '400', "Single file string incorrect"
assert str(RawList('400-403')) == '400-403', "Range string incorrect"
print("✓ String representation")

print("✓ All RawList tests passed")
EOF

echo ""
echo "=========================================="
echo "All Integration Tests Passed! ✓"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Configuration management: Working"
echo "  - DAG generation: Working"
echo "  - Submit file creation: Working"
echo "  - Directory structure: Correct"
echo "  - RawList processing: Working"
echo ""
echo "The DAGman workflow is ready for production use."
echo "To submit a real workflow, run:"
echo "  python dag_manager.py -y <year> -r <run> -f <files> -i <iterations> --submit"
