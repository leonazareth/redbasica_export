# RedBasica Export - Installation Guide

## Overview

RedBasica Export is a self-contained QGIS plugin that requires no external dependencies. All necessary libraries are bundled with the plugin for immediate use after installation.

## System Requirements

### Minimum Requirements
- **QGIS**: Version 3.16 or later
- **Python**: Version 3.7 or later (included with QGIS)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 512 MB RAM minimum, 1 GB recommended
- **Disk Space**: 50 MB for plugin and bundled libraries

### Recommended Requirements
- **QGIS**: Version 3.22 LTR or later
- **Memory**: 2 GB RAM or more for large datasets
- **Disk Space**: 100 MB for plugin, examples, and working files

## Installation Methods

### Method 1: QGIS Plugin Repository (Recommended)

This is the easiest installation method for most users.

1. **Open QGIS**
2. **Access Plugin Manager**:
   - Go to **Plugins** → **Manage and Install Plugins**
   - Or press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)

3. **Search for Plugin**:
   - Click on the **All** tab
   - In the search box, type "RedBasica Export"
   - The plugin should appear in the results

4. **Install Plugin**:
   - Click on "RedBasica Export" in the results
   - Click **Install Plugin** button
   - Wait for installation to complete

5. **Verify Installation**:
   - The plugin should appear in the **Installed** tab
   - Look for the RedBasica Export icon in the toolbar
   - Check **Plugins** menu for "RedBasica Export" entry

### Method 2: Manual Installation from ZIP

Use this method if installing from a downloaded ZIP file or for development versions.

1. **Download Plugin ZIP**:
   - Download the plugin ZIP file from the official source
   - Do not extract the ZIP file

2. **Install from ZIP**:
   - Open QGIS
   - Go to **Plugins** → **Manage and Install Plugins**
   - Click on **Install from ZIP** tab
   - Click **...** button to browse for ZIP file
   - Select the downloaded ZIP file
   - Click **Install Plugin**

3. **Verify Installation**:
   - Check that installation completed successfully
   - Look for the plugin in the toolbar and menus

### Method 3: Manual Installation to Plugin Directory

For advanced users or custom installations.

1. **Locate QGIS Plugin Directory**:
   
   **Windows**:
   ```
   C:\Users\[username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
   ```
   
   **macOS**:
   ```
   ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
   ```
   
   **Linux**:
   ```
   ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
   ```

2. **Extract Plugin**:
   - Extract the plugin ZIP file
   - Copy the `redbasica_export` folder to the plugins directory

3. **Restart QGIS**:
   - Close and restart QGIS
   - The plugin should be available in the Plugin Manager

## Post-Installation Setup

### 1. Activate Plugin

If the plugin is not automatically activated:

1. **Open Plugin Manager**:
   - Go to **Plugins** → **Manage and Install Plugins**
   - Click on **Installed** tab

2. **Find RedBasica Export**:
   - Look for "RedBasica Export" in the list
   - Check the checkbox next to it to activate

3. **Verify Activation**:
   - Plugin icon should appear in toolbar
   - Menu entry should be available under **Plugins**

### 2. Verify Dependencies

The plugin includes all necessary dependencies, but you can verify they're working:

1. **Check Bundled Libraries**:
   - Open QGIS Python Console: **Plugins** → **Python Console**
   - Run the following commands:
   ```python
   import sys
   import os
   
   # Add plugin path
   plugin_path = os.path.join(os.path.expanduser('~'), '.local/share/QGIS/QGIS3/profiles/default/python/plugins/redbasica_export')
   addon_path = os.path.join(plugin_path, 'addon')
   sys.path.insert(0, addon_path)
   
   # Test ezdxf import
   try:
       import ezdxf
       print(f"ezdxf version: {ezdxf.__version__}")
       print("✓ ezdxf library loaded successfully")
   except ImportError as e:
       print(f"✗ ezdxf import failed: {e}")
   
   # Test c3d import (optional)
   try:
       import c3d
       print("✓ c3d library available")
   except ImportError:
       print("ℹ c3d library not available (optional)")
   ```

2. **Expected Output**:
   ```
   ezdxf version: 1.0.x
   ✓ ezdxf library loaded successfully
   ℹ c3d library not available (optional)
   ```

### 3. Initial Configuration

1. **Launch Plugin**:
   - Click the RedBasica Export icon in toolbar
   - Or go to **Plugins** → **RedBasica Export** → **Export Sewerage Network**

2. **Check Initial Settings**:
   - Plugin should open without errors
   - Default settings should be loaded
   - All UI elements should be responsive

## Troubleshooting Installation Issues

### Issue: Plugin Not Found in Repository

**Possible Causes**:
- Plugin not yet published to official repository
- QGIS version too old
- Repository connection issues

**Solutions**:
1. Check QGIS version (must be 3.16+)
2. Try refreshing plugin repository: **Settings** → **Reload repository**
3. Use manual installation method instead

### Issue: Installation Failed from ZIP

**Possible Causes**:
- Corrupted ZIP file
- Insufficient permissions
- QGIS plugin directory issues

**Solutions**:
1. Re-download ZIP file
2. Run QGIS as administrator (Windows)
3. Check available disk space
4. Try extracting manually to plugin directory

### Issue: Plugin Loads but Crashes

**Possible Causes**:
- Missing Python dependencies
- Corrupted installation
- QGIS version compatibility

**Solutions**:
1. Check QGIS Python Console for error messages
2. Reinstall plugin completely
3. Verify QGIS version compatibility
4. Check system requirements

### Issue: Bundled Libraries Not Working

**Possible Causes**:
- Incomplete installation
- Python path issues
- File permissions

**Solutions**:
1. Reinstall plugin completely
2. Check file permissions in plugin directory
3. Verify Python path configuration
4. Contact support with error details

### Issue: Plugin Icon Missing

**Possible Causes**:
- Plugin not activated
- Toolbar customization
- Installation incomplete

**Solutions**:
1. Check Plugin Manager → Installed tab
2. Activate plugin if not checked
3. Reset toolbar: **View** → **Toolbars** → **Reset**
4. Restart QGIS

## Uninstallation

### Method 1: Plugin Manager

1. **Open Plugin Manager**:
   - Go to **Plugins** → **Manage and Install Plugins**
   - Click **Installed** tab

2. **Uninstall Plugin**:
   - Find "RedBasica Export" in the list
   - Click **Uninstall Plugin** button
   - Confirm uninstallation

### Method 2: Manual Removal

1. **Locate Plugin Directory**:
   - Navigate to QGIS plugins directory (see installation paths above)
   - Find `redbasica_export` folder

2. **Remove Plugin**:
   - Delete the entire `redbasica_export` folder
   - Restart QGIS

3. **Clean Settings** (Optional):
   - Settings are stored in QGIS configuration
   - To remove completely: **Settings** → **Options** → **System** → **Reset**

## Upgrading

### Automatic Upgrade

1. **Check for Updates**:
   - Plugin Manager automatically checks for updates
   - Notification appears when updates available

2. **Install Update**:
   - Go to **Plugins** → **Manage and Install Plugins**
   - Click **Upgradeable** tab
   - Click **Upgrade Plugin** for RedBasica Export

### Manual Upgrade

1. **Backup Settings** (Recommended):
   - Export current configurations before upgrading
   - **Plugins** → **RedBasica Export** → **Export Settings**

2. **Uninstall Old Version**:
   - Follow uninstallation steps above
   - Keep settings backup

3. **Install New Version**:
   - Follow installation steps for new version
   - Import settings backup if needed

## Network Installation

For organizations installing on multiple computers:

### 1. Prepare Installation Package

1. **Download Plugin**:
   - Get plugin ZIP file from official source
   - Verify integrity and version

2. **Create Installation Script**:
   ```batch
   @echo off
   REM Windows batch script for network installation
   
   set PLUGIN_ZIP=redbasica_export.zip
   set QGIS_PLUGINS=%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins
   
   REM Create plugins directory if it doesn't exist
   if not exist "%QGIS_PLUGINS%" mkdir "%QGIS_PLUGINS%"
   
   REM Extract plugin
   powershell -command "Expand-Archive -Path '%PLUGIN_ZIP%' -DestinationPath '%QGIS_PLUGINS%' -Force"
   
   echo RedBasica Export installed successfully
   pause
   ```

### 2. Deploy to Workstations

1. **Copy Files**:
   - Distribute ZIP file and installation script
   - Or use network deployment tools

2. **Run Installation**:
   - Execute installation script on each workstation
   - Or use automated deployment systems

3. **Verify Installation**:
   - Test plugin functionality on sample workstations
   - Document any issues or customizations needed

## Development Installation

For developers working on the plugin:

### 1. Development Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/leonazareth/redbasica_export.git
   cd redbasica_export
   ```

2. **Create Symbolic Link**:
   
   **Linux/macOS**:
   ```bash
   ln -s $(pwd) ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/redbasica_export
   ```
   
   **Windows** (as Administrator):
   ```cmd
   mklink /D "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\redbasica_export" "%CD%"
   ```

3. **Install Development Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

### 2. Testing Installation

1. **Run Unit Tests**:
   ```bash
   python -m pytest tests/
   ```

2. **Test in QGIS**:
   - Start QGIS
   - Activate plugin in Plugin Manager
   - Test functionality with sample data

## Support

### Getting Help

1. **Documentation**:
   - User Guide: Complete feature documentation
   - API Reference: Developer documentation
   - Tutorials: Step-by-step guides

2. **Community Support**:
   - GitHub Issues: Bug reports and feature requests
   - User Forums: Community discussions
   - Email Support: Direct developer contact

3. **Professional Support**:
   - Custom installation assistance
   - Enterprise deployment support
   - Training and consultation services

### Reporting Issues

When reporting installation issues, please include:

1. **System Information**:
   - Operating system and version
   - QGIS version
   - Python version
   - Available memory and disk space

2. **Installation Details**:
   - Installation method used
   - Error messages (exact text)
   - Steps that led to the issue

3. **Log Files**:
   - QGIS log messages
   - Python console output
   - System error logs if applicable

This comprehensive installation guide should help users successfully install and configure RedBasica Export in various environments and scenarios.