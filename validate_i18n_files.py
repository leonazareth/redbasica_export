#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for internationalization files.

This script validates the structure and content of translation files
without requiring QGIS environment.
"""

import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def validate_ts_file(ts_file: Path) -> bool:
    """
    Validate a .ts translation file.
    
    Args:
        ts_file: Path to .ts file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        print(f"Validating {ts_file.name}...")
        
        # Parse XML
        tree = ET.parse(ts_file)
        root = tree.getroot()
        
        # Check root element
        if root.tag != 'TS':
            print(f"  ✗ Invalid root element: {root.tag}")
            return False
        
        # Check language attribute
        language = root.get('language')
        if not language:
            print(f"  ✗ Missing language attribute")
            return False
        
        print(f"  Language: {language}")
        
        # Count contexts and messages
        contexts = root.findall('context')
        total_messages = 0
        translated_messages = 0
        
        for context in contexts:
            context_name = context.find('name')
            if context_name is not None:
                print(f"  Context: {context_name.text}")
            
            messages = context.findall('message')
            total_messages += len(messages)
            
            for message in messages:
                translation = message.find('translation')
                if translation is not None and translation.get('type') != 'unfinished':
                    if translation.text and translation.text.strip():
                        translated_messages += 1
        
        print(f"  Messages: {total_messages} total, {translated_messages} translated")
        
        if total_messages > 0:
            completion = (translated_messages / total_messages) * 100
            print(f"  Completion: {completion:.1f}%")
        
        print(f"  ✓ {ts_file.name} is valid")
        return True
        
    except ET.ParseError as e:
        print(f"  ✗ XML parse error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Validation error: {e}")
        return False


def check_qm_files(i18n_dir: Path) -> bool:
    """
    Check if compiled .qm files exist and are newer than .ts files.
    
    Args:
        i18n_dir: Path to i18n directory
        
    Returns:
        bool: True if all .qm files are up to date
    """
    print("\nChecking compiled translation files...")
    
    ts_files = list(i18n_dir.glob('redbasica_export_*.ts'))
    all_good = True
    
    for ts_file in ts_files:
        qm_file = ts_file.with_suffix('.qm')
        
        if not qm_file.exists():
            print(f"  ✗ Missing compiled file: {qm_file.name}")
            all_good = False
        else:
            ts_mtime = ts_file.stat().st_mtime
            qm_mtime = qm_file.stat().st_mtime
            
            if ts_mtime > qm_mtime:
                print(f"  ⚠ {qm_file.name} is older than {ts_file.name}")
                all_good = False
            else:
                print(f"  ✓ {qm_file.name} is up to date")
    
    return all_good


def validate_file_structure(plugin_dir: Path) -> bool:
    """
    Validate the i18n file structure.
    
    Args:
        plugin_dir: Path to plugin directory
        
    Returns:
        bool: True if structure is valid
    """
    print("Validating i18n file structure...")
    
    i18n_dir = plugin_dir / 'i18n'
    if not i18n_dir.exists():
        print("  ✗ i18n directory not found")
        return False
    
    print(f"  ✓ i18n directory exists: {i18n_dir}")
    
    # Check for required files
    required_files = [
        'redbasica_export_en.ts',
        'redbasica_export_pt.ts',
    ]
    
    all_exist = True
    for filename in required_files:
        file_path = i18n_dir / filename
        if file_path.exists():
            print(f"  ✓ {filename} exists")
        else:
            print(f"  ✗ {filename} missing")
            all_exist = False
    
    return all_exist


def main():
    """Main validation function."""
    plugin_dir = Path(__file__).parent
    i18n_dir = plugin_dir / 'i18n'
    
    print("RedBasica Export - I18n Validation")
    print("=" * 40)
    
    # Validate file structure
    if not validate_file_structure(plugin_dir):
        print("\n❌ File structure validation failed")
        return 1
    
    # Validate .ts files
    print("\nValidating translation files...")
    ts_files = list(i18n_dir.glob('redbasica_export_*.ts'))
    
    if not ts_files:
        print("  ✗ No translation files found")
        return 1
    
    all_valid = True
    for ts_file in ts_files:
        if not validate_ts_file(ts_file):
            all_valid = False
    
    if not all_valid:
        print("\n❌ Translation file validation failed")
        return 1
    
    # Check compiled files
    qm_files_ok = check_qm_files(i18n_dir)
    
    # Summary
    print("\n" + "=" * 40)
    if all_valid and qm_files_ok:
        print("🎉 All i18n files are valid and up to date!")
        return 0
    elif all_valid:
        print("✅ Translation files are valid")
        print("⚠ Some compiled files may need updating")
        print("Run: python scripts/compile_translations.py")
        return 0
    else:
        print("❌ Some validation issues found")
        return 1


if __name__ == '__main__':
    sys.exit(main())