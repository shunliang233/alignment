#!/usr/bin/env python3
"""
Unit tests for DAG generation.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dag_manager import DAGManager
from config import AlignmentConfig
from RawList import RawList


class TestDAGManager(unittest.TestCase):
    """Test cases for DAGManager class."""
    
    def setUp(self):
        """Create temporary directory and config for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.src_dir = Path(self.temp_dir) / "src"
        self.src_dir.mkdir()
        
        # Create test config file
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        test_config = {
            "paths": {
                "calypso_install": "/test/calypso",
                "pede_install": "/test/pede",
                "reco_env_script": "test_env.sh",
                "millepede_env_script": "test_env.sh"
            },
            "htcondor": {
                "requirements": "(Machine =!= LastRemoteHost)",
                "reco": {
                    "job_flavour": "espresso",
                    "request_cpus": 1,
                    "request_memory": "2 GB",
                    "request_disk": "2 GB",
                    "max_retries": 2
                },
                "millepede": {
                    "job_flavour": "espresso",
                    "request_cpus": 1,
                    "request_memory": "2 GB",
                    "request_disk": "2 GB",
                    "max_retries": 1
                }
            },
            "alignment": {
                "default_iterations": 5
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        self.config = AlignmentConfig(self.config_file)
        self.dag_manager = DAGManager(self.config)
        
        # Create dummy millepede directory structure
        millepede_dir = self.src_dir / "millepede" / "bin"
        millepede_dir.mkdir(parents=True)
        (millepede_dir / "millepede.py").touch()
        
        # Create dummy runAlignment.sh
        (self.src_dir / "runAlignment.sh").touch()
        
        # Create dummy env script
        env_script = Path(self.temp_dir) / "test_env.sh"
        env_script.touch()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_reco_submit_file(self):
        """Test creation of reconstruction submit file."""
        output_dir = Path(self.temp_dir) / "test_output"
        work_dir = Path(self.temp_dir) / "test_work"
        file_str = "00400"
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        submit_file = self.dag_manager.create_reco_submit_file(
            output_dir, 1, "2023", "011705", file_str,
            False, True, self.src_dir, env_path, work_dir
        )
        
        # Check file was created
        self.assertTrue(submit_file.exists())
        
        # Check content
        with open(submit_file, 'r') as f:
            content = f.read()
        
        self.assertIn("executable", content)
        self.assertIn("runAlignment.sh", content)
        self.assertIn("queue", content)
        # Should have exactly one queue statement per file
        self.assertEqual(content.count("queue"), 1)
        # Should contain the specific file number
        self.assertIn("00400", content)
    
    def test_create_millepede_submit_file(self):
        """Test creation of Millepede submit file."""
        output_dir = Path(self.temp_dir) / "test_output"
        work_dir = Path(self.temp_dir) / "test_work"
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        submit_file = self.dag_manager.create_millepede_submit_file(
            output_dir, 1, self.src_dir, env_path, work_dir
        )
        
        # Check file was created
        self.assertTrue(submit_file.exists())
        
        # Check wrapper script was created
        wrapper = submit_file.parent / "run_millepede.sh"
        self.assertTrue(wrapper.exists())
        
        # Check content
        with open(submit_file, 'r') as f:
            content = f.read()
        
        self.assertIn("executable", content)
        self.assertIn("run_millepede.sh", content)
    
    def test_create_dag_file(self):
        """Test creation of complete DAG file."""
        output_dir = Path(self.temp_dir) / "test_output"
        work_dir = Path(self.temp_dir) / "test_work"
        file_list = RawList("400-402")
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        dag_file = self.dag_manager.create_dag_file(
            output_dir, "2023", "011705", file_list, 3,
            False, True, self.src_dir, env_path, env_path, work_dir
        )
        
        # Check file was created
        self.assertTrue(dag_file.exists())
        
        # Check content
        with open(dag_file, 'r') as f:
            content = f.read()
        
        # Check for job definitions - should have individual jobs per file
        for i in range(1, 4):  # 3 iterations
            # Check for individual reco jobs per file
            self.assertIn(f"JOB reco_{i:02d}_00400", content)
            self.assertIn(f"JOB reco_{i:02d}_00401", content)
            self.assertIn(f"JOB millepede_{i:02d}", content)
        
        # Check for dependencies - each reco job should feed into millepede
        self.assertIn("PARENT reco_01_00400 CHILD millepede_01", content)
        self.assertIn("PARENT reco_01_00401 CHILD millepede_01", content)
        self.assertIn("PARENT millepede_01 CHILD reco_02_00400", content)
        self.assertIn("PARENT millepede_01 CHILD reco_02_00401", content)
        
        # Check for retry settings
        self.assertIn("RETRY reco_01_00400", content)
        self.assertIn("RETRY reco_01_00401", content)
        self.assertIn("RETRY millepede_01", content)
    
    def test_setup_job_script(self):
        """Test creation of setup script for iterations."""
        output_dir = Path(self.temp_dir) / "test_output"
        
        # Create setup for iteration 1
        self.dag_manager._create_setup_job_script(output_dir, 1)
        
        # Check directories were created
        iter_dir = output_dir / "iter01"
        self.assertTrue((iter_dir / "1reco").exists())
        self.assertTrue((iter_dir / "2kfalignment").exists())
        self.assertTrue((iter_dir / "3millepede").exists())
        
        # Check inputforalign.txt was created (empty for iter 1)
        input_file = iter_dir / "1reco" / "inputforalign.txt"
        self.assertTrue(input_file.exists())
        self.assertEqual(input_file.stat().st_size, 0)
    
    def test_dag_with_single_file(self):
        """Test DAG generation with single file."""
        output_dir = Path(self.temp_dir) / "test_single"
        work_dir = Path(self.temp_dir) / "test_single_work"
        file_list = RawList("400")
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        dag_file = self.dag_manager.create_dag_file(
            output_dir, "2023", "011705", file_list, 2,
            False, True, self.src_dir, env_path, env_path, work_dir
        )
        
        self.assertTrue(dag_file.exists())
        
        # Check individual reconstruction submit file for file 400 (now in work_dir)
        reco_submit = work_dir / "iter01" / "reco_iter01_00400.sub"
        self.assertTrue(reco_submit.exists())
        with open(reco_submit, 'r') as f:
            content = f.read()
        self.assertEqual(content.count("queue"), 1)
    
    def test_htcondor_settings_in_submit_file(self):
        """Test that HTCondor settings from config are used."""
        output_dir = Path(self.temp_dir) / "test_settings"
        work_dir = Path(self.temp_dir) / "test_settings_work"
        file_str = "00400"
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        submit_file = self.dag_manager.create_reco_submit_file(
            output_dir, 1, "2023", "011705", file_str,
            False, True, self.src_dir, env_path, work_dir
        )
        
        with open(submit_file, 'r') as f:
            content = f.read()
        
        # Check configured values are present
        self.assertIn("espresso", content)  # job_flavour
        self.assertIn("request_cpus = 1", content)
        self.assertIn("max_retries = 2", content)
    
    def test_parallel_reconstruction_jobs_in_dag(self):
        """Test that reconstruction jobs can run in parallel."""
        output_dir = Path(self.temp_dir) / "test_parallel"
        work_dir = Path(self.temp_dir) / "test_parallel_work"
        # Use multiple files to test parallel execution
        # RawList uses Python range semantics: "400-405" gives files 400, 401, 402, 403, 404
        file_list = RawList("400-405")  # 5 files (range is end-exclusive)
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        dag_file = self.dag_manager.create_dag_file(
            output_dir, "2023", "011705", file_list, 2,
            False, True, self.src_dir, env_path, env_path, work_dir
        )
        
        with open(dag_file, 'r') as f:
            content = f.read()
        
        # Verify individual jobs exist for each file in iteration 1
        # range(400, 405) generates 400, 401, 402, 403, 404 (matching RawList output)
        for file_num in range(400, 405):
            job_name = f"reco_01_{file_num:05d}"
            self.assertIn(f"JOB {job_name}", content)
        
        # Verify each reco job is a separate DAG node (has its own submit file in work_dir)
        for file_num in range(400, 405):
            submit_file = work_dir / "iter01" / f"reco_iter01_{file_num:05d}.sub"
            self.assertTrue(submit_file.exists(), 
                          f"Submit file for file {file_num} should exist")
        
        # Verify all reco jobs feed into millepede (allowing parallel execution)
        for file_num in range(400, 405):
            job_name = f"reco_01_{file_num:05d}"
            self.assertIn(f"PARENT {job_name} CHILD millepede_01", content)
        
        # Verify no dependencies between reco jobs (they can run in parallel)
        # Check that reco jobs don't depend on each other
        for file_num1 in range(400, 405):
            for file_num2 in range(400, 405):
                if file_num1 != file_num2:
                    job1 = f"reco_01_{file_num1:05d}"
                    job2 = f"reco_01_{file_num2:05d}"
                    # Should not have dependencies between reco jobs
                    self.assertNotIn(f"PARENT {job1} CHILD {job2}", content)
                    self.assertNotIn(f"PARENT {job2} CHILD {job1}", content)
    
    def test_separate_job_configurations(self):
        """Test that reco and millepede jobs use separate configurations."""
        output_dir = Path(self.temp_dir) / "test_separate_config"
        work_dir = Path(self.temp_dir) / "test_separate_config_work"
        file_str = "00400"
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        # Create reco submit file
        reco_submit = self.dag_manager.create_reco_submit_file(
            output_dir, 1, "2023", "011705", file_str,
            False, True, self.src_dir, env_path, work_dir
        )
        
        with open(reco_submit, 'r') as f:
            reco_content = f.read()
        
        # Check reco job uses reco config
        self.assertIn("espresso", reco_content)  # reco job_flavour from test config
        self.assertIn("request_cpus = 1", reco_content)
        self.assertIn("max_retries = 2", reco_content)
        
        # Create millepede submit file
        millepede_submit = self.dag_manager.create_millepede_submit_file(
            output_dir, 1, self.src_dir, env_path, work_dir
        )
        
        with open(millepede_submit, 'r') as f:
            millepede_content = f.read()
        
        # Check millepede job uses millepede config
        self.assertIn("espresso", millepede_content)  # millepede job_flavour
        self.assertIn("request_cpus = 1", millepede_content)
        self.assertIn("max_retries = 1", millepede_content)
    
    def test_log_paths_use_work_dir(self):
        """Test that log paths are in work_dir to avoid collisions."""
        output_dir = Path(self.temp_dir) / "test_log_paths"
        work_dir = Path(self.temp_dir) / "test_log_paths_work"
        file_str = "00400"
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        # Create reco submit file
        reco_submit = self.dag_manager.create_reco_submit_file(
            output_dir, 1, "2023", "011705", file_str,
            False, True, self.src_dir, env_path, work_dir
        )
        
        with open(reco_submit, 'r') as f:
            reco_content = f.read()
        
        # Log paths should be in work_dir/iter01/logs/
        expected_log_dir = work_dir / "iter01" / "logs"
        self.assertIn(str(expected_log_dir), reco_content)
        
        # Check that log directory was created
        self.assertTrue(expected_log_dir.exists())
        
        # Create millepede submit file
        millepede_submit = self.dag_manager.create_millepede_submit_file(
            output_dir, 1, self.src_dir, env_path, work_dir
        )
        
        with open(millepede_submit, 'r') as f:
            millepede_content = f.read()
        
        # Millepede log paths should also be in work_dir/iter01/logs/
        self.assertIn(str(expected_log_dir), millepede_content)


if __name__ == '__main__':
    unittest.main()
