#!/usr/bin/env python3
"""
Analyser for ROOT TTree files.

This module provides a class to read and analyze TTree structure and branch information.
"""

import ROOT
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from pathlib import Path
from typing import Dict, List, Optional, Union, Any, cast

from BranchInfo import BranchInfo

# Add type hints for ROOT classes
TFile = Any  # ROOT.TFile
TTree = Any  # ROOT.TTree
TBranch = Any  # ROOT.TBranch
TObjArray = Any  # ROOT.TObjArray

class Analyser:
    """Analyser for ROOT TTree files."""
    
    # ROOT TTree leaf type mapping
    _TYPE_MAP = {
        'D': 'Double_t',
        'F': 'Float_t',
        'I': 'Int_t',
        'i': 'UInt_t',
        'L': 'Long64_t',
        'l': 'ULong64_t',
        'S': 'Short_t',
        's': 'UShort_t',
        'B': 'Char_t',
        'b': 'UChar_t',
        'O': 'Bool_t',
    }
    
    def __init__(self, file_path: Union[str, Path], tree_name: str = "tree"):
        """
        Initialize the analyser.
        
        Args:
            file_path: Path to ROOT file
            tree_name: Name of TTree to analyze (default: "tree")
        
        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If file can't be opened or tree doesn't exist
        """
        # Check File Existence
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"ROOT file not found: {self.file_path}")
        # Check File Validity
        self.file = cast(TFile, ROOT.TFile.Open(str(self.file_path)))
        if not self.file or self.file.IsZombie():
            raise RuntimeError(f"Cannot open ROOT file: {self.file_path}")
        # Get TTree
        self.tree_name = tree_name
        self.tree = cast(TTree, self.file.Get(tree_name))
        if not self.tree:
            self.file.Close()
            raise RuntimeError(f"TTree '{tree_name}' not found in {self.file_path}")
        
        # Initialize Branch Dictionary
        self._branches: Dict[str, BranchInfo] = {}
        # Cache for vector branches
        self._vector_branches_cache: Optional[Dict[str, str]] = None
    
    def _close(self):
        """Close ROOT file if it's open."""
        if hasattr(self, 'file') and self.file and self.file.IsOpen():
            self.file.Close()
    def __del__(self):
        """Clean up ROOT file when object is destroyed."""
        self._close()
    def __enter__(self):
        """Context manager entry."""
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._close()
    
    @property
    def entries(self) -> int:
        """Get number of entries in the tree."""
        return self.tree.GetEntries()
    
    @property
    def branches(self) -> Dict[str, BranchInfo]:
        """
        Get dictionary of all branches.
        
        Returns:
            Dictionary mapping branch name to BranchInfo
        """
        if not self._branches:
            branch_list = cast(TObjArray, self.tree.GetListOfBranches())
            for i in range(branch_list.GetEntries()):
                branch = cast(TBranch, branch_list.At(i))
                name: str = branch.GetName()
                typename: str = branch.GetClassName()
                title: str = branch.GetTitle()
                if not typename: # For basic types (leaflist)
                    if '/' in title:
                        type_char = title.split('/')[1]
                        typename = self._TYPE_MAP.get(type_char, type_char)
                    else:
                        typename = "unknown"
                
                self._branches[name] = BranchInfo(name, typename, title)
        return self._branches
    
    def get_branch_names(self) -> List[str]:
        """
        Get list of all branch names.
        
        Returns:
            List of branch names
        """
        return list(self.branches.keys())
    
    def get_branch_info(self, branch_name: str) -> Optional[BranchInfo]:
        """
        Get information about a specific branch.
        
        Args:
            branch_name: Name of the branch
            
        Returns:
            BranchInfo object or None if branch doesn't exist
        """
        return self.branches.get(branch_name)
    
    def print_summary(self) -> None:
        """Print a summary of the tree structure."""
        print(f"File: {self.file_path}")
        print(f"Tree: {self.tree_name}")
        print(f"Entries: {self.entries}")
        print(f"Branches: {len(self.branches)}")
        print("\nBranch Information:")
        print("-" * 80)
        print(f"{'Name':50} {'Type':20}")
        print("-" * 80)
        for branch_info in self.branches.values():
            print(branch_info)
    
    def get_branch_data(self, branch_name: str, max_entries: Optional[int] = None) -> List:
        """
        Get data from a specific branch.
        
        Args:
            branch_name: Name of the branch
            max_entries: Maximum number of entries to read (default: all)
            
        Returns:
            List of values from the branch
            
        Raises:
            ValueError: If branch doesn't exist
        """
        if branch_name not in self.branches:
            raise ValueError(f"Branch '{branch_name}' not found")
        
        data = []
        n_entries = min(self.entries, max_entries) if max_entries else self.entries
        
        for i in range(n_entries):
            self.tree.GetEntry(i)
            value = getattr(self.tree, branch_name)
            data.append(value)
        
        return data
    
    def print_branch_stats(self, branch_name: str) -> None:
        """
        Print detailed statistics for a branch.
        
        Args:
            branch_name: Name of the branch
        """
        if branch_name not in self.branches:
            raise ValueError(f"Branch '{branch_name}' not found")
        
        branch: TBranch = self.tree.GetBranch(branch_name)
        
        print(f"\nBranch Statistics for '{branch_name}':")
        print("-" * 80)
        print(f"Type:           {self.branches[branch_name].typename}")
        print(f"Title:          {self.branches[branch_name].title}")
        print(f"Entries:        {branch.GetEntries()}")
        print(f"Total Size:     {branch.GetTotBytes()} bytes")
        print(f"File Size:      {branch.GetZipBytes()} bytes")
        compression = branch.GetTotBytes() / branch.GetZipBytes() if branch.GetZipBytes() > 0 else 0
        print(f"Compression:    {compression:.2f}")
        print(f"Baskets:        {branch.GetWriteBasket()}")
        print(f"Basket Size:    {branch.GetBasketSize()} bytes")
    
    def get_vector_branches(self) -> Dict[str, str]:
        """
        Get all vector-type branches.
        
        Returns:
            Dictionary mapping branch name to type name
        """
        # Return cached result if available
        if self._vector_branches_cache is not None:
            return self._vector_branches_cache
        
        vector_branches = {}
        branch_list = cast(TObjArray, self.tree.GetListOfBranches())
        
        for i in range(branch_list.GetEntries()):
            branch = cast(TBranch, branch_list.At(i))
            branch_name: str = branch.GetName()
            type_name: str = branch.GetClassName()
            
            # Check if branch is a vector type
            if type_name and ('vector' in type_name.lower() or type_name.startswith('std::vector')):
                vector_branches[branch_name] = type_name
        
        # Cache the result
        self._vector_branches_cache = vector_branches
        return vector_branches
    
    def get_vector_lengths(self, branch_name: str, max_entries: Optional[int] = None) -> List[int]:
        """
        Get vector lengths for all entries in a vector branch.
        
        Args:
            branch_name: Name of the vector branch
            max_entries: Maximum number of entries to read (default: all)
            
        Returns:
            List of vector lengths
            
        Raises:
            ValueError: If branch is not a vector type
        """
        vector_branches = self.get_vector_branches()
        if branch_name not in vector_branches:
            raise ValueError(f"Branch '{branch_name}' is not a vector type")
        
        lengths = []
        n_entries = min(self.entries, max_entries) if max_entries else self.entries
        
        for i in range(n_entries):
            self.tree.GetEntry(i)
            vec = getattr(self.tree, branch_name)
            if vec is not None:
                lengths.append(len(vec))
        
        return lengths
    
    def create_vector_length_histograms(self, output_pdf: str = 'vector_lengths.pdf',
                                       branches: Optional[List[str]] = None) -> None:
        """
        Create histograms of vector lengths for all vector branches and save to PDF.
        
        Args:
            output_pdf: Output PDF file path (default: 'vector_lengths.pdf')
            branches: List of specific branches to plot (default: all vector branches)
        """
        vector_branches = self.get_vector_branches()
        
        if not vector_branches:
            print("No vector branches found in the tree.")
            return
        
        # Filter branches if specified
        if branches:
            vector_branches = {k: v for k, v in vector_branches.items() if k in branches}
            if not vector_branches:
                print(f"None of the specified branches are vector types.")
                return
        
        print(f"Analyzing {len(vector_branches)} vector branch(es)...")
        
        with PdfPages(output_pdf) as pdf:
            for branch_name, type_name in vector_branches.items():
                print(f"Processing: {branch_name} (type: {type_name})")
                
                try:
                    lengths = self.get_vector_lengths(branch_name)
                    
                    if not lengths:
                        print(f"  Warning: No data for {branch_name}")
                        continue
                    
                    # Create histogram
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Use integer bins: one bin per integer value
                    min_len = min(lengths)
                    max_len = max(lengths)
                    bins = np.arange(min_len, max_len + 2) - 0.5  # Center bins on integers
                    
                    ax.hist(lengths, bins=bins, edgecolor='black', alpha=0.7)
                    ax.set_xlabel('Vector Length')
                    ax.set_ylabel('Frequency')
                    ax.set_title(f'Vector Length Distribution: {branch_name}')
                    ax.grid(True, alpha=0.3)
                    
                    # Set integer ticks on x-axis
                    ax.set_xticks(range(min_len, max_len + 1))
                    
                    # Add statistics text
                    stats_text = f'Entries: {len(lengths)}\n'
                    stats_text += f'Mean: {np.mean(lengths):.2f}\n'
                    stats_text += f'Std: {np.std(lengths):.2f}\n'
                    stats_text += f'Min: {min_len}\n'
                    stats_text += f'Max: {max_len}'
                    ax.text(0.98, 0.97, stats_text,
                           transform=ax.transAxes,
                           verticalalignment='top',
                           horizontalalignment='right',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                    
                    plt.tight_layout()
                    pdf.savefig(fig)
                    plt.close(fig)
                    
                except Exception as e:
                    print(f"  Error processing {branch_name}: {e}")
                    continue
        
        print(f"\nHistograms saved to: {output_pdf}")
        print(f"Total vector branches analyzed: {len(vector_branches)}")
