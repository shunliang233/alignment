#!/usr/bin/env python3

from pathlib import Path

from InputAlign import InputAlign

if __name__ == "__main__":
    # Example usage
    align1 = InputAlign(Path("align-2025.txt"))
    align2 = InputAlign(Path("align-origin.txt"))
    
    align_diff = align1 - align2
    
    align_diff.plot_local_parameters(save_path=Path("local.png"))
    align_diff.plot_global_parameters(save_path=Path("global.png"))