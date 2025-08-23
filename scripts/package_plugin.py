#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plugin packaging script for RedBasica Export.

This script creates a distributable ZIP package of the plugin with all
necessary files and bundled dependencies.
"""

import os
import sys
import zipfile
import shutil
import argparse
from pathlib import Path
import json
from datetime import datetime


class PluginPackager:
    """Handles packaging of the RedBasica Export plugin."""
    
    def __init__(self, plugin_dir: str, output_dir: str = None):
        """
        Initialize packager.
        
        Args:
            plugin_dir: Path to plugin source directory
            output_dir: Output directory for packages (default: plugin_dir/dist)
        """
        self.plugin_dir = Path(plugin_dir).resolve()
        self.output_dir = Path(output_dir) if output_dir else self.plugin_dir / "dist"
        self.plugin_name = "redbasica_export"
        
        # Files and directories to include in package
        self.include_patterns = [
            "*.py",
            "*.ui",
            "*.qrc",
            "*.txt",
            "*.md",
            "metadata.txt",
            "icon.png",
            "icon_2.png",
            "LICENSE",
            "ui/",
            "core/",
            "addon/",
            "resources/",
            "i18n/",
            "docs/",
            "examples/",
        ]
        
        # Files and directories to exclude
        self.exclude_patterns = [
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            ".git/",
            ".gitignore",
            ".pytest_cache/",
            "test_*.py",
            "tests/",
            "scripts/",
            "*.log",
            "*.tmp",
            ".vscode/",
            ".idea/",
            "dist/",
            "build/",
        ]
    
    def create_package(self, version: str = None, include_examples: bool = True) -> str:
        """
        Create plugin package ZIP file.
        
        Args:
            version: Plugin version (read from metadata.txt if not provided)
            include_examples: Whether to include example datasets
            
        Returns:
            Path to created ZIP file
        """
        # Get version from metadata if not provided
        if not version:
            version = self._get_version_from_metadata()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate package filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{self.plugin_name}_v{version}_{timestamp}.zip"
        zip_path = self.output_dir / zip_filename
        
        print(f"Creating plugin package: {zip_filename}")
        print(f"Source directory: {self.plugin_dir}")
        print(f"Output path: {zip_path}")
        
        # Create ZIP package
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            self._add_plugin_files(zipf, include_examples)
        
        # Verify package
        package_size = zip_path.stat().st_size
        print(f"Package created successfully: {package_size:,} bytes")
        
        # Create package info
        self._create_package_info(zip_path, version, include_examples)
        
        return str(zip_path)
    
    def create_minimal_package(self, version: str = None) -> str:
        """
        Create minimal plugin package without examples and documentation.
        
        Args:
            version: Plugin version
            
        Returns:
            Path to created ZIP file
        """
        # Temporarily modify include patterns for minimal package
        original_patterns = self.include_patterns.copy()
        self.include_patterns = [p for p in self.include_patterns 
                               if not p.startswith(('docs/', 'examples/'))]
        
        try:
            # Get version
            if not version:
                version = self._get_version_from_metadata()
            
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate package filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{self.plugin_name}_minimal_v{version}_{timestamp}.zip"
            zip_path = self.output_dir / zip_filename
            
            print(f"Creating minimal plugin package: {zip_filename}")
            
            # Create ZIP package
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                self._add_plugin_files(zipf, include_examples=False)
            
            package_size = zip_path.stat().st_size
            print(f"Minimal package created: {package_size:,} bytes")
            
            return str(zip_path)
            
        finally:
            # Restore original patterns
            self.include_patterns = original_patterns
    
    def validate_package(self, zip_path: str) -> bool:
        """
        Validate plugin package contents.
        
        Args:
            zip_path: Path to ZIP package
            
        Returns:
            True if package is valid, False otherwise
        """
        print(f"Validating package: {zip_path}")
        
        required_files = [
            f"{self.plugin_name}/__init__.py",
            f"{self.plugin_name}/metadata.txt",
            f"{self.plugin_name}/redbasica_export.py",
        ]
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                file_list = zipf.namelist()
                
                # Check required files
                missing_files = []
                for required_file in required_files:
                    if required_file not in file_list:
                        missing_files.append(required_file)
                
                if missing_files:
                    print(f"✗ Missing required files: {missing_files}")
                    return False
                
                # Check for bundled libraries
                ezdxf_found = any('addon/ezdxf' in f for f in file_list)
                if not ezdxf_found:
                    print("⚠ Warning: ezdxf library not found in addon/")
                
                # Check metadata
                metadata_content = zipf.read(f"{self.plugin_name}/metadata.txt").decode('utf-8')
                if 'name=' not in metadata_content:
                    print("✗ Invalid metadata.txt format")
                    return False
                
                print(f"✓ Package validation successful")
                print(f"  Files: {len(file_list)}")
                print(f"  Size: {Path(zip_path).stat().st_size:,} bytes")
                
                return True
                
        except Exception as e:
            print(f"✗ Package validation failed: {e}")
            return False
    
    def _add_plugin_files(self, zipf: zipfile.ZipFile, include_examples: bool = True):
        """Add plugin files to ZIP archive."""
        added_files = 0
        
        for root, dirs, files in os.walk(self.plugin_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(d + "/")]
            
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.plugin_dir)
                
                # Check if file should be included
                if self._should_include(str(relative_path), include_examples):
                    # Add to ZIP with plugin name as root directory
                    zip_path = f"{self.plugin_name}/{relative_path}"
                    zipf.write(file_path, zip_path)
                    added_files += 1
        
        print(f"Added {added_files} files to package")
    
    def _should_include(self, file_path: str, include_examples: bool = True) -> bool:
        """Check if file should be included in package."""
        # Check exclude patterns first
        if self._should_exclude(file_path):
            return False
        
        # Check examples
        if not include_examples and file_path.startswith('examples/'):
            return False
        
        # Check include patterns
        for pattern in self.include_patterns:
            if pattern.endswith('/'):
                # Directory pattern
                if file_path.startswith(pattern):
                    return True
            elif '*' in pattern:
                # Wildcard pattern
                import fnmatch
                if fnmatch.fnmatch(file_path, pattern):
                    return True
            else:
                # Exact match
                if file_path == pattern:
                    return True
        
        return False
    
    def _should_exclude(self, file_path: str) -> bool:
        """Check if file should be excluded from package."""
        for pattern in self.exclude_patterns:
            if pattern.endswith('/'):
                # Directory pattern
                if file_path.startswith(pattern) or f"/{pattern}" in file_path:
                    return True
            elif '*' in pattern:
                # Wildcard pattern
                import fnmatch
                if fnmatch.fnmatch(file_path, pattern):
                    return True
            else:
                # Exact match
                if file_path == pattern or file_path.endswith(f"/{pattern}"):
                    return True
        
        return False
    
    def _get_version_from_metadata(self) -> str:
        """Extract version from metadata.txt file."""
        metadata_path = self.plugin_dir / "metadata.txt"
        
        if not metadata_path.exists():
            return "1.0.0"
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('version='):
                        return line.split('=', 1)[1].strip()
        except Exception as e:
            print(f"Warning: Could not read version from metadata.txt: {e}")
        
        return "1.0.0"
    
    def _create_package_info(self, zip_path: Path, version: str, include_examples: bool):
        """Create package information file."""
        info_path = zip_path.with_suffix('.json')
        
        package_info = {
            "plugin_name": self.plugin_name,
            "version": version,
            "package_file": zip_path.name,
            "package_size": zip_path.stat().st_size,
            "created_date": datetime.now().isoformat(),
            "include_examples": include_examples,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "packager_version": "1.0.0"
        }
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(package_info, f, indent=2, ensure_ascii=False)
        
        print(f"Package info saved: {info_path.name}")


def main():
    """Main packaging script entry point."""
    parser = argparse.ArgumentParser(description="Package RedBasica Export plugin")
    parser.add_argument("plugin_dir", help="Path to plugin source directory")
    parser.add_argument("-o", "--output", help="Output directory for packages")
    parser.add_argument("-v", "--version", help="Plugin version")
    parser.add_argument("--minimal", action="store_true", 
                       help="Create minimal package without examples")
    parser.add_argument("--no-examples", action="store_true",
                       help="Exclude examples from package")
    parser.add_argument("--validate", help="Validate existing package ZIP file")
    
    args = parser.parse_args()
    
    if args.validate:
        # Validate existing package
        packager = PluginPackager(args.plugin_dir, args.output)
        is_valid = packager.validate_package(args.validate)
        sys.exit(0 if is_valid else 1)
    
    # Create package
    packager = PluginPackager(args.plugin_dir, args.output)
    
    try:
        if args.minimal:
            zip_path = packager.create_minimal_package(args.version)
        else:
            include_examples = not args.no_examples
            zip_path = packager.create_package(args.version, include_examples)
        
        # Validate created package
        if packager.validate_package(zip_path):
            print(f"\n✓ Plugin package ready: {zip_path}")
        else:
            print(f"\n✗ Package validation failed: {zip_path}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error creating package: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()