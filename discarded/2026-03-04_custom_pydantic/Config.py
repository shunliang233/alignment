#!/usr/bin/env python3
"""
Basic configuration manager from JSON file.

This module handles loading of configuration from JSON files.
"""

import json
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

class ConfigNode:
    """
    A node in the configuration tree.

    Represents both branches (dict) and leaves (scalar values):
    - Branch: attribute access returns child ConfigNodes
    - Leaf:   .value returns the scalar; attribute access raises an error
    """

    def __init__(self, data: Any, path: str = ""):
        self._data = data
        self._path = path

    # ---- type queries ----
    @property
    def _is_leaf(self) -> bool:
        """True if this node holds a scalar value (not a dict or list)."""
        return not isinstance(self._data, (dict, list))
    @property
    def _is_branch(self) -> bool:
        """True if this node holds a dict (has named children)."""
        return isinstance(self._data, dict)
    @property
    def _is_array(self) -> bool:
        """True if this node holds a list (has indexed children)."""
        return isinstance(self._data, list)

    # ---- value access ----
    @property
    def value(self) -> Any:
        """
        Return the raw Python value.

        Works for leaf (scalar) and array (list) nodes.
        Raises TypeError for branch (dict) nodes — navigate with attributes instead.
        """
        if self._is_branch:
            raise TypeError(f"'{self._path}' is a branch node.")
        return self._data

    # ---- child access (branch nodes only) ----
    def __getattr__(self, key: str):
        if key.startswith('_'):
            raise AttributeError(f"Illegal '{key}' starts with '_'.")
        if self._is_leaf:
            raise AttributeError(
                f"'{self._path}' is a leaf node (value={self._data!r}), "
                f"cannot access attribute '{key}'")
        if self._is_array:
            raise AttributeError(
                f"'{self._path}' is an array node, use [] / iteration instead")
        if key in self._data:
            child_path = f"{self._path}.{key}" if self._path else key
            return ConfigNode(self._data[key], child_path)
        raise AttributeError(f"No such config key: '{self._path}.{key}'")

    # ---- indexed access (array and branch nodes) ----
    def __getitem__(self, key):
        if self._is_array:
            # IndexError propagates naturally for out-of-range indices.
            return ConfigNode(self._data[key], f"{self._path}[{key}]")
        if self._is_branch:
            if key not in self._data:
                raise KeyError(f"No such config key: '{self._path}.{key}'")
            child_path = f"{self._path}.{key}" if self._path else key
            return ConfigNode(self._data[key], child_path)
        raise TypeError(
            f"'{self._path}' is a leaf node (value={self._data!r}), "
            f"cannot use [] access")

    # ---- iteration support (array nodes only) ----
    def __iter__(self):
        if not self._is_array:
            raise TypeError(
                f"'{self._path}' is not an array node, cannot iterate")
        for i, item in enumerate(self._data):
            yield ConfigNode(item, f"{self._path}[{i}]")

    def __len__(self):
        if not self._is_array:
            raise TypeError(
                f"'{self._path}' is not an array node, cannot get length")
        return len(self._data)

    # ---- transparent proxy (useful for leaf nodes) ----
    def __repr__(self):
        return repr(self._data)
    def __str__(self):
        return str(self._data)
    def __int__(self):
        return int(self._data)
    def __bool__(self):
        return bool(self._data)
    def __eq__(self, other):
        if isinstance(other, ConfigNode):
            return self._data == other._data
        return self._data == other

class Config(ABC):
    """Basic config manager from JSON file."""
    
    def __init__(self, config_file: Path):
        """
        Initialize configuration.

        Args:
            config_file: Path to JSON configuration file.
        """
        # NOTE: Never explicitly/implicitly invoke __getattr__ in __init__
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
    
    def __getattr__(self, key: str) -> ConfigNode:
        """Allow attribute-style access to config keys."""
        if key.startswith('_'):
            raise AttributeError(f"Illegal '{key}' starts with '_'.")
        if key in self._config:
            return ConfigNode(self._config[key], key)
        raise AttributeError(f"No such config key: {key}")

    # ==================== Template Methods ====================

    @property
    @abstractmethod
    def _archive_dest(self) -> Path:
        """Destination path for archiving the config file."""
        ...

    def archive(self) -> None:
        """Copy the config file to the archive destination."""
        # NOTE: mkdir is a defensive operation in case parent don't exist.
        dest = self._archive_dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self._config_file, dest)

    # ==================== Helper methods ====================
    
    def _ensure_type(self, config: ConfigNode,
                     expected_types: tuple) -> Any:
        """
        Ensure and return value of expected type(s).

        Args:
            config: A leaf ConfigNode (branch nodes are rejected at runtime).
            expected_types: Tuple of accepted types.

        Returns:
            The unwrapped scalar value.

        Raises:
            TypeError: If config is a branch node, or value type doesn't match.
        """
        val = config.value
        if not isinstance(val, expected_types):
            raise TypeError(
                f"{config.path} type: {type(val).__name__} not valid.\n"
                f"Expected: {', '.join(t.__name__ for t in expected_types)}"
            )
        return val
    
    def _get_int(self, config: ConfigNode) -> int:
        return self._ensure_type(config, (int,))

    def _get_list(self, config: ConfigNode) -> list:
        """Get a list value from a leaf ConfigNode."""
        return self._ensure_type(config, (list,))
    
    def _get_str(self, config: ConfigNode, **kwargs) -> str:
        """
        Get a string value with optional formatting.

        Args:
            config: A leaf ConfigNode.
            **kwargs: Optional format arguments.

        Returns:
            String value (formatted if kwargs provided).
        """
        string_value = self._ensure_type(config, (str,))

        # Format if arguments provided
        if kwargs:
            try:
                return string_value.format(**kwargs)
            except KeyError as e:
                raise ValueError(
                    f"{config.path}: missing key {e} in string: {string_value}")
        
        return string_value
    
    def _get_path(self, config: ConfigNode,
                  base: Optional[Path] = None,
                  exist: bool = False, ensure: bool = False, **kwargs) -> Path:
        """
        Get a path value with optional formatting and existence validation.
        
        Args:
            config: ConfigValue or ConfigNode wrapper
            base: Optional base directory to join with relative path from config
            exist: Whether the path must exist (raises error if not, ignores ensure)
            ensure: Whether to ensure path exists (creates if not, only when exist=False)
            **kwargs: Format arguments (if provided, string will be formatted)
            
        Returns:
            Path object
            
        Note:
            - base=None: Use path from config directly
            - base provided: Join base with relative path from config
            - exist=True: Path must exist, raises error if not (for templates, scripts)
            - exist=False, ensure=True: Ensure path exists, create if not (for data dirs)
            - exist=False, ensure=False: Path may not exist, no action taken (default)
        """
        # Get string value (formatted if kwargs provided)
        string_value = self._get_str(config, **kwargs)
        
        # Build path: join with base if provided, otherwise use directly
        if base is not None:
            path = base / string_value
        else:
            path = Path(string_value)
        
        # Validation mode: path must exist
        if exist:
            if not path.exists():
                raise FileNotFoundError(
                    f"{config.path}: path does not exist: {path}")
        # Creation mode: ensure path exists if requested
        elif ensure:
            path.mkdir(parents=True, exist_ok=True)
        
        return path
    


