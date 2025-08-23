#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to compile Qt translation files (.ts) to binary format (.qm).

This script compiles all .ts files in the i18n directory to .qm files
that can be used by the Qt translation system.
"""

import os
import sys
import subprocess
from pathlib import Path


def find_lrelease():
    """
    Find the lrelease executable.
    
    Returns:
        str: Path to lrelease executable or None if not found
    """
    # Common locations for lrelease
    possible_paths = [
        'lrelease',  # In PATH
        'lrelease-qt5',  # Ubuntu/Debian
        '/usr/bin/lrelease',
        '/usr/bin/lrelease-qt5',
        '/usr/local/bin/lrelease',
        # Windows Qt installations
        'C:/Qt/5.15.2/msvc2019_64/bin/lrelease.exe',
        'C:/Qt/6.2.0/msvc2019_64/bin/lrelease.exe',
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
    
    return None


def compile_translation(ts_file, qm_file, lrelease_path):
    """
    Compile a single .ts file to .qm format.
    
    Args:
        ts_file: Path to .ts file
        qm_file: Path to output .qm file
        lrelease_path: Path to lrelease executable
        
    Returns:
        bool: True if compilation successful, False otherwise
    """
    try:
        result = subprocess.run([lrelease_path, str(ts_file), '-qm', str(qm_file)],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Compiled {ts_file.name} -> {qm_file.name}")
            return True
        else:
            print(f"✗ Failed to compile {ts_file.name}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error compiling {ts_file.name}: {e}")
        return False


def main():
    """Main function to compile all translation files."""
    # Get script directory and plugin root
    script_dir = Path(__file__).parent
    plugin_dir = script_dir.parent
    i18n_dir = plugin_dir / 'i18n'
    
    print("RedBasica Export - Translation Compiler")
    print("=" * 40)
    
    # Check if i18n directory exists
    if not i18n_dir.exists():
        print(f"✗ i18n directory not found: {i18n_dir}")
        return 1
    
    # Find lrelease executable
    lrelease_path = find_lrelease()
    if not lrelease_path:
        print("✗ lrelease executable not found!")
        print("Please install Qt development tools or add lrelease to PATH")
        return 1
    
    print(f"Using lrelease: {lrelease_path}")
    print()
    
    # Find all .ts files
    ts_files = list(i18n_dir.glob('*.ts'))
    if not ts_files:
        print(f"✗ No .ts files found in {i18n_dir}")
        return 1
    
    # Compile each .ts file
    success_count = 0
    for ts_file in ts_files:
        # Skip the old af.ts file
        if ts_file.name == 'af.ts':
            continue
            
        qm_file = ts_file.with_suffix('.qm')
        if compile_translation(ts_file, qm_file, lrelease_path):
            success_count += 1
    
    print()
    print(f"Compilation complete: {success_count}/{len(ts_files)} files compiled successfully")
    
    if success_count == len(ts_files):
        print("✓ All translations compiled successfully!")
        return 0
    else:
        print("✗ Some translations failed to compile")
        return 1


if __name__ == '__main__':
    sys.exit(main())