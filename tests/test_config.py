#!/usr/bin/env python3
"""
Unit tests for configuration management.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import AlignmentConfig, create_default_config


class TestAlignmentConfig(unittest.TestCase):
    """Test cases for AlignmentConfig class."""
    
    def setUp(self):
        """Create temporary config file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test configuration
        self.test_config = {
            "paths": {
                "calypso_install": "/test/calypso",
                "pede_install": "/test/pede",
                "reco_env_script": "test_reco_env.sh",
                "millepede_env_script": "test_millepede_env.sh"
            },
            "htcondor": {
                "requirements": "(Machine =!= LastRemoteHost)",
                "reco": {
                    "job_flavour": "microcentury",
                    "request_cpus": 2,
                    "request_memory": "4 GB",
                    "request_disk": "4 GB",
                    "max_retries": 5
                },
                "millepede": {
                    "job_flavour": "espresso",
                    "request_cpus": 1,
                    "request_memory": "2 GB",
                    "request_disk": "2 GB",
                    "max_retries": 2
                }
            },
            "alignment": {
                "default_iterations": 15
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_load_config(self):
        """Test loading configuration from file."""
        config = AlignmentConfig(self.config_file)
        self.assertEqual(config.get('paths.calypso_install'), '/test/calypso')
        self.assertEqual(config.get('htcondor.reco.request_cpus'), 2)
    
    def test_missing_config_file(self):
        """Test error handling for missing config file."""
        with self.assertRaises(FileNotFoundError):
            AlignmentConfig('/nonexistent/config.json')
    
    def test_invalid_json(self):
        """Test error handling for invalid JSON."""
        invalid_config = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_config, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(ValueError):
            AlignmentConfig(invalid_config)
    
    def test_get_with_default(self):
        """Test getting configuration with default value."""
        config = AlignmentConfig(self.config_file)
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')
        self.assertIsNone(config.get('nonexistent.key'))
    
    def test_set_value(self):
        """Test setting configuration values."""
        config = AlignmentConfig(self.config_file)
        config.set('paths.new_path', '/new/path')
        self.assertEqual(config.get('paths.new_path'), '/new/path')
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config = AlignmentConfig(self.config_file)
        config.set('test.value', 'test_data')
        config.save()
        
        # Load again and verify
        config2 = AlignmentConfig(self.config_file)
        self.assertEqual(config2.get('test.value'), 'test_data')
    
    def test_properties(self):
        """Test convenience properties."""
        config = AlignmentConfig(self.config_file)
        self.assertEqual(config.calypso_path, '/test/calypso')
        self.assertEqual(config.pede_path, '/test/pede')
        self.assertEqual(config.reco_env_script, 'test_reco_env.sh')
        self.assertEqual(config.millepede_env_script, 'test_millepede_env.sh')
    
    def test_missing_required_path(self):
        """Test error when required path is not configured."""
        # Create config without required paths
        empty_config = os.path.join(self.temp_dir, "empty.json")
        with open(empty_config, 'w') as f:
            json.dump({"paths": {}}, f)
        
        config = AlignmentConfig(empty_config)
        with self.assertRaises(ValueError):
            _ = config.calypso_path


class TestCreateDefaultConfig(unittest.TestCase):
    """Test cases for create_default_config function."""
    
    def setUp(self):
        """Create temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_default_config(self):
        """Test creating default configuration file."""
        config_path = os.path.join(self.temp_dir, "default_config.json")
        create_default_config(config_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(config_path))
        
        # Verify it's valid JSON with expected structure
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertIn('paths', config)
        self.assertIn('htcondor', config)
        self.assertIn('alignment', config)
        self.assertIn('calypso_install', config['paths'])


if __name__ == '__main__':
    unittest.main()
