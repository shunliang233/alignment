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
                "env_script": "test_env.sh"
            },
            "htcondor": {
                "job_flavour": "espresso",
                "request_cpus": 1,
                "max_retries": 2,
                "requirements": "(Machine =!= LastRemoteHost)"
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
        file_list = RawList("400-402")
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        submit_file = self.dag_manager.create_reco_submit_file(
            output_dir, "2023", "011705", file_list, 1,
            False, True, self.src_dir, env_path
        )
        
        # Check file was created
        self.assertTrue(submit_file.exists())
        
        # Check content
        with open(submit_file, 'r') as f:
            content = f.read()
        
        self.assertIn("executable", content)
        self.assertIn("runAlignment.sh", content)
        self.assertIn("queue", content)
        # Should have entries for files 400 and 401
        self.assertEqual(content.count("queue"), 2)
    
    def test_create_millepede_submit_file(self):
        """Test creation of Millepede submit file."""
        output_dir = Path(self.temp_dir) / "test_output"
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        submit_file = self.dag_manager.create_millepede_submit_file(
            output_dir, 1, self.src_dir, env_path
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
        file_list = RawList("400-402")
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        dag_file = self.dag_manager.create_dag_file(
            output_dir, "2023", "011705", file_list, 3,
            False, True, self.src_dir, env_path
        )
        
        # Check file was created
        self.assertTrue(dag_file.exists())
        
        # Check content
        with open(dag_file, 'r') as f:
            content = f.read()
        
        # Check for job definitions
        for i in range(1, 4):  # 3 iterations
            self.assertIn(f"JOB reco_{i:02d}", content)
            self.assertIn(f"JOB millepede_{i:02d}", content)
        
        # Check for dependencies
        self.assertIn("PARENT reco_01 CHILD millepede_01", content)
        self.assertIn("PARENT millepede_01 CHILD reco_02", content)
        
        # Check for retry settings
        self.assertIn("RETRY reco_01", content)
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
        file_list = RawList("400")
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        dag_file = self.dag_manager.create_dag_file(
            output_dir, "2023", "011705", file_list, 2,
            False, True, self.src_dir, env_path
        )
        
        self.assertTrue(dag_file.exists())
        
        # Check reconstruction submit file has only one queue statement
        reco_submit = output_dir / "iter01" / "1reco" / "reco.sub"
        with open(reco_submit, 'r') as f:
            content = f.read()
        self.assertEqual(content.count("queue"), 1)
    
    def test_htcondor_settings_in_submit_file(self):
        """Test that HTCondor settings from config are used."""
        output_dir = Path(self.temp_dir) / "test_settings"
        file_list = RawList("400")
        env_path = Path(self.temp_dir) / "test_env.sh"
        
        submit_file = self.dag_manager.create_reco_submit_file(
            output_dir, "2023", "011705", file_list, 1,
            False, True, self.src_dir, env_path
        )
        
        with open(submit_file, 'r') as f:
            content = f.read()
        
        # Check configured values are present
        self.assertIn("espresso", content)  # job_flavour
        self.assertIn("request_cpus = 1", content)
        self.assertIn("max_retries = 2", content)


if __name__ == '__main__':
    unittest.main()
