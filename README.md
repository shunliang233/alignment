# How to do Alignment
This package mainly submit condor reconstruction jobs and do millepede iteratively.

The `main.py` script can do iteration automatically if run as a daemon like:
```bash
nohup python3 auto_iter_test.py -y 2023 -r 011705 -f 450-500 -i 10 &>auto_iter_test.log &
```

The script will find the specified raw files in `/eos/experiment/faser/raw/` and repeat the iteration for `10` times as specified by `-i` operation.


## Source environment
```bash
#!/bin/bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase 
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
asetup --input=calypso/asetup.faser Athena,24.0.41
source /eos/home-s/shunlian/Alignment/install/setup.sh
```

## Run `main.py`

### Basic usage
```bash
python main.py --year 2023 --run 011705 --file 400
# Or use short options
python main.py -y 2023 -r 11705 -f 400
```

### Batch processing multiple rawfiles
```bash
# Use range format start-end
python main.py --year 2023 --run 011705 --file 400-450

# Use range format start:end
python main.py --year 2023 --run 011705 --file 400:450

# Short option form
python main.py -y 2023 -r 11705 -f 400-450
```

### Parameter description
- `--year, -y`: Year (required, e.g.: 2022-2025)
- `--run, -r`: Run number (required, e.g.: 011705, will be zero-padded to 6 digits)
- `--file, -f`: Single raw file number (e.g.: 400) or range (e.g.: 400-450 or 400:450)
- `--fourst`: Run 4-station mode (optional, off by default)
- `--threest`: Run 3-station mode (optional, on by default)

## File description
- Run the main program with `main.py`
- The class for processing the `--file` parameter is in `RawList.py`
- Generates the `submit_unbiased.sub` file and submits it to Condor with `-spool`
- Submission information is stored in `main.log`
- Each Condor node independently runs the `runAlignment.sh` script to process each `.raw` file
- The script includes `aligndb_copy.sh` parameter configuration and the `faser_reco_alignment.py` reconstruction algorithm
- The reconstructed `.root` files are stored in the `../2root_file` directory
- After completion, use `condor_transfer_data ${Cluster}` to retrieve log files

### Log files
After job execution, log files are saved in the `logs/` directory:
- `job_$(Cluster)_$(Process).out` - Standard output
- `job_$(Cluster)_$(Process).err` - Error output  
- `job_$(Cluster)_$(Process).log` - Condor log