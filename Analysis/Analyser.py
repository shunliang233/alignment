#!/usr/bin/env python3
"""
Analyser for ROOT TTree files.

This module provides a class to read and analyze TTree structure and branch information.
"""

import ROOT

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
        self.root_file = cast(TFile, ROOT.TFile.Open(str(self.file_path)))
        if not self.root_file or self.root_file.IsZombie():
            raise RuntimeError(f"Cannot open ROOT file: {self.file_path}")
        # Get TTree
        self.tree_name = tree_name
        self.tree = cast(TTree, self.root_file.Get(tree_name))
        if not self.tree:
            self.root_file.Close()
            raise RuntimeError(f"TTree '{tree_name}' not found in {self.file_path}")
        # Initialize Branch Dictionary
        self._branches: Dict[str, BranchInfo] = {}
    
    def _close(self):
        """Close ROOT file if it's open."""
        if hasattr(self, 'root_file') and self.root_file and self.root_file.IsOpen():
            self.root_file.Close()
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
        print(f"{'Name':<30} {'Type':<20} {'Title'}")
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
    