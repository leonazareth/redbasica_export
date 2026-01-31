---
description: Expert knowledge for developing and maintaining the RedBasica Export QGIS plugin
---

# RedBasica Export Plugin Development Guide

This skill provides the context and rules for working on the RedBasica Export QGIS Plugin.

## Plugin Overview
**Name**: RedBasica Export - Flexible Sewerage DXF Export
**Purpose**: Professional DXF export for sewerage networks allowing flexible layer selection (unlike QEsg) while maintaining QEsg-compatible professional output standards.

## Architecture

The plugin follows a modular architecture:
- **core/**: Business logic (LayerManager, AttributeMapper, DxfExporter).
- **ui/**: Interface (MainExportDialog, LayerSelector).
- **addon/**: Bundled dependencies (`ezdxf`, `c3d`) - **NO external pip install required**.

### Key Components

- **LayerManager** (`core/layer_manager.py`): Handles discovery of ANY layer type (Line/Point) and validating geometry.
- **AttributeMapper** (`core/attribute_mapper.py`): Maps user fields to required internal fields (`pipe_id`, `upstream_node`, etc.) with data type conversion.
- **DxfExporter** (`core/dxf_exporter.py`): The heavy lifter. Uses `ezdxf` to generate the DXF.

## Critical Technical Implementation Rules

### 1. Color System (CRITICAL)
**Rule**: Entities MUST use `'color': 256` (ByLayer) to properly inherit layer colors.
**Reason**: Explicit colors (e.g., `'color': 5`) override layer settings and break AutoCAD visualization.

**Correct Entity Creation Pattern**:
```python
entity = msp.add_text(
    content,
    dxfattribs={
        'layer': layer_name,
        'color': 256,  # MUST BE 256
        'style': 'ROMANS'
    }
)
```

**Layer Color Definitions**:
- **REDE** (Pipes): Blue (5)
- **NUMERO/TEXTO/SETA**: White (7)
- **PV/TEXTOPVS**: Red (1)

### 2. Scale and Sizing (QEsg Compatibility)
**Rule**: Use exact QEsg formulas.
- **Scale Factor**: `sc = scale_factor / 2000.0`
- **Text Height**: `3 * sc`
- **Arrow Dimensions**: `4*sc` length.

### 3. Text Rotation
**Rule**: Text must never be upside down.
```python
while rot > 90: rot -= 180
while rot < -90: rot += 180
```

### 4. Qt Resources
**Rule**: Icons are loaded from `resources.py` which is compiled from `resources.qrc`.
**Reference**: `':/plugins/redbasica_export/icon_2.png'`

## Compilation & Deployment
**UI Files**: Start immediately (dynamic loading). No compilation needed.
**Resource Files**: Run `pyrcc5 -o resources.py resources.qrc` if `icon.png` changes.

## Troubleshooting Common Issues

### Blue Labels in AutoCAD
**Cause**: Entity has explicit color 5.
**Fix**: Change entity `dxfattribs` to `color: 256`.

### Icons Missing
**Cause**: `resources.py` stale or QGIS cache.
**Fix**: Compile resources, reload plugin, use "Plugin Reloader".

### Configuration Lost
**Cause**: Not saving config after dialogs.
**Fix**: Ensure `configuration.save()` is called in dialog accept slots.

## Coding Standards
- **Imports**: Use relative imports within the package.
- **Type Hinting**: Use `typing` module extensively.
- **Error Handling**: Catch specific exceptions (`ValidationError`, `ExportError`) and provide user-friendly messages.
