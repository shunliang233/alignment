
import argparse

from Analyser import Analyser

def main():
    """Example usage of the Analyser class."""
    
    parser = argparse.ArgumentParser(description="Analyze ROOT TTree structure")
    parser.add_argument('file', type=str, help='Path to ROOT file')
    parser.add_argument('-t', '--tree', type=str, default='tree', 
                        help='Name of TTree (default: tree)')
    parser.add_argument('-b', '--branch', type=str, 
                        help='Show data from specific branch')
    parser.add_argument('-n', '--entries', type=int, 
                        help='Number of entries to display')
    
    args = parser.parse_args()
    
    try:
        with Analyser(args.file, args.tree) as analyser:
            analyser.print_summary()
            
            if args.branch:
                print(f"\nData from branch '{args.branch}':")
                print("-" * 80)
                data = analyser.get_branch_data(args.branch, args.entries)
                for i, value in enumerate(data):
                    print(f"Entry {i}: {value}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
