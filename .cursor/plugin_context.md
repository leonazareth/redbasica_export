# RedBasica Export Plugin - Context Summary

## Plugin Overview
**Name**: RedBasica Export - Flexible Sewerage DXF Export
**Version**: 1.0.0  
**Author**: Leonardo Nazareth
**Purpose**: Professional DXF export for sewerage networks with flexible layer selection and intelligent field mapping

## Key Architecture Components

### Core Files Structure
```
redbasica_export/
├── core/
│   ├── dxf_exporter.py          # Main export engine with QEsg-compatible output
│   ├── template_manager.py      # Layer definitions and DXF template handling
│   ├── field_definitions.py     # Standard sewerage network field schemas
│   └── configuration.py         # Settings persistence
├── ui/
│   └── main_export_dialog.py    # Primary user interface
├── QEsg/                        # Reference implementation for compatibility
├── metadata.txt                 # Plugin metadata (icon: icon_2.png)
├── resources.qrc/.py           # Qt resources (compiled for icon_2.png)
└── redbasica_export.py         # Main plugin entry point
```

## Critical Technical Implementations

### 1. QEsg-Compatible Export Engine
- **Scale calculation**: `sc = scale_factor / 2000.0`
- **Text height**: `3 * sc` (QEsg standard)
- **Arrow implementation**: Solid triangle blocks using `add_solid()`
- **Text rotation logic**: Prevents upside-down labels (-90° to +90° bounds)
- **3D elevation support**: Uses invert elevations for Z coordinates

### 2. Layer Color Scheme (DXF Colors)
```python
LAYER_DEFINITIONS = [
    ('REDE', 5, 'Sewage pipes/network'),             # BLUE - pipes only
    ('NUMERO', 7, 'Pipe ID labels'),                 # WHITE - pipe labels  
    ('TEXTO', 7, 'Pipe data labels'),                # WHITE - length-dia-slope
    ('SETA', 7, 'Flow direction arrows'),            # WHITE - flow arrows
    ('TEXTOPVS', 1, 'Manhole elevation data'),       # RED - manhole labels
    ('PV', 1, 'Manholes/junctions'),                 # RED - manhole circles
    ('NUMPV', 1, 'Manhole ID labels'),               # RED - manhole IDs
    # ... other layers
]
```

### 3. Manhole Label System (Enhanced from QEsg)
- **Two-segment leader lines**: Inclined then horizontal 
- **Precise positioning**: CT/CF left block, "h - ID" right block
- **Text spacing**: 1.4 × text height vertical, 0.93 width factor
- **Positioning offsets**: 7.82 units left, 1.35 units up corrections applied

## Recent Critical Fixes

### Color System Fix (MAJOR)
**Problem**: Labels and arrows appeared blue instead of white in AutoCAD
**Root Cause**: Explicit `'color': 5` assignments in dxf_exporter.py overrode layer colors
**Fix**: Changed to `'color': 256` (ByLayer) for proper color inheritance
**Files Modified**: 
- `core/dxf_exporter.py` lines 1496, 1526, 1607
- `core/template_manager.py` layer definitions

### Icon System Implementation
**Resource compilation**: icon_2.png → resources.qrc → resources.py (Qt resources)
**Main reference**: `redbasica_export.py` line 185: `':/plugins/redbasica_export/icon_2.png'`

### Configuration Persistence
**Issue**: Layer/attribute mappings lost when selecting output file
**Fix**: Immediate config saving in mapping dialogs (`main_export_dialog.py` lines 210-213, 243-246)

## Key Technical Patterns

### Text Creation (QEsg Style)
```python
from ezdxf.enums import TextEntityAlignment
text = msp.add_text(content, height=3*sc, dxfattribs={
    'rotation': rotation, 'style': 'ROMANS', 'color': 256, 'layer': layer_name
}).set_placement(position, align=TextEntityAlignment.BOTTOM_CENTER)
```

### Arrow Block Creation (QEsg Compatible)
```python
arrow_block = doc.blocks.new(name=block_name)
arrow_block.add_solid(
    [(4*sc, 0), (-4*sc, -1.33*sc), (-4*sc, 1.33*sc)],
    dxfattribs={'color': 256, 'layer': layer_name}  # ByLayer for proper colors
)
```

### Text Rotation Logic
```python
azim = start_point.azimuth(end_point)
rot = 90.0 - azim
while rot > 90: rot -= 180
while rot < -90: rot += 180
```

## Plugin Dependencies
- **Self-contained**: Bundled ezdxf library in `addon/` directory
- **No external dependencies** required for end users
- **QGIS**: Minimum version 3.16, tested up to 3.99

## Quality Assurance Notes
- **AutoCAD compatibility**: Verified layer colors, text positioning, arrow visibility
- **QEsg compatibility**: Maintains same output quality as original QEsg plugin
- **Configuration persistence**: Mappings survive dialog interactions
- **Error handling**: Comprehensive validation and graceful fallbacks

## Current Status
✅ **Fully functional** sewerage network DXF export
✅ **Color scheme fixed**: Blue pipes, white labels/arrows, red manholes  
✅ **Icon updated**: Using icon_2.png via Qt resources
✅ **Configuration stable**: No more mapping loss issues
✅ **QEsg-compatible**: Maintains professional output standards

## Development Environment
- **Platform**: Windows (OSGeo4W/QGIS installation)
- **Python**: 3.12+ (bundled with QGIS)
- **Qt Resources**: Compiled via custom Python script (pyrcc5 issues resolved)