#!/usr/bin/env python3
"""
Alignment data parser for reading alignment parameter files.

This module parses alignment data files that contain quasi-JSON format
with alignment parameters organized by detector component identifiers.
"""

import json
from pathlib import Path
from typing import Optional


class InputAlign:
    """
    Parser for alignment parameter files.
    
    Handles files with format:
    "00": [x, y, z, rx, ry, rz], "01": [...], ...
    
    Where keys are detector component IDs and values are 6-element
    transformation parameters [x, y, z, rx, ry, rz].
    """
    
    # Parameter names for plotting
    _PARAM_NAMES = ['X', 'Y', 'Z', 'Rx', 'Ry', 'Rz']
    _PARAM_UNITS = ['mm', 'mm', 'mm', 'rad', 'rad', 'rad']
    
    def __init__(self, file_path: Path, title: Optional[str] = None):
        """
        Initialize alignment parser.
        
        Args:
            file_path: Path to alignment data file
            title: Optional title for the alignment data (used in plotting)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        self._title = title if title else file_path.stem
        self._file_path = Path(file_path)
        if not self._file_path.exists():
            raise FileNotFoundError(f"Alignment file not found: {file_path}")
        
        self._data: dict[str, tuple[float, ...]] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load and parse alignment data from file."""
        with open(self._file_path, 'r') as f:
            content = f.read()
        
        # Clean up the content
        content = content.strip()
        
        # Add outer braces to make it valid JSON
        json_str = '{' + content + '}'
        
        try:
            raw_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid alignment file format: {e}")
        
        # Validate and convert to tuple
        for key, value in raw_data.items():
            if not isinstance(value, list):
                raise ValueError(f"Invalid value for key '{key}': expected list, got {type(value)}")
            if len(value) != 6:
                raise ValueError(f"Invalid parameter count for key '{key}': expected 6, got {len(value)}")
            self._data[key] = tuple(value)
    
    def __add__(self, other: 'InputAlign') -> 'InputAlign':
        """
        Add two InputAlign objects element-wise.
        
        Args:
            other: Another InputAlign object
            
        Returns:
            New InputAlign object with summed parameters
            
        Raises:
            ValueError: If component IDs don't match
        """
        if not isinstance(other, InputAlign):
            raise TypeError(f"Cannot add InputAlign with {type(other).__name__}")
        
        if set(self._data.keys()) != set(other._data.keys()):
            raise ValueError("Cannot add: component IDs do not match")
        
        # Create new instance with temporary data
        result = InputAlign.__new__(InputAlign)
        result._file_path = Path("memory://summed")
        result._title = f"{self._title} + {other._title}"
        result._data = {}
        
        for key in self._data.keys():
            result._data[key] = tuple(
                self._data[key][i] + other._data[key][i]
                for i in range(6)
            )
        
        return result
    
    def __sub__(self, other: 'InputAlign') -> 'InputAlign':
        """
        Subtract two InputAlign objects element-wise.
        
        Args:
            other: Another InputAlign object
            
        Returns:
            New InputAlign object with difference of parameters
            
        Raises:
            ValueError: If component IDs don't match
        """
        if not isinstance(other, InputAlign):
            raise TypeError(f"Cannot subtract {type(other).__name__} from InputAlign")
        
        if set(self._data.keys()) != set(other._data.keys()):
            raise ValueError("Cannot subtract: component IDs do not match")
        
        # Create new instance with temporary data
        result = InputAlign.__new__(InputAlign)
        result._file_path = Path("memory://difference")
        result._title = f"{self._title} - {other._title}"
        result._data = {}
        
        for key in self._data.keys():
            result._data[key] = tuple(
                self._data[key][i] - other._data[key][i]
                for i in range(6)
            )
        
        return result
    
    def to_dict(self) -> dict[str, tuple[float, ...]]:
        """
        Export all alignment data as dictionary.
        
        Returns:
            Dictionary mapping component IDs to parameter tuples (immutable)
        """
        return self._data.copy()
    
    def plot_all_parameters(self, figsize: tuple = (15, 10), 
                           save_path: Optional[Path] = None) -> None:
        """
        Plot all 6 parameters in a 2x3 grid.
        
        Each subplot shows a scatter plot of parameter values vs component ID.
        
        Args:
            figsize: Figure size (width, height)
            save_path: Path to save figure (None = display only)
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle(self._title, fontsize=16, fontweight='bold')
        
        # Get sorted component IDs for consistent plotting
        component_ids = sorted(self._data.keys())
        indices = np.arange(len(component_ids))
        
        for param_idx in range(6):
            row = param_idx // 3
            col = param_idx % 3
            ax = axes[row, col]
            
            # Extract parameter values
            values = [self._data[cid][param_idx] for cid in component_ids]
            
            # Create scatter plot
            ax.scatter(indices, values, alpha=0.6, s=30)
            ax.axhline(y=0, color='r', linestyle='--', alpha=0.3)
            ax.set_xlabel('Component ID')
            ax.set_ylabel(f'{self._PARAM_NAMES[param_idx]} ({self._PARAM_UNITS[param_idx]})')
            
            # Smart tick selection: show fewer labels if too many components
            n_components = len(component_ids)
            if n_components <= 10:
                step = 1
            elif n_components <= 30:
                step = 2
            elif n_components <= 60:
                step = 5
            else:
                step = max(1, n_components // 15)
            
            tick_indices = indices[::step]
            tick_labels = component_ids[::step]
            ax.set_xticks(tick_indices)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
            ax.set_title(f'Parameter: {self._PARAM_NAMES[param_idx]}')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved plot to {save_path}")
        else:
            plt.show()
    
    def plot_local_parameters(self, figsize: tuple = (15, 10), 
                             save_path: Optional[Path] = None) -> None:
        """
        Plot 6 parameters for local components (3-character IDs) in a 2x3 grid.
        
        Each subplot shows a scatter plot of parameter values vs component ID.
        
        Args:
            figsize: Figure size (width, height)
            save_path: Path to save figure (None = display only)
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Filter for 3-character component IDs (local)
        local_ids = sorted([cid for cid in self._data.keys() if len(cid) == 3])
        
        if not local_ids:
            print("No local components (3-character IDs) found.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle(f'{self._title} - Local Components', fontsize=16, fontweight='bold')
        
        indices = np.arange(len(local_ids))
        
        for param_idx in range(6):
            row = param_idx // 3
            col = param_idx % 3
            ax = axes[row, col]
            
            # Extract parameter values
            values = [self._data[cid][param_idx] for cid in local_ids]
            
            # Create scatter plot
            ax.scatter(indices, values, alpha=0.6, s=30, color='blue')
            ax.axhline(y=0, color='r', linestyle='--', alpha=0.3)
            ax.set_xlabel('Component ID')
            ax.set_ylabel(f'{self._PARAM_NAMES[param_idx]} ({self._PARAM_UNITS[param_idx]})')
            
            # Smart tick selection
            n_components = len(local_ids)
            if n_components <= 10:
                step = 1
            elif n_components <= 30:
                step = 2
            elif n_components <= 60:
                step = 5
            else:
                step = max(1, n_components // 15)
            
            tick_indices = indices[::step]
            tick_labels = local_ids[::step]
            ax.set_xticks(tick_indices)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
            ax.set_title(f'Parameter: {self._PARAM_NAMES[param_idx]}')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved local plot to {save_path}")
        else:
            plt.show()
    
    def plot_global_parameters(self, figsize: tuple = (15, 10), 
                              save_path: Optional[Path] = None) -> None:
        """
        Plot 6 parameters for global components (2-character IDs) in a 2x3 grid.
        
        Each subplot shows a scatter plot of parameter values vs component ID.
        
        Args:
            figsize: Figure size (width, height)
            save_path: Path to save figure (None = display only)
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Filter for 2-character component IDs (global)
        global_ids = sorted([cid for cid in self._data.keys() if len(cid) == 2])
        
        if not global_ids:
            print("No global components (2-character IDs) found.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle(f'{self._title} - Global Components', fontsize=16, fontweight='bold')
        
        indices = np.arange(len(global_ids))
        
        for param_idx in range(6):
            row = param_idx // 3
            col = param_idx % 3
            ax = axes[row, col]
            
            # Extract parameter values
            values = [self._data[cid][param_idx] for cid in global_ids]
            
            # Create scatter plot
            ax.scatter(indices, values, alpha=0.6, s=30, color='green')
            ax.axhline(y=0, color='r', linestyle='--', alpha=0.3)
            ax.set_xlabel('Component ID')
            ax.set_ylabel(f'{self._PARAM_NAMES[param_idx]} ({self._PARAM_UNITS[param_idx]})')
            
            # Smart tick selection
            n_components = len(global_ids)
            if n_components <= 10:
                step = 1
            elif n_components <= 30:
                step = 2
            elif n_components <= 60:
                step = 5
            else:
                step = max(1, n_components // 15)
            
            tick_indices = indices[::step]
            tick_labels = global_ids[::step]
            ax.set_xticks(tick_indices)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
            ax.set_title(f'Parameter: {self._PARAM_NAMES[param_idx]}')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved global plot to {save_path}")
        else:
            plt.show()
