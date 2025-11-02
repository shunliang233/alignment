# Auto Iteration by Python Script
This package mainly submit condor reconstruction jobs and do millepede iteratively.

The `auto_iter.py` script can do iteration automatically if run as a daemon like:
```bash
nohup python3 auto_iter.py -y 2023 -r 011705 -f 450-500 -i 10 &>>auto_iter.log &
```

The script will find the specified raw files in `/eos/experiment/faser/raw/` and repeat the iteration for `10` times as specified by `-i` operation.

## FASER Alignment Process

The FASER alignment process uses HTCondor for automated parallel processing with iterative refinement. The following diagram illustrates the complete workflow:

```mermaid
flowchart TD
    Start([Start: auto_iter.py]) --> Init[Initialize Parameters<br/>Year, Run, Files, Iterations]
    Init --> CreateDirs[Create Work Directory<br/>Y{year}_R{run}_F{files}]
    CreateDirs --> IterLoop{Iteration Loop<br/>i = 1 to N}
    
    IterLoop -->|For each iteration| IterSetup[Setup Iteration Directory<br/>iter{i}/1reco, 2kfalignment, 3millepede]
    
    IterSetup --> PrepAlign{First Iteration?}
    PrepAlign -->|Yes| CreateEmpty[Create Empty<br/>inputforalign.txt]
    PrepAlign -->|No| CopyAlign[Copy inputforalign.txt<br/>from previous iteration]
    
    CreateEmpty --> PrepCondor[Prepare HTCondor Submit File]
    CopyAlign --> PrepCondor
    
    PrepCondor --> SubmitJobs[Submit HTCondor Jobs<br/>condor_submit -spool]
    
    SubmitJobs --> ParallelReco[Parallel Reconstruction Jobs<br/>One per raw file]
    
    ParallelReco --> RecoJob1[HTCondor Job 1:<br/>runAlignment.sh]
    ParallelReco --> RecoJob2[HTCondor Job 2:<br/>runAlignment.sh]
    ParallelReco --> RecoJobN[HTCondor Job N:<br/>runAlignment.sh]
    
    RecoJob1 --> SetupEnv1[Setup ATLAS Environment]
    RecoJob2 --> SetupEnv2[Setup ATLAS Environment]
    RecoJobN --> SetupEnvN[Setup ATLAS Environment]
    
    SetupEnv1 --> SetupDB1[Setup Alignment Database<br/>aligndb_copy.sh]
    SetupEnv2 --> SetupDB2[Setup Alignment Database<br/>aligndb_copy.sh]
    SetupEnvN --> SetupDBN[Setup Alignment Database<br/>aligndb_copy.sh]
    
    SetupDB1 --> RunReco1[Run Reconstruction<br/>faser_reco_alignment.py]
    SetupDB2 --> RunReco2[Run Reconstruction<br/>faser_reco_alignment.py]
    SetupDBN --> RunRecoN[Run Reconstruction<br/>faser_reco_alignment.py]
    
    RunReco1 --> Output1[Output: kfalignment_*.root]
    RunReco2 --> Output2[Output: kfalignment_*.root]
    RunRecoN --> OutputN[Output: kfalignment_*.root]
    
    Output1 --> Monitor[Monitor HTCondor Jobs<br/>condor_q every 5 minutes]
    Output2 --> Monitor
    OutputN --> Monitor
    
    Monitor --> CheckStatus{All Jobs<br/>Complete?}
    CheckStatus -->|No: idle or running| Monitor
    CheckStatus -->|Hold| ErrorHandle[Error: Jobs on Hold]
    CheckStatus -->|Yes: all done| CollectResults[Collect kfalignment files<br/>in 2kfalignment/]
    
    ErrorHandle --> End([Error Exit])
    
    CollectResults --> RunMille[Run Millepede Algorithm<br/>millepede/bin/millepede.py]
    
    RunMille --> GenConstants[Generate New Alignment Constants<br/>Update inputforalign.txt]
    
    GenConstants --> CheckIter{More<br/>Iterations?}
    CheckIter -->|Yes| IterLoop
    CheckIter -->|No| Complete([Complete: Final Alignment Constants])
    
    style Start fill:#90EE90
    style Complete fill:#90EE90
    style End fill:#FFB6C1
    style ParallelReco fill:#FFE4B5
    style RecoJob1 fill:#FFE4B5
    style RecoJob2 fill:#FFE4B5
    style RecoJobN fill:#FFE4B5
    style RunMille fill:#87CEEB
    style Monitor fill:#DDA0DD
```

### Key Components:

1. **auto_iter.py**: Main orchestration script that manages the iterative alignment process
2. **HTCondor Jobs**: Parallel processing of raw data files using HTCondor job submission and monitoring
3. **runAlignment.sh**: Shell script executed on each HTCondor node for individual raw file processing
4. **faser_reco_alignment.py**: FASER reconstruction algorithm based on ATLAS Athena framework
5. **Millepede**: Alignment algorithm that processes all kfalignment data to generate new alignment constants
6. **Iteration Loop**: The process repeats N times, with each iteration using improved alignment constants

### Data Flow:

- **Input**: Raw data files from `/eos/experiment/faser/raw/{year}/{run}/`
- **Intermediate**: kfalignment ROOT files in `2kfalignment/` directory
- **Output**: Final alignment constants in `inputforalign.txt` after all iterations

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