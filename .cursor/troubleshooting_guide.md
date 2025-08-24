# RedBasica Export - Troubleshooting Guide

## Common Issues & Solutions

### 1. Color Issues in AutoCAD/DXF Viewers

#### Problem: Labels/arrows appear wrong color
**Symptoms**: ESG_NUMERO, ESG_TEXTO, ESG_SETA show blue instead of white
**Root Cause**: Explicit color assignments override layer colors
**Solution**: Ensure all entities use `'color': 256` (ByLayer) in dxf_exporter.py
**Check locations**:
- Line ~1496: NUMERO text entities
- Line ~1526: TEXTO text entities  
- Line ~1607: SETA arrow blocks

#### Problem: All entities same color
**Cause**: Layer definitions incorrect in template_manager.py
**Fix**: Verify LAYER_DEFINITIONS color assignments:
- REDE: 5 (blue), NUMERO/TEXTO/SETA: 7 (white), TEXTOPVS/PV: 1 (red)

### 2. Plugin Icon Issues

#### Problem: Toolbar icon not updating
**Cause**: QGIS caches icons, Qt resources not refreshed
**Solutions** (in order):
1. Plugin Manager: Disable/re-enable plugin
2. Clear cache: Delete `%APPDATA%\QGIS\QGIS3\profiles\default\cache`
3. Restart QGIS completely
4. Check resource compilation: resources.qrc → resources.py

#### Problem: Icon appears transparent/corrupted
**Cause**: Resource compilation failed or wrong file reference
**Check**:
- `metadata.txt` line 69: `icon=icon_2.png`
- `redbasica_export.py` line 185: `':/plugins/redbasica_export/icon_2.png'`
- `resources.qrc`: Contains `<file>icon_2.png</file>`

### 3. Configuration Loss Issues

#### Problem: Layer mappings disappear after file selection
**Cause**: Configuration not saved immediately after mapping dialog
**Solution**: Implemented in main_export_dialog.py
**Check lines**:
- 210-213: Pipes mapping save
- 243-246: Junctions mapping save

### 4. Text/Label Positioning Issues

#### Problem: Upside-down text labels
**Cause**: Text rotation not bounded properly
**Solution**: Text rotation logic in geometry_processor.py
```python
while rot > 90: rot -= 180
while rot < -90: rot += 180
```

#### Problem: Overlapping manhole labels  
**Cause**: Text width calculation or spacing issues
**Solution**: Fine-tuned values in dxf_exporter.py:
- Text width factor: 0.93
- Vertical spacing: 1.4 × text_height
- Position corrections: -7.82 units left, +1.35 units up

### 5. Scale and Sizing Issues

#### Problem: Text/arrows too small/large
**Cause**: Scale factor calculation inconsistent with QEsg
**Solution**: Always use QEsg standard: `sc = scale_factor / 2000.0`
**Text height**: `3 * sc`

#### Problem: Arrow blocks not visible
**Cause**: Arrow created as lines instead of solid blocks
**Solution**: Use `add_solid()` method with triangle points:
`[(4*sc, 0), (-4*sc, -1.33*sc), (-4*sc, 1.33*sc)]`

## Debugging Tips

### Enable Debug Output
- Check console for "DEBUG:" messages in dxf_exporter.py
- Verify entity creation success/failure

### Verify Layer Creation
```python
# Check if layers exist with correct colors
for layer in doc.layers:
    print(f"Layer: {layer.dxf.name}, Color: {layer.dxf.color}")
```

### Test Export with Minimal Data
- Single pipe, single junction
- Verify all components (line, labels, arrows, manhole) appear correctly

### AutoCAD Testing Checklist
1. Layer colors match specification
2. Text readable (not upside-down)
3. Arrows visible and pointing correct direction
4. Manhole labels properly positioned with leaders
5. No duplicate labels
6. Proper 3D elevations if enabled

## Performance Notes
- Large datasets: Consider progress callbacks
- Memory usage: ezdxf handles efficiently, but watch for very large networks
- File size: DXF files can be large with extensive labeling

## Recovery Procedures

### If plugin fails to load:
1. Check QGIS Python console for errors
2. Verify all files present (especially resources.py)
3. Re-enable in Plugin Manager
4. Check permissions on plugin directory

### If export produces empty/corrupt DXF:
1. Verify layer selection and field mapping
2. Check for NULL/invalid data in source layers
3. Test with simplified configuration first
4. Check write permissions on output directory