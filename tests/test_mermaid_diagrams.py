#!/usr/bin/env python3
"""
Test script to validate Mermaid diagrams in documentation files.

This script extracts and validates Mermaid diagrams from markdown files
to ensure they have valid syntax.
"""

import re
import sys
import subprocess
from pathlib import Path


def extract_mermaid_blocks(file_path):
    """
    Extract all Mermaid code blocks from a markdown file.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        List of tuples (line_number, mermaid_code)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = []
    pattern = r'```mermaid\n(.*?)```'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        # Find line number
        line_num = content[:match.start()].count('\n') + 1
        mermaid_code = match.group(1)
        blocks.append((line_num, mermaid_code))
    
    return blocks


def validate_mermaid_syntax(mermaid_code):
    """
    Validate Mermaid syntax by checking for common issues.
    
    Args:
        mermaid_code: The Mermaid diagram code
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check for balanced brackets
    bracket_count = mermaid_code.count('[') - mermaid_code.count(']')
    if bracket_count != 0:
        errors.append(f"Unbalanced square brackets (difference: {bracket_count})")
    
    # Check for balanced curly braces
    brace_count = mermaid_code.count('{') - mermaid_code.count('}')
    if brace_count != 0:
        errors.append(f"Unbalanced curly braces (difference: {brace_count})")
    
    # Check for balanced parentheses
    paren_count = mermaid_code.count('(') - mermaid_code.count(')')
    if paren_count != 0:
        errors.append(f"Unbalanced parentheses (difference: {paren_count})")
    
    # Check for double brackets (not supported in some Mermaid versions)
    if '[[' in mermaid_code:
        errors.append("Double brackets '[[' detected - may cause lexical errors in some Mermaid versions")
    
    # Check for non-ASCII characters in decision nodes (curly braces with Chinese/special chars)
    # This can cause "Unrecognized text" lexical errors in Mermaid
    import unicodedata
    lines = mermaid_code.strip().split('\n')
    for i, line in enumerate(lines, 1):
        # Check for curly braces with non-ASCII content (decision nodes)
        if '{' in line and '}' in line:
            # Extract content between curly braces
            start = line.find('{')
            end = line.find('}', start)
            if start != -1 and end != -1:
                content = line[start+1:end]
                # Check if contains non-ASCII characters
                if any(ord(char) > 127 for char in content):
                    errors.append(f"Line {i}: Decision node contains non-ASCII characters: '{content}'. "
                                f"This may cause lexical errors in Mermaid. Consider using ASCII only or simplifying.")
    
    # Check for emoji or special unicode in node labels with brackets
    for i, line in enumerate(lines, 1):
        if '[' in line and ']' in line:
            # Extract content between brackets
            matches = re.finditer(r'\[([^\]]+)\]', line)
            for match in matches:
                content = match.group(1)
                # Check for problematic unicode
                if any(unicodedata.category(char).startswith('So') for char in content):
                    # Emoji detected
                    pass  # Emojis in quotes are generally OK
    
    # Check for proper graph declaration
    if lines:
        first_line = lines[0].strip()
        valid_starts = ['graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 
                       'stateDiagram', 'erDiagram', 'journey', 'gantt', 'pie']
        if not any(first_line.startswith(start) for start in valid_starts):
            errors.append(f"Invalid diagram type declaration: '{first_line}'")
    
    # Check for style definitions
    style_pattern = r'style\s+\w+\s+fill:'
    if 'style' in mermaid_code and not re.search(style_pattern, mermaid_code):
        errors.append("Potentially malformed style definition")
    
    # Check for line breaks in labels (should use <br/> or <br> not literal breaks)
    if '\n' in mermaid_code and '<br' not in mermaid_code.lower():
        # Multi-line code is OK, but check for unclosed quotes with line breaks
        pass
    
    return len(errors) == 0, errors


def validate_with_mermaid_cli(mermaid_code):
    """
    Attempt to validate using mermaid-cli if available.
    
    Args:
        mermaid_code: The Mermaid diagram code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if mmdc (mermaid-cli) is available
        result = subprocess.run(['which', 'mmdc'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        
        if result.returncode != 0:
            return None, "mermaid-cli (mmdc) not available - skipping CLI validation"
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
            f.write(mermaid_code)
            temp_file = f.name
        
        try:
            # Try to validate with mermaid-cli
            result = subprocess.run(['mmdc', '-i', temp_file, '--parse'],
                                  capture_output=True,
                                  text=True,
                                  timeout=10)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr
        finally:
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
            
    except subprocess.TimeoutExpired:
        return None, "mermaid-cli validation timed out"
    except Exception as e:
        return None, f"mermaid-cli validation error: {str(e)}"


def test_markdown_file(file_path):
    """
    Test all Mermaid diagrams in a markdown file.
    
    Args:
        file_path: Path to markdown file
        
    Returns:
        Tuple of (success_count, total_count, errors)
    """
    print(f"\nValidating Mermaid diagrams in: {file_path}")
    print("=" * 60)
    
    blocks = extract_mermaid_blocks(file_path)
    
    if not blocks:
        print("No Mermaid diagrams found.")
        return 0, 0, []
    
    print(f"Found {len(blocks)} Mermaid diagram(s)\n")
    
    success_count = 0
    all_errors = []
    
    for i, (line_num, mermaid_code) in enumerate(blocks, 1):
        print(f"Diagram {i} (starting at line {line_num}):")
        
        # Basic syntax validation
        is_valid, errors = validate_mermaid_syntax(mermaid_code)
        
        if is_valid:
            print("  ✓ Basic syntax validation: PASSED")
            success_count += 1
        else:
            print("  ✗ Basic syntax validation: FAILED")
            for error in errors:
                print(f"    - {error}")
                all_errors.append((file_path, line_num, error))
        
        # Try CLI validation if available
        cli_valid, cli_error = validate_with_mermaid_cli(mermaid_code)
        if cli_valid is True:
            print("  ✓ mermaid-cli validation: PASSED")
        elif cli_valid is False:
            print(f"  ✗ mermaid-cli validation: FAILED")
            print(f"    - {cli_error}")
            all_errors.append((file_path, line_num, f"CLI: {cli_error}"))
        else:
            print(f"  ⓘ mermaid-cli validation: SKIPPED ({cli_error})")
        
        print()
    
    return success_count, len(blocks), all_errors


def main():
    """Main test function."""
    print("Mermaid Diagram Validation Test")
    print("=" * 60)
    
    # Find repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # Files to check
    markdown_files = [
        repo_root / "README.md",
        repo_root / "README_cn.md",
    ]
    
    # Check if files exist
    markdown_files = [f for f in markdown_files if f.exists()]
    
    if not markdown_files:
        print("ERROR: No markdown files found to validate")
        return 1
    
    total_success = 0
    total_diagrams = 0
    all_errors = []
    
    for md_file in markdown_files:
        success, count, errors = test_markdown_file(md_file)
        total_success += success
        total_diagrams += count
        all_errors.extend(errors)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total diagrams validated: {total_diagrams}")
    print(f"Passed basic validation: {total_success}")
    print(f"Failed basic validation: {total_diagrams - total_success}")
    
    if all_errors:
        print(f"\n❌ Found {len(all_errors)} validation error(s):")
        for file_path, line_num, error in all_errors:
            print(f"  {file_path.name}:{line_num} - {error}")
        return 1
    else:
        print("\n✓ All Mermaid diagrams passed validation!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
