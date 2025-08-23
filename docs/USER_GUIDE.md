# RedBasica Export - User Guide

## Overview

RedBasica Export is a professional QGIS plugin for exporting sewerage network designs to DXF format. Unlike traditional plugins that require specific layer names and field structures, RedBasica Export provides complete flexibility to work with ANY layer organization and field naming conventions.

## Key Features

### 🎯 Universal Compatibility
- Works with **ANY** layer names (not just 'PIPES' and 'JUNCTIONS')
- Supports **ANY** field naming conventions
- Compatible with existing QEsg projects and any other data structure

### 🧠 Intelligent Field Mapping
- Auto-suggests field mappings based on common patterns
- Supports QEsg field names (DC_ID, PVM, PVJ, etc.) as suggestions
- Allows completely manual mapping when needed
- Handles multilingual field names

### 🔧 Robust Data Processing
- Converts string numbers ("1.05", "2,50") to proper numeric values
- Handles NULL/empty values gracefully with appropriate defaults
- Supports Portuguese decimal notation (comma to dot conversion)
- Automatic type conversion with fallback to safe defaults

### 📐 Professional DXF Output
- Organized layer structure compatible with AutoCAD
- 3D geometry support with elevation data
- Flow arrows and comprehensive labeling
- QEsg-compatible styling and blocks
- Extended entity data (XDATA) for software compatibility

## Installation

### Method 1: QGIS Plugin Repository (Recommended)
1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins**
3. Search for "RedBasica Export"
4. Click **Install Plugin**

### Method 2: Manual Installation
1. Download the plugin ZIP file
2. Go to **Plugins** → **Manage and Install Plugins** → **Install from ZIP**
3. Select the downloaded ZIP file
4. Click **Install Plugin**

### Verification
After installation, you should see the RedBasica Export icon in your toolbar and the plugin listed in the **Plugins** menu.

## Quick Start Guide

### Step 1: Prepare Your Data
Ensure your QGIS project contains:
- **Pipe layer**: Line geometry representing sewerage pipes
- **Junction layer**: Point geometry representing manholes/junctions (optional)

Your layers can have ANY names and field structures - the plugin will adapt to your data.

### Step 2: Launch the Plugin
1. Click the RedBasica Export icon in the toolbar, or
2. Go to **Plugins** → **RedBasica Export** → **Export Sewerage Network**

### Step 3: Select Layers
1. In the **Pipe Layer** dropdown, select your pipe/line layer
2. In the **Junction Layer** dropdown, select your manhole/point layer (optional)
3. The plugin will automatically filter to show only compatible geometry types

### Step 4: Configure Field Mapping
1. Click **Configure Pipe Fields** to map your pipe attributes
2. Click **Configure Junction Fields** to map your junction attributes
3. The plugin will suggest mappings based on your field names
4. Adjust mappings as needed or set them manually

### Step 5: Set Export Options
- **Output Path**: Choose where to save your DXF file
- **Scale Factor**: Set the drawing scale (default: 2000)
- **Layer Prefix**: Add prefix to DXF layer names (default: "ESG_")
- **Template**: Use custom DXF template or default

### Step 6: Export
1. Click **Validate** to check your configuration
2. Review any warnings or errors
3. Click **Export** to generate your DXF file

## Detailed Workflows

### Working with Different Data Structures

#### Scenario 1: QEsg-Compatible Data
If your data follows QEsg conventions:
- Layers named 'PIPES' and 'JUNCTIONS'
- Fields like DC_ID, PVM, PVJ, CCM, CCJ
- The plugin will auto-detect and suggest these mappings

#### Scenario 2: Generic Sewerage Data
If your data uses generic names:
- Layers like 'sewer_lines', 'manholes'
- Fields like 'id', 'length', 'diameter', 'upstream', 'downstream'
- The plugin will suggest mappings based on common patterns

#### Scenario 3: Custom Data Structure
If your data uses unique naming:
- Any layer names: 'rede_esgoto', 'pocos_visita'
- Any field names: 'codigo', 'comprimento', 'diametro'
- Use manual mapping to connect your fields to required attributes

### Field Mapping Guide

#### Required Pipe Fields
- **Pipe ID**: Unique identifier for each pipe segment
- **Upstream Node**: Identifier of upstream manhole
- **Downstream Node**: Identifier of downstream manhole
- **Length**: Pipe length in meters
- **Diameter**: Pipe diameter in millimeters
- **Upstream Invert**: Upstream invert elevation
- **Downstream Invert**: Downstream invert elevation

#### Optional Pipe Fields
- **Upstream Ground**: Upstream ground elevation
- **Downstream Ground**: Downstream ground elevation
- **Slope**: Pipe slope (calculated if not provided)
- **Material**: Pipe material
- **Notes**: Additional observations

#### Junction Fields
- **Node ID**: Unique identifier for each junction
- **Ground Elevation**: Ground surface elevation (optional)
- **Invert Elevation**: Junction invert elevation (optional)

### Data Type Handling

The plugin automatically handles various data formats:

#### String Numbers
- "1.05" → 1.05
- "2,50" → 2.50 (Portuguese decimal notation)
- "150" → 150

#### NULL/Empty Values
- NULL → 0 (for numeric fields)
- Empty string → "" (for text fields)
- Missing values → appropriate defaults

#### Type Mismatches
- Text in numeric field → 0 (with warning)
- Invalid formats → default values (with logging)

## DXF Output Structure

### Layer Organization
The exported DXF contains organized layers:

- **ESG_REDE**: Main pipe network (color 172)
- **ESG_NUMERO**: Pipe ID labels (color 3)
- **ESG_TEXTO**: Pipe data labels (length-diameter-slope) (color 3)
- **ESG_TEXTOPVS**: Manhole elevation data (color 7)
- **ESG_PV**: Manhole symbols (color 3)
- **ESG_NUMPV**: Manhole ID labels (color 3)
- **ESG_SETA**: Flow direction arrows (color 172)
- **ESG_NO**: Dry point symbols (color 3)
- **ESG_AUX**: Auxiliary elements (color 241)
- **ESG_LIDER**: Leader lines (color 2)

### 3D Support
- Pipes exported with 3D coordinates when elevation data available
- Manholes include elevation information
- Compatible with 3D CAD workflows

### Blocks and Symbols
- Flow arrows using SETA blocks
- Manhole data blocks (pv_dados_NE, pv_dados_NO, pv_dados_SE, pv_dados_SO)
- Drop tube symbols (tr_curto, notq)

## Troubleshooting

### Common Issues

#### "No compatible layers found"
**Cause**: No line layers (for pipes) or point layers (for junctions) in project
**Solution**: Ensure your project contains vector layers with appropriate geometry types

#### "Required fields not mapped"
**Cause**: Essential fields like pipe_id, length, diameter not mapped
**Solution**: Use the field mapping dialog to assign your layer fields to required attributes

#### "Export failed - file permissions"
**Cause**: Cannot write to selected output location
**Solution**: Choose a different output location or check file permissions

#### "Invalid geometry detected"
**Cause**: Some features have invalid or corrupt geometry
**Solution**: Use QGIS geometry validation tools to fix invalid features

### Data Quality Tips

1. **Validate Geometry**: Use QGIS **Vector** → **Geometry Tools** → **Check Validity**
2. **Check Connectivity**: Ensure pipe endpoints connect to junction points
3. **Verify Elevations**: Check that invert elevations decrease in flow direction
4. **Review Field Data**: Look for NULL values, invalid numbers, or missing data

### Performance Optimization

- **Large Datasets**: Process in smaller sections if experiencing performance issues
- **Complex Geometry**: Simplify geometry if not needed for DXF output
- **Field Selection**: Map only necessary fields to improve processing speed

## Advanced Features

### Custom Templates
1. Create or modify DXF template files
2. Include custom blocks, layers, and styles
3. Specify template path in export options
4. Plugin will use template as base for export

### Calculated Fields
The plugin can calculate additional values:
- **Slope**: From invert elevations and length
- **Depth**: From ground and invert elevations
- **Flow Direction**: From elevation differences

### Extended Data (XDATA)
Exported DXF includes extended entity data for:
- Pipe attributes (diameter, length, material)
- Junction information (elevations, depths)
- Compatible with specialized CAD software

### Batch Processing
For multiple exports:
1. Save configuration settings
2. Use saved settings for subsequent exports
3. Automate with QGIS Processing framework (advanced users)

## Configuration Management

### Saving Settings
- Plugin automatically saves last used configuration
- Settings persist between QGIS sessions
- Include layer selections, field mappings, and export options

### Configuration Files
Settings stored in QGIS user profile:
- Field mappings
- Export preferences
- Template paths
- UI preferences

### Sharing Configurations
Export/import configuration files to share settings between users or projects.

## Integration with Other Software

### AutoCAD
- DXF files open directly in AutoCAD
- Layers, blocks, and styling preserved
- 3D geometry supported
- Extended data accessible through AutoCAD tools

### Other CAD Software
- Compatible with most DXF-supporting software
- Standard DXF format ensures broad compatibility
- Organized layer structure aids in CAD workflows

### GIS Software
- DXF can be imported back into QGIS or other GIS
- Maintains attribute data through extended properties
- Useful for round-trip workflows

## Support and Resources

### Documentation
- User Guide (this document)
- Developer Documentation
- API Reference
- Example datasets

### Community
- GitHub repository for issues and feature requests
- User forums and discussions
- Example projects and templates

### Professional Support
Contact the developer for:
- Custom modifications
- Training and consultation
- Enterprise deployment
- Integration services

## Appendix

### Supported File Formats
- **Input**: QGIS vector layers (Shapefile, GeoPackage, PostGIS, etc.)
- **Output**: DXF (AutoCAD Drawing Exchange Format)
- **Templates**: DXF template files

### System Requirements
- QGIS 3.16 or later
- Python 3.7 or later
- Windows, macOS, or Linux
- Sufficient disk space for output files

### License
This plugin is released under the GNU General Public License v3.0. See LICENSE file for details.

### Acknowledgments
- Based on QEsg plugin architecture
- Uses ezdxf library for DXF processing
- Inspired by the sewerage engineering community's needs for flexible export tools