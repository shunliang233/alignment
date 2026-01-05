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
    parser.add_argument('-o', '--output', type=str, default='vector_lengths.pdf',
                        help='Output PDF file for vector length histograms (default: vector_lengths.pdf)')
    parser.add_argument('--vector-only', action='store_true',
                        help='Only analyze vector branches and generate histograms')
    
    args = parser.parse_args()
    
    try:
        analyser = Analyser(args.file, args.tree)
        
        if not args.vector_only:
            analyser.print_summary()
            
            if args.branch:
                print(f"\nData from branch '{args.branch}':")
                print("-" * 80)
                data = analyser.get_branch_data(args.branch, args.entries)
                for i, value in enumerate(data):
                    print(f"Entry {i}: {value}")
        
        # Analyze vector branches and create histograms
        print("\nAnalyzing vector branches...")
        analyser.create_vector_length_histograms(output_pdf=args.output)
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
