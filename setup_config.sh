#!/bin/bash
# Interactive configuration setup script for FASER alignment

echo "=========================================="
echo "FASER Alignment Configuration Setup"
echo "=========================================="
echo ""

CONFIG_FILE="config.json"

# Check if config already exists
if [ -f "$CONFIG_FILE" ]; then
    echo "Configuration file already exists: $CONFIG_FILE"
    read -p "Do you want to overwrite it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Create default config
python3 config.py "$CONFIG_FILE" << EOF
y
EOF

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Failed to create configuration file."
    exit 1
fi

echo ""
echo "Default configuration created. Now let's customize it..."
echo ""

# Ask for paths
read -p "Enter path to Calypso installation [/eos/user/c/chiw/FASER/Alignment/run/]: " CALYPSO_PATH
read -p "Enter path to Pede installation [/afs/cern.ch/user/c/chiw/public/faser-utils/pede/]: " PEDE_PATH
read -p "Enter path to reconstruction environment script [/afs/cern.ch/user/c/chiw/condor/FASER-Alignment/reco_condor_env.sh]: " RECO_ENV_SCRIPT
read -p "Enter path to Millepede environment script [/afs/cern.ch/user/c/chiw/condor/FASER-Alignment/millepede_condor_env.sh]: " MILLEPEDE_ENV_SCRIPT
read -p "Enter path to working directory [/afs/cern.ch/user/c/chiw/condor/FASER-Alignment/]: " WORK_DIR
read -p "Enter path to EOS output directory [/eos/user/c/chiw/FASER/Alignment/Alignment-Shunliang/]: " EOS_OUTPUT_DIR

# Update config using Python
python3 << EOF
import json

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

# Use user input if provided, otherwise keep the existing value
config['paths']['calypso_install'] = '${CALYPSO_PATH}' or config['paths']['calypso_install']
config['paths']['pede_install'] = '${PEDE_PATH}' or config['paths']['pede_install']
config['paths']['reco_env_script'] = '${RECO_ENV_SCRIPT}' or config['paths']['reco_env_script']
config['paths']['millepede_env_script'] = '${MILLEPEDE_ENV_SCRIPT}' or config['paths']['millepede_env_script']
config['paths']['work_dir'] = '${WORK_DIR}' or config['paths']['work_dir']
config['paths']['eos_output_dir'] = '${EOS_OUTPUT_DIR}' or config['paths']['eos_output_dir']

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)

print("Configuration updated successfully!")
EOF
echo ""
echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
cat "$CONFIG_FILE"
echo ""
echo "=========================================="
echo ""
echo "Setup complete! You can now use the DAGman workflow."
echo ""
echo "Next steps:"
echo "  1. Review and edit $CONFIG_FILE if needed"
echo "  2. Run tests: bash tests/test_integration.sh"
echo "  3. Generate a DAG: python3 dag_manager.py -y 2023 -r 011705 -f 400-403 -i 2"
echo "  4. See USAGE_GUIDE.md for more information"
echo ""
