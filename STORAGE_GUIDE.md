# Storage Management Guide for FASER Alignment

This guide explains how to configure and use the HTCondor DAGman framework with proper AFS and EOS storage management.

## Storage Architecture

### AFS vs EOS

**AFS (Andrew File System):**
- Small quota (typically a few GB)
- Good for: Code, configuration files, submit files, DAG files
- Location: `/afs/cern.ch/user/`
- Use for: Job submission and workflow management

**EOS (CERN's disk storage):**
- Large quota (hundreds of GB to TB)
- Good for: Large data files, intermediate results, output files
- Location: `/eos/experiment/faser/` or `/eos/user/`
- Use for: Root files, alignment output, reconstruction results

## Configuration

### Basic Setup

Edit `config.json` to configure storage paths:

```json
{
  "paths": {
    "calypso_install": "/afs/cern.ch/user/y/yourusername/calypso/install",
    "pede_install": "/afs/cern.ch/user/y/yourusername/pede",
    "env_script": "reco_condor_env.sh",
    "work_dir": "/afs/cern.ch/user/y/yourusername/alignment-work",
    "eos_output_dir": "/eos/user/y/yourusername/faser-alignment-output"
  },
  "storage": {
    "use_eos_for_output": true,
    "keep_intermediate_root_files": true,
    "keep_alignment_constants": true,
    "cleanup_reco_temp_files": true
  }
}
```

### Storage Options Explained

**`use_eos_for_output`** (boolean, default: true)
- When `true`: Large output files (root files, xAOD files) are written to EOS
- When `false`: All output written to work_dir (use only if you have sufficient AFS space)

**`keep_intermediate_root_files`** (boolean, default: true)
- When `true`: Root files from all iterations are kept
- When `false`: Only final iteration root files are kept (saves space)

**`keep_alignment_constants`** (boolean, default: true)
- Always recommended to keep these (small files, crucial for analysis)
- Contains alignment parameters from each iteration

**`cleanup_reco_temp_files`** (boolean, default: true)
- When `true`: Temporary reconstruction files are removed after iteration completes
- When `false`: All temporary files are kept (useful for debugging)

**`cleanup_database_files`** (boolean, default: true)
- When `true`: Database files (ALLP200.db, ~100MB each) are automatically removed after each reconstruction job completes
- When `false`: Database files are kept (can quickly fill disk quota with 50+ files)
- **Recommended**: Keep enabled to avoid disk quota issues
- Uses HTCondor POST scripts to clean up the `data/sqlite200/` directory for each job

## Directory Structure

### With EOS Storage (Recommended)

```
AFS: /afs/cern.ch/user/y/yourusername/alignment-work/
├── Y2023_R011705_F400-450/
│   ├── alignment.dag                # DAG definition
│   ├── alignment.dag.dagman.out     # DAGman logs
│   ├── iter01/
│   │   ├── 1reco/
│   │   │   ├── reco.sub            # Submit file
│   │   │   ├── inputforalign.txt   # Alignment constants (small)
│   │   │   └── logs/               # Job logs
│   │   └── 3millepede/
│   │       ├── millepede.sub
│   │       └── millepede.out
│   └── iter02/
│       └── ...

EOS: /eos/user/y/yourusername/faser-alignment-output/
├── Y2023_R011705_F400-450/
│   ├── iter01/
│   │   ├── 2kfalignment/           # Root files (large)
│   │   │   ├── kfalignment_*.root
│   │   │   └── xAOD_*.root
│   │   └── 3millepede/
│   │       └── millepede-result.txt
│   └── iter02/
│       └── ...
```

## Performance Considerations

### Executable Location

**Question**: Should executables (Calypso, Pede) be on AFS or EOS?

**Recommendation**:
- **Calypso**: Keep on **AFS**
  - Compilation time: ~1 hour (not feasible on compute nodes)
  - Size: ~230 MB (manageable on AFS)
  - Access: Faster from AFS, used by all jobs
  
- **Pede**: Can be on **AFS** or **EOS**
  - Compilation time: ~2 min (fast enough for local compilation)
  - Size: ~60 MB (small enough for AFS)
  - Recommendation: Keep on AFS for better performance

**Performance Impact**:
- Reading executables from EOS adds ~1-2 seconds per job startup
- For short jobs (<5 min), this is significant overhead (~2-5%)
- For long jobs (>1 hour), impact is negligible (<0.1%)

### Best Practices

1. **Submit from AFS**:
   ```bash
   cd /afs/cern.ch/user/y/yourusername/alignment-work
   python3 dag_manager.py -y 2023 -r 011705 -f 400-450 -i 10 --submit
   ```

2. **Configure EOS for output**:
   - Set `eos_output_dir` in config.json
   - Large files automatically written to EOS
   - Symlinks created in AFS work directory for easy access

3. **Monitor disk usage**:
   ```bash
   # Check AFS quota
   fs quota ~
   
   # Check EOS usage
   eos quota /eos/user/y/yourusername
   ```

4. **Clean up after completion**:
   ```bash
   # Remove temporary files (if not auto-cleaned)
   python3 cleanup_workflow.py Y2023_R011705_F400-450
   ```

## File Size Estimates

Typical file sizes per iteration (50 raw files):

| File Type | Location | Size per Iteration | Keep? |
|-----------|----------|-------------------|-------|
| Raw files | EOS (input) | ~5 GB | Input only |
| xAOD files | EOS | ~2 GB | Optional |
| Root files (kfalignment) | EOS | ~500 MB | Yes |
| Database files (ALLP200.db) | AFS (temp) | ~5 GB (100MB × 50) | **Auto-cleaned** |
| Alignment constants | AFS | ~50 KB | Yes |
| Job logs | AFS | ~10 MB | Yes |
| Temporary files | Temp | ~200 MB | No |

**Total per iteration**: ~2.5 GB on EOS, ~10 MB on AFS (with cleanup enabled)

**For 10 iterations**: ~25 GB on EOS, ~100 MB on AFS

**Note**: Database files are automatically cleaned after each job completes (when `cleanup_database_files: true`). Without cleanup, they would consume ~5GB per iteration on AFS!

## Troubleshooting

### Issue: AFS quota exceeded due to database files

**Symptoms**: 
- Jobs fail with "Disk quota exceeded"
- Large `data/sqlite200/ALLP200.db` files (~100MB each) in reconstruction directories
- Disk usage grows by ~5GB per iteration (50 files × 100MB)

**Cause**: Database files are copied to each job's working directory and not cleaned up automatically.

**Solution**:
1. Enable automatic cleanup (default in config.json):
   ```json
   {
     "storage": {
       "cleanup_database_files": true
     }
   }
   ```

2. Verify cleanup scripts are added to DAG:
   ```bash
   grep "SCRIPT POST" Y2023_R011705_F400-450/alignment.dag
   ```

3. Manual cleanup (if needed):
   ```bash
   # Remove database files from all reconstruction directories
   find Y2023_R011705_F400-450 -type d -name "data" -path "*/1reco/*" -exec rm -rf {} +
   ```

### Issue: AFS quota exceeded (general)

**Symptoms**: Jobs fail with "Disk quota exceeded"

**Solution**:
1. Verify EOS is configured:
   ```bash
   grep eos_output_dir config.json
   ```
2. Enable all cleanup options:
   ```json
   "cleanup_reco_temp_files": true
   ```
3. Remove old workflows:
   ```bash
   rm -rf Y2023_R011705_F400-450/
   ```

### Issue: EOS write failures

**Symptoms**: Jobs complete but output files missing

**Solution**:
1. Check EOS quota:
   ```bash
   eos quota /eos/user/y/yourusername
   ```
2. Verify EOS directory exists:
   ```bash
   ls -la /eos/user/y/yourusername/faser-alignment-output/
   ```
3. Check permissions:
   ```bash
   eos chmod 755 /eos/user/y/yourusername/faser-alignment-output/
   ```

### Issue: Slow job startup

**Symptoms**: Jobs take long to start, spend time in "I" state

**Possible causes**:
1. Executables on EOS (slow read)
2. Large input files transferred via HTCondor
3. Environment setup from EOS

**Solutions**:
1. Keep executables on AFS
2. Use EOS paths directly (not via file transfer)
3. Optimize environment script

## Migration from Legacy Setup

If migrating from `auto_iter.py` or `main.py`:

**Old structure** (everything in one place):
```
/eos/experiment/faser/alignment/Y2023_R011705/
├── iter01/
│   ├── 1reco/
│   ├── 2kfalignment/
│   └── 3millepede/
```

**New structure** (AFS + EOS):
```
AFS: Submit files, DAG, logs
EOS: Root files, large outputs
```

**Migration command**:
```bash
python3 migrate_storage.py --old-dir /eos/.../Y2023_R011705 \
                           --afs-dir /afs/.../alignment-work \
                           --eos-dir /eos/.../output
```

## Advanced Configuration

### Custom Storage Rules

Create `storage_rules.json` for fine-grained control:

```json
{
  "file_patterns": {
    "*.root": "eos",
    "*.xAOD": "eos",
    "*.txt": "afs",
    "*.log": "afs",
    "*.sub": "afs"
  },
  "cleanup_patterns": [
    "*/temp/*",
    "*/*.tmp"
  ],
  "keep_patterns": [
    "*/inputforalign.txt",
    "*/millepede.out",
    "*/kfalignment_*.root"
  ]
}
```

### Using Symbolic Links

To access EOS files from AFS work directory:

```bash
# Automatic symlink creation (enabled by default)
ln -s /eos/user/y/yourusername/output/Y2023.../iter01/2kfalignment \
      /afs/.../work/Y2023.../iter01/2kfalignment
```

Benefits:
- Navigate from AFS work directory
- Access large files without copying
- Transparent to analysis scripts

## Summary

**Recommended Setup**:
1. ✅ Submit jobs from AFS (use `work_dir` on AFS)
2. ✅ Store executables (Calypso, Pede) on AFS for performance
3. ✅ Store large outputs (root files) on EOS
4. ✅ Keep alignment constants and logs on AFS
5. ✅ Enable automatic cleanup of temporary files
6. ✅ Monitor both AFS and EOS quotas

This setup provides optimal performance while managing storage efficiently.
