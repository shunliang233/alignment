# FASER Alignment DAGman Usage Guide

This guide provides step-by-step instructions for using the HTCondor DAGman-based alignment workflow.

## Quick Start

### 1. Initial Setup

First, configure your environment:

```bash
# Clone the repository (if not already done)
git clone https://github.com/Eric100911/faser-alignment-script.git
cd faser-alignment-script

# Create configuration file
python3 config.py

# Edit config.json with your paths
nano config.json
```

Example `config.json`:

```json
{
  "paths": {
    "calypso_install": "/afs/cern.ch/user/y/yourusername/calypso/install",
    "pede_install": "/afs/cern.ch/user/y/yourusername/pede",
    "env_script": "reco_condor_env.sh"
  },
  "htcondor": {
    "job_flavour": "longlunch",
    "request_cpus": 1,
    "max_retries": 3,
    "requirements": "(Machine =!= LastRemoteHost) && (OpSysAndVer =?= \"AlmaLinux9\")"
  },
  "alignment": {
    "default_iterations": 10,
    "polling_interval_seconds": 300
  }
}
```

### 2. Generate and Submit DAG

**For a small test run (2 iterations, 3 files):**

```bash
python3 dag_manager.py \
  --year 2023 \
  --run 011705 \
  --files 400-403 \
  --iterations 2 \
  --submit
```

**For a production run (10 iterations, 50 files):**

```bash
python3 dag_manager.py \
  --year 2023 \
  --run 011705 \
  --files 400-450 \
  --iterations 10 \
  --submit
```

**With 4-station mode:**

```bash
python3 dag_manager.py \
  -y 2023 \
  -r 011705 \
  -f 400-450 \
  -i 10 \
  --fourst \
  --submit
```

### 3. Monitor Progress

```bash
# Check overall status
condor_q

# View DAG structure and status
condor_q -dag

# Check specific DAG
condor_q -nobatch

# Monitor DAGman log in real-time
tail -f Y2023_R011705_F400-450/alignment.dag.dagman.out

# Check job history
condor_history <username>
```

### 4. Handle Issues

**If some jobs fail:**

HTCondor will automatically retry failed jobs according to the configured policy. Check the logs:

```bash
cd Y2023_R011705_F400-450/iter01/1reco/logs/
less reco_<Process>.err
```

**If the DAG fails:**

HTCondor creates rescue DAGs automatically:

```bash
# Submit the rescue DAG to continue from where it failed
condor_submit_dag Y2023_R011705_F400-450/alignment.dag.rescue001
```

**To remove a running DAG:**

```bash
# Find the DAGman job ID
condor_q

# Remove it
condor_rm <DAGman_job_id>
```

## Advanced Usage

### Custom Configuration File

```bash
python3 dag_manager.py \
  -y 2023 \
  -r 011705 \
  -f 400-450 \
  -i 10 \
  --config my_custom_config.json \
  --submit
```

### Generate DAG Without Submitting

Useful for reviewing the DAG before submission:

```bash
python3 dag_manager.py \
  -y 2023 \
  -r 011705 \
  -f 400-450 \
  -i 10

# Review the generated DAG
cat Y2023_R011705_F400-450/alignment.dag

# Submit manually when ready
condor_submit_dag Y2023_R011705_F400-450/alignment.dag
```

### Single File Processing

```bash
python3 dag_manager.py \
  -y 2023 \
  -r 011705 \
  -f 400 \
  -i 5 \
  --submit
```

### Different File Range Formats

All of these are equivalent:

```bash
# Using dash
python3 dag_manager.py -y 2023 -r 011705 -f 400-450 -i 10

# Using colon
python3 dag_manager.py -y 2023 -r 011705 -f 400:450 -i 10
```

## Understanding the Output

### Directory Structure

After submission, you'll have:

```
Y2023_R011705_F400-450/
├── alignment.dag              # Main DAG file
├── alignment.dag.dagman.out   # DAGman execution log
├── alignment.dag.dagman.log   # DAGman status log
├── alignment.dag.lib.out      # DAGman library output
├── alignment.dag.lib.err      # DAGman library errors
├── iter01/
│   ├── pre_reco.sh           # PRE script (for iter > 1)
│   ├── 1reco/
│   │   ├── reco.sub          # Reconstruction submit file
│   │   ├── inputforalign.txt # Alignment constants
│   │   ├── runAlignment.sh   # Copied executable
│   │   ├── logs/             # Job logs
│   │   │   ├── reco_0.out
│   │   │   ├── reco_0.err
│   │   │   └── reco_0.log
│   │   └── <run>/<file>/     # Per-file work directories
│   ├── 2kfalignment/         # KF alignment output
│   │   └── kfalignment_*.root
│   └── 3millepede/
│       ├── millepede.sub     # Millepede submit file
│       ├── run_millepede.sh  # Millepede wrapper
│       ├── millepede.out
│       ├── millepede.err
│       └── millepede.log
├── iter02/
│   └── ...
└── ...
```

### Log Files to Check

1. **DAGman logs**: `alignment.dag.dagman.out` - Shows overall workflow progress
2. **Reconstruction logs**: `iter*/1reco/logs/reco_*.err` - Individual job errors
3. **Millepede logs**: `iter*/3millepede/millepede.out` - Alignment computation output

## Monitoring Examples

### Check How Many Jobs Are Running

```bash
condor_q -run | grep <username>
```

### Check How Many Jobs Are Idle

```bash
condor_q -idle | grep <username>
```

### Check Completed Jobs

```bash
condor_history <username> -limit 10
```

### See DAG Progress

```bash
# This shows parent-child relationships
condor_q -dag

# Example output:
# ID      OWNER      DAG_NodeName          STATUS
# 12345.0 username   reco_01              DONE
# 12345.1 username   millepede_01         DONE
# 12345.2 username   reco_02              RUNNING
# 12345.3 username   millepede_02         IDLE
```

## Troubleshooting

### Problem: Environment script not found

**Error**: `FileNotFoundError: Environment script not found: reco_condor_env.sh`

**Solution**: The environment script will be created automatically if you provide the `--calypso_path` when first running `main.py`, or you can create it manually.

### Problem: Config file not found

**Error**: `FileNotFoundError: Configuration file not found: config.json`

**Solution**: 
```bash
python3 config.py
# Edit the generated config.json with your paths
```

### Problem: Jobs stuck in idle state

**Possible causes**:
1. Requirements not met (e.g., AlmaLinux9 not available)
2. Resource limits reached
3. Accounting group issues

**Check**:
```bash
condor_q -better-analyze <job_id>
```

### Problem: Jobs fail with "Cannot find raw file"

**Solution**: Make sure the raw data files exist in `/eos/experiment/faser/raw/`

```bash
ls /eos/experiment/faser/raw/2023/011705/Faser-Physics-011705-00400.raw
```

### Problem: Millepede fails

**Check logs**:
```bash
cd Y2023_R011705_F400-450/iter01/3millepede/
cat millepede.err
cat millepede.out
```

**Common issues**:
- Missing pede in PATH
- No root files from reconstruction
- Insufficient memory

## Performance Tips

1. **Choose appropriate job flavour**:
   - `espresso`: < 20 minutes (for testing)
   - `microcentury`: < 1 hour
   - `longlunch`: < 2 hours (default)
   - `workday`: < 8 hours
   - `tomorrow`: < 1 day

2. **Optimize file ranges**:
   - Start with small ranges for testing (3-5 files)
   - Scale up once validated (50-100 files)

3. **Monitor resource usage**:
   ```bash
   condor_q -l <job_id> | grep -E "Memory|Cpus|Disk"
   ```

## Migration from Daemon Approach

If you're migrating from the old `auto_iter.py` daemon approach:

**Old command**:
```bash
nohup python3 auto_iter.py -y 2023 -r 011705 -f 450-500 -i 10 &>>auto_iter.log &
```

**New command**:
```bash
python3 dag_manager.py -y 2023 -r 011705 -f 450-500 -i 10 --submit
```

**Benefits**:
- ✅ No need for `nohup` or background processes
- ✅ Automatic job dependency management
- ✅ Built-in retry logic
- ✅ Better monitoring with standard HTCondor tools
- ✅ Officially supported on lxplus

## Getting Help

For issues or questions:

1. Check the logs (DAGman and job-specific)
2. Review this guide and README.md
3. Run the test suite: `bash tests/test_integration.sh`
4. Check HTCondor documentation: https://htcondor.readthedocs.io/
5. Contact the development team

## Running Tests

Before production use, verify everything works:

```bash
# Run unit tests
python3 tests/test_config.py -v
python3 tests/test_dag_generation.py -v

# Run integration test
bash tests/test_integration.sh
```

All tests should pass before proceeding to production workflows.
