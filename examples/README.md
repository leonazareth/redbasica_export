# RedBasica Export - Example Datasets and Templates

This directory contains example datasets, configuration templates, and sample projects to help users get started with the RedBasica Export plugin.

## Contents

### Sample Datasets
- `sample_sewerage_network/` - Complete example sewerage network project
- `qesg_compatible_data/` - Data structured like original QEsg plugin
- `generic_data/` - Generic sewerage data with common field names
- `custom_data/` - Custom data structure demonstrating flexibility

### Configuration Templates
- `configurations/` - Pre-configured export settings for different scenarios
- `field_mappings/` - Common field mapping templates
- `dxf_templates/` - Custom DXF templates with different styling

### Documentation
- `tutorials/` - Step-by-step tutorials for different use cases
- `screenshots/` - UI screenshots for documentation

## Quick Start

1. **Load Sample Project**: Open one of the sample QGIS projects
2. **Launch Plugin**: Start RedBasica Export from the toolbar
3. **Apply Template**: Load a matching configuration template
4. **Export**: Generate DXF output to see results

## Sample Projects

### 1. Complete Sewerage Network (`sample_sewerage_network/`)

A comprehensive example with:
- Pipe network with all required attributes
- Junction points with elevation data
- Proper connectivity and flow direction
- Mixed data types and formats

**Files:**
- `sewerage_network.qgz` - QGIS project file
- `pipes.shp` - Pipe network shapefile
- `junctions.shp` - Junction points shapefile
- `export_config.json` - Matching export configuration

### 2. QEsg Compatible Data (`qesg_compatible_data/`)

Data structured exactly like the original QEsg plugin:
- Layers named 'PIPES' and 'JUNCTIONS'
- Fields: DC_ID, PVM, PVJ, CCM, CCJ, etc.
- Demonstrates seamless migration from QEsg

**Files:**
- `qesg_project.qgz` - QGIS project file
- `PIPES.shp` - Pipe layer with QEsg field names
- `JUNCTIONS.shp` - Junction layer with QEsg field names
- `qesg_config.json` - QEsg-compatible configuration

### 3. Generic Data (`generic_data/`)

Common field naming patterns:
- Layers: 'sewer_lines', 'manholes'
- Fields: 'id', 'length', 'diameter', 'upstream', 'downstream'
- Demonstrates auto-mapping capabilities

**Files:**
- `generic_project.qgz` - QGIS project file
- `sewer_lines.shp` - Generic pipe layer
- `manholes.shp` - Generic junction layer
- `generic_config.json` - Generic field mapping configuration

### 4. Custom Data (`custom_data/`)

Unique naming conventions:
- Layers: 'rede_esgoto', 'pocos_visita'
- Fields: 'codigo', 'comprimento', 'diametro'
- Portuguese field names and decimal notation
- Demonstrates manual mapping flexibility

**Files:**
- `custom_project.qgz` - QGIS project file
- `rede_esgoto.shp` - Custom pipe layer
- `pocos_visita.shp` - Custom junction layer
- `custom_config.json` - Custom field mapping configuration

## Configuration Templates

### Export Configurations (`configurations/`)

Pre-configured export settings for common scenarios:

1. **`standard_export.json`** - Standard settings for most projects
2. **`high_detail_export.json`** - Maximum detail with all options enabled
3. **`simple_export.json`** - Minimal export for basic drawings
4. **`large_scale_export.json`** - Optimized for large-scale drawings
5. **`small_scale_export.json`** - Optimized for small-scale drawings

### Field Mapping Templates (`field_mappings/`)

Common field mapping patterns:

1. **`qesg_mappings.json`** - QEsg field name mappings
2. **`generic_mappings.json`** - Common generic field names
3. **`portuguese_mappings.json`** - Portuguese field names
4. **`english_mappings.json`** - English field names
5. **`multilingual_mappings.json`** - Mixed language field names

### DXF Templates (`dxf_templates/`)

Custom DXF templates with different styling:

1. **`standard_template.dxf`** - Standard QEsg-compatible template
2. **`minimal_template.dxf`** - Minimal template with basic layers
3. **`detailed_template.dxf`** - Detailed template with extra blocks
4. **`custom_colors_template.dxf`** - Custom color scheme
5. **`metric_template.dxf`** - Metric units template

## Tutorials

### Tutorial 1: Basic Export (`tutorials/basic_export.md`)
Step-by-step guide for first-time users

### Tutorial 2: Field Mapping (`tutorials/field_mapping.md`)
Comprehensive guide to field mapping and auto-suggestions

### Tutorial 3: Custom Templates (`tutorials/custom_templates.md`)
Creating and using custom DXF templates

### Tutorial 4: Data Conversion (`tutorials/data_conversion.md`)
Handling different data formats and types

### Tutorial 5: Troubleshooting (`tutorials/troubleshooting.md`)
Common issues and solutions

## Data Formats Demonstrated

### Numeric Data Formats
- Integer: `150`, `200`, `300`
- Float: `1.05`, `2.50`, `0.001`
- String numbers: `"150"`, `"1.05"`, `"2,50"`
- Portuguese decimals: `"1,234"`, `"2,50"`
- Currency: `"R$ 1.234,56"`, `"$25.50"`
- With units: `"150mm"`, `"2.5m"`

### Text Data Formats
- Simple strings: `"PV001"`, `"PIPE_123"`
- With spaces: `"Pipe Section A"`, `"Manhole 001"`
- Special characters: `"PV-001"`, `"PIPE_A/B"`
- Portuguese: `"Tubo Principal"`, `"Poço de Visita"`

### NULL/Empty Value Handling
- NULL values from database
- Empty strings: `""`
- Whitespace: `"   "`
- Missing attributes

### Boolean Values
- True/False: `True`, `False`
- Yes/No: `"Yes"`, `"No"`, `"Sim"`, `"Não"`
- Numeric: `1`, `0`
- String: `"true"`, `"false"`

## Testing Scenarios

### Scenario 1: Perfect Data
All required fields mapped, no missing values, proper data types

### Scenario 2: Missing Fields
Some required fields not available, using default values

### Scenario 3: Data Type Mismatches
Numeric data stored as strings, conversion required

### Scenario 4: Invalid Geometry
Some features with invalid or corrupt geometry

### Scenario 5: Large Dataset
Thousands of features, performance testing

### Scenario 6: Multilingual Data
Mixed language field names and values

## Usage Instructions

### Loading Sample Projects

1. Open QGIS
2. Load one of the sample projects (`.qgz` files)
3. Verify layers are loaded correctly
4. Launch RedBasica Export plugin

### Applying Configuration Templates

1. In the export dialog, click "Load Configuration"
2. Browse to the `configurations/` directory
3. Select appropriate template for your scenario
4. Verify settings match your needs
5. Adjust as necessary

### Using Field Mapping Templates

1. In the attribute mapping dialog, click "Load Mappings"
2. Browse to the `field_mappings/` directory
3. Select template matching your field names
4. Review and adjust mappings
5. Save custom mappings for reuse

### Testing Export Results

1. Export to a test DXF file
2. Open in AutoCAD or compatible CAD software
3. Verify layer organization and styling
4. Check entity properties and extended data
5. Validate 3D coordinates if applicable

## Customization

### Creating Your Own Templates

1. **Export Configuration**: Export successful configurations as templates
2. **Field Mappings**: Save field mappings for similar projects
3. **DXF Templates**: Customize DXF templates with your preferred styling

### Sharing Templates

Templates can be shared between users and projects:
1. Export configuration to JSON file
2. Share file with team members
3. Import configuration in RedBasica Export
4. Customize as needed for specific projects

## Support

For questions about the example datasets or templates:
1. Check the tutorials for step-by-step guidance
2. Review the troubleshooting guide for common issues
3. Consult the main user documentation
4. Contact support for additional assistance

## Contributing

To contribute additional examples:
1. Create new sample datasets following the established structure
2. Include complete QGIS projects with all necessary files
3. Provide matching configuration templates
4. Document the use case and field mappings
5. Submit via the project repository