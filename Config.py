#!/usr/bin/env python3
"""
Configuration management for FASER alignment scripts.

This module handles loading and validation of configuration from JSON files,
providing centralized path management for Calypso, Pede, and other dependencies.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

class ConfigNode:
    """A dict node in the configuration tree."""
    def __init__(self, data: dict[str, Any]):
        if not isinstance(data, dict):
            raise TypeError(f"ConfigNode expects a dict, got {type(data).__name__}")
        self._data = data

    def __getattr__(self, key: str):
        if key in self._data:
            value = self._data[key]
            if isinstance(value, dict):
                return ConfigNode(value)
            else:
                return value
        raise AttributeError(f"No such config key: {key}")

class Config:
    """Basic config manager from JSON file."""
    
    def __init__(self, config_file: Path):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to JSON configuration file.
        """
        self.config_file: Path = config_file
        self.config: dict[str, Any] = self._load_config()
        
    def _load_config(self) -> dict[str, Any]:
        """Load configuration from JSON file."""
        config_path = self.config_file
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}")
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def __getattr__(self, key: str):
        """Allow attribute-style access to config keys"""
        if key in self.config:
            value = self.config[key]
            if isinstance(value, dict):
                return ConfigNode(value)
            else:
                return value
        raise AttributeError(f"No such config key: {key}")
    
    # Convenience properties for commonly used paths
    # @property
    # def calypso_path(self) -> str:
    #     """Get Calypso installation path."""
    #     path = self.get('paths.calypso_install', '')
    #     if not path:
    #         raise ValueError(
    #             "Calypso installation path not configured. "
    #             "Please set 'paths.calypso_install' in config.json"
    #         )
    #     return path
    
    
    # def validate_paths(self) -> None:
    #     """
    #     Validate that configured paths exist.
        
    #     Raises:
    #         FileNotFoundError: If required paths don't exist
    #     """
    #     calypso = self.get('paths.calypso_install')
    #     if calypso and not Path(calypso).exists():
    #         raise FileNotFoundError(f"Calypso installation not found: {calypso}")
        
    #     pede = self.get('paths.pede_install')
    #     if pede and not Path(pede).exists():
    #         raise FileNotFoundError(f"Pede installation not found: {pede}")
    
