#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to update Qt translation files (.ts) with new translatable strings.

This script scans Python files for tr() calls and UI files for translatable strings,
then updates the .ts files with new entries.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from xml.etree import ElementTree as ET


def find_pylupdate():
    """
    Find the pylupdate executable.
    
    Returns:
        str: Path to pylupdate executable or None if not found
    """
    # Common locations for pylupdate
    possible_paths = [
        'pylupdate5',  # Most common
        'pylupdate6',  # Qt6 version
        'pylupdate',   # Generic
        '/usr/bin/pylupdate5',
        '/usr/bin/pylupdate6',
        '/usr/local/bin/pylupdate5',
        # Windows Qt installations
        'C:/Qt/5.15.2/msvc2019_64/bin/pylupdate5.exe',
        'C:/Qt/6.2.0/msvc2019_64/bin/pylupdate6.exe',
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


def create_pro_file(plugin_dir: Path) -> Path:
    """
    Create a temporary .pro file for pylupdate.
    
    Args:
        plugin_dir: Path to plugin directory
        
    Returns:
        Path to created .pro file
    """
    pro_file = plugin_dir / 'redbasica_export.pro'
    
    # Find all Python files
    python_files = []
    for py_file in plugin_dir.rglob('*.py'):
        # Skip __pycache__ and test files
        if '__pycache__' not in str(py_file) and 'test_' not in py_file.name:
            python_files.append(str(py_file.relative_to(plugin_dir)))
    
    # Find all UI files
    ui_files = []
    for ui_file in plugin_dir.rglob('*.ui'):
        ui_files.append(str(ui_file.relative_to(plugin_dir)))
    
    # Create .pro file content
    pro_content = f"""# RedBasica Export Plugin Translation Project File
# Generated automatically by update_translations.py

SOURCES = {' '.join(python_files)}
FORMS = {' '.join(ui_files)}

TRANSLATIONS = i18n/redbasica_export_en.ts \\
               i18n/redbasica_export_pt.ts

CODECFORTR = UTF-8
"""
    
    with open(pro_file, 'w', encoding='utf-8') as f:
        f.write(pro_content)
    
    return pro_file


def update_translations(plugin_dir: Path, pylupdate_path: str) -> bool:
    """
    Update translation files using pylupdate.
    
    Args:
        plugin_dir: Path to plugin directory
        pylupdate_path: Path to pylupdate executable
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create temporary .pro file
        pro_file = create_pro_file(plugin_dir)
        
        # Run pylupdate
        result = subprocess.run([pylupdate_path, str(pro_file)],
                              capture_output=True, text=True, cwd=plugin_dir)
        
        # Clean up .pro file
        pro_file.unlink()
        
        if result.returncode == 0:
            print("✓ Translation files updated successfully")
            if result.stdout:
                print(f"Output: {result.stdout}")
            return True
        else:
            print(f"✗ Failed to update translations: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error updating translations: {e}")
        return False


def add_missing_translations(ts_file: Path):
    """
    Add any missing translations that might not be caught by pylupdate.
    
    Args:
        ts_file: Path to .ts file
    """
    try:
        # Parse existing .ts file
        tree = ET.parse(ts_file)
        root = tree.getroot()
        
        # Find the RedBasicaExport context
        context = None
        for ctx in root.findall('context'):
            name_elem = ctx.find('name')
            if name_elem is not None and name_elem.text == 'RedBasicaExport':
                context = ctx
                break
        
        if context is None:
            # Create context if it doesn't exist
            context = ET.SubElement(root, 'context')
            name_elem = ET.SubElement(context, 'name')
            name_elem.text = 'RedBasicaExport'
        
        # Get existing messages
        existing_messages = set()
        for message in context.findall('message'):
            source = message.find('source')
            if source is not None:
                existing_messages.add(source.text)
        
        # Additional messages that might be missed
        additional_messages = [
            # UI text that might not be in UI files
            'Required Fields',
            'Optional Fields',
            'Calculated Fields',
            'Field Mapping',
            'Auto Mapping',
            'Manual Mapping',
            'Validation Status',
            'Export Progress',
            'Processing...',
            'Completed',
            'Failed',
            'Warning',
            'Error',
            'Information',
            'Success',
            # File dialog filters
            'DXF Files (*.dxf)',
            'All Files (*.*)',
            # Common button text
            'Yes',
            'No',
            'Close',
            'Help',
            'About',
        ]
        
        # Add missing messages
        added_count = 0
        for msg_text in additional_messages:
            if msg_text not in existing_messages:
                message = ET.SubElement(context, 'message')
                source = ET.SubElement(message, 'source')
                source.text = msg_text
                translation = ET.SubElement(message, 'translation')
                translation.set('type', 'unfinished')
                added_count += 1
        
        if added_count > 0:
            # Write back to file
            tree.write(ts_file, encoding='utf-8', xml_declaration=True)
            print(f"✓ Added {added_count} additional messages to {ts_file.name}")
        
    except Exception as e:
        print(f"✗ Error adding missing translations to {ts_file.name}: {e}")


def main():
    """Main function to update translation files."""
    # Get script directory and plugin root
    script_dir = Path(__file__).parent
    plugin_dir = script_dir.parent
    i18n_dir = plugin_dir / 'i18n'
    
    print("RedBasica Export - Translation Updater")
    print("=" * 40)
    
    # Check if i18n directory exists
    if not i18n_dir.exists():
        print(f"✗ i18n directory not found: {i18n_dir}")
        return 1
    
    # Find pylupdate executable
    pylupdate_path = find_pylupdate()
    if not pylupdate_path:
        print("✗ pylupdate executable not found!")
        print("Please install Qt development tools or add pylupdate to PATH")
        return 1
    
    print(f"Using pylupdate: {pylupdate_path}")
    print()
    
    # Update translation files
    if update_translations(plugin_dir, pylupdate_path):
        print("✓ Base translation update completed")
    else:
        print("✗ Failed to update translations")
        return 1
    
    # Add missing translations to each .ts file
    ts_files = list(i18n_dir.glob('redbasica_export_*.ts'))
    for ts_file in ts_files:
        add_missing_translations(ts_file)
    
    print()
    print("Translation update complete!")
    print("Next steps:")
    print("1. Review and translate strings in .ts files")
    print("2. Run compile_translations.py to generate .qm files")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())