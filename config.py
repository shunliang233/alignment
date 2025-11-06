#!/usr/bin/env python3
"""
Configuration management for FASER alignment scripts.

This module handles loading and validation of configuration from JSON files,
providing centralized path management for Calypso, Pede, and other dependencies.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class AlignmentConfig:
    """Manages configuration for FASER alignment scripts."""
    
    DEFAULT_CONFIG_FILE = "config.json"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to JSON configuration file. If None, uses default.
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: Dict[str, Any] = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create {self.config_file} or specify a valid config file."
            )
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., "paths.calypso_install")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    # Convenience properties for commonly used paths
    
    @property
    def calypso_path(self) -> str:
        """Get Calypso installation path."""
        path = self.get('paths.calypso_install', '')
        if not path:
            raise ValueError(
                "Calypso installation path not configured. "
                "Please set 'paths.calypso_install' in config.json"
            )
        return path
    
    @property
    def pede_path(self) -> str:
        """Get Pede installation path."""
        path = self.get('paths.pede_install', '')
        if not path:
            raise ValueError(
                "Pede installation path not configured. "
                "Please set 'paths.pede_install' in config.json"
            )
        return path
    
    @property
    def reco_env_script(self) -> str:
        """Get environment script path."""
        return self.get('paths.reco_env_script', '')

    @property
    def millepede_env_script(self) -> str:
        """Get Millepede environment script path."""
        return self.get('paths.millepede_env_script', '')
    
    @property
    def work_dir(self) -> Optional[str]:
        """Get work directory path (typically on AFS)."""
        return self.get('paths.work_dir', '')
    
    @property
    def eos_output_dir(self) -> Optional[str]:
        """Get EOS output directory path."""
        return self.get('paths.eos_output_dir', '')
    
    @property
    def use_eos_storage(self) -> bool:
        """Check if EOS storage is enabled for output."""
        return self.get('storage.use_eos_for_output', True)
    
    def validate_paths(self) -> None:
        """
        Validate that configured paths exist.
        
        Raises:
            FileNotFoundError: If required paths don't exist
        """
        calypso = self.get('paths.calypso_install')
        if calypso and not Path(calypso).exists():
            raise FileNotFoundError(f"Calypso installation not found: {calypso}")
        
        pede = self.get('paths.pede_install')
        if pede and not Path(pede).exists():
            raise FileNotFoundError(f"Pede installation not found: {pede}")


def create_default_config(output_path: str = "config.json") -> None:
    """
    Create a default configuration file.
    
    Args:
        output_path: Path where to create the configuration file
    """
    default_config = {
        "paths": {
            "calypso_install": "",
            "pede_install": "",
            "reco_env_script": "",
            "millepede_env_script": "",
            "work_dir": "",
            "eos_output_dir": ""
        },
        "htcondor": {
            "job_flavour": "longlunch",
            "request_cpus": 1,
            "request_memory": "2GB",
            "request_disk": "4GB",
            "max_retries": 3,
            "requirements": "(Machine =!= LastRemoteHost) && (OpSysAndVer =?= \"AlmaLinux9\")"
        },
        "alignment": {
            "default_iterations": 10,
            "polling_interval_seconds": 300
        },
        "storage": {
            "use_eos_for_output": True,
            "keep_intermediate_root_files": True,
            "keep_alignment_constants": True,
            "cleanup_reco_temp_files": True
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Created default configuration file: {output_path}")
    print("Please edit this file to set your installation paths.")
    print("\nKey configuration:")
    print("  - paths.work_dir: AFS directory for job submission")
    print("  - paths.eos_output_dir: EOS directory for large output files")
    print("  - storage.use_eos_for_output: Enable EOS storage (recommended)")
    print("\nSee STORAGE_GUIDE.md for detailed storage configuration.")


if __name__ == "__main__":
    # When run as a script, create a default config file
    import sys
    
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = "config.json"
    
    if Path(output_path).exists():
        response = input(f"{output_path} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    create_default_config(output_path)
