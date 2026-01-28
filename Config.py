#!/usr/bin/env python3
"""
Basic configuration manager from JSON file.

This module handles loading of configuration from JSON files.
"""

import json
from pathlib import Path
from typing import Any, Optional, Union

class ConfigNode:
    """Branch: A dict node in the configuration tree."""
    def __init__(self, data: dict[str, Any], path: str = ""):
        if not isinstance(data, dict):
            raise TypeError(f"ConfigNode expects a dict, got {type(data).__name__}")
        self._data = data
        self._path = path

    def __getattr__(self, key: str):
        if key.startswith('_'):
            raise AttributeError(f"Illegal attribute: {key} start with '_'.")
        if key in self._data:
            value = self._data[key]
            new_path = f"{self._path}.{key}" if self._path else key
            if isinstance(value, dict):
                return ConfigNode(value, new_path)
            else:
                return ConfigValue(value, new_path)
        raise AttributeError(f"No such config key: {key}")


class ConfigValue:
    """Leaf: Wrapper for config values that carries keys information."""
    def __init__(self, value: Any, keys: str):
        self._value = value
        self._keys = keys
    
    """Public Properties"""
    @property
    def value(self) -> Any:
        """Get the wrapped value."""
        return self._value
    @property
    def keys(self) -> str:
        """Get the configuration keys."""
        return self._keys
    
    """Transparent Proxy"""
    def __repr__(self):
        return repr(self._value)
    def __str__(self):
        return str(self._value)
    def __int__(self):
        return int(self._value)
    def __bool__(self):
        return bool(self._value)
    def __eq__(self, other):
        if isinstance(other, ConfigValue):
            return self._value == other._value
        return self._value == other

class Config:
    """Basic config manager from JSON file."""
    
    def __init__(self, config_file: Path):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to JSON configuration file.
        """
        self._config_file: Path = config_file
        self._config: dict[str, Any] = self._load_config()
        
    def _load_config(self) -> dict[str, Any]:
        """Load configuration from JSON file."""
        config_path = self._config_file
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
        if key.startswith('_'):
            raise AttributeError(f"Illegal attribute: {key} start with '_'.")
        if key in self._config:
            value = self._config[key]
            if isinstance(value, dict):
                return ConfigNode(value, key)
            else:
                return ConfigValue(value, key)
        raise AttributeError(f"No such config key: {key}")
    
    # ==================== Helper methods ====================
    
    # Liberal Accept, Strict Validate
    def _ensure_type(self, config: Union[ConfigValue, ConfigNode],
                     expected_types: tuple) -> Any:
        """
        Ensure and return value of expected type(s).
        
        Args:
            config: Must be ConfigValue (leaf node).
            expected_types: Tuple of expected types
            
        Returns:
            The unwrapped value if type is correct
            
        Raises:
            TypeError: If value is ConfigNode or if value type isn't expected
            
        Note:
            Type hint accepts Union[ConfigValue, ConfigNode] because static type 
            checkers cannot determine whether config.x.y is a leaf or branch at 
            compile time. Runtime validation ensures only ConfigValue is processed.
        """
        # Runtime guard: can't deal with ConfigNode
        if isinstance(config, ConfigNode):
            raise TypeError(
                f"{config._path} is a ConfigNode (dict)."
            )
        
        if not isinstance(config.value, expected_types):
            raise TypeError(
                f"{config.keys} type: {type(config.value).__name__} not valid.\n"
                f"Expected: {', '.join(t.__name__ for t in expected_types)}"
            )
        return config.value
    
    def _get_str(self, config: Union[ConfigValue, ConfigNode]) -> str:
        return self._ensure_type(config, (str,))
    
    def _get_int(self, config: Union[ConfigValue, ConfigNode]) -> int:
        return self._ensure_type(config, (int,))
    
    def _format_str(self, config: Union[ConfigValue, ConfigNode], **kwargs) -> str:
        """
        Get a string value and format it with provided arguments.
        
        Args:
            config: ConfigValue or ConfigNode wrapper
            **kwargs: Format arguments
            
        Returns:
            Formatted string
        """
        string_value = self._get_str(config)  # Already rejects ConfigNode
        try:
            return string_value.format(**kwargs)
        except KeyError as e:
            raise ValueError(
                f"{config.keys}: missing key {e} in string: {string_value}")
    
    def _get_path(self, config: Union[ConfigValue, ConfigNode],
                  exist: bool = False, **kwargs) -> Path:
        """
        Get a path value with optional formatting and existence validation.
        
        Args:
            config: ConfigValue or ConfigNode wrapper
            exist: Whether the path must exist
            **kwargs: Format arguments (if provided, string will be formatted)
            
        Returns:
            Path object
            
        Warnings:
            Existence check is performed, so only for absolute paths.
        """
        # If format arguments provided, format the string first
        if kwargs:
            string_value = self._format_str(config, **kwargs)
        else:
            string_value = self._get_str(config)
        
        path = Path(string_value)
        if exist and not path.exists():
            raise FileNotFoundError(
                f"{config.keys}: path does not exist: {path}")
        return path
    
    def _get_joint_path(self, base_path: Path, config: Union[ConfigValue, ConfigNode],
                        exist: bool = False, **kwargs) -> Path:
        """
        Get a path by joining a base directory with a relative path from config.
        
        Args:
            base_path: Base directory path
            config: ConfigValue or ConfigNode wrapper containing relative path
            exist: Whether the resulting path must exist
            **kwargs: Format arguments (if provided, string will be formatted)
            
        Returns:
            Joined Path object
        """
        # Get relative path from config
        if kwargs:
            relative = self._format_str(config, **kwargs)
        else:
            relative = self._get_str(config)
        
        # Join with base path
        path = base_path / relative
        if exist and not path.exists():
            raise FileNotFoundError(
                f"{config.keys}: path does not exist: {path}")
        return path
