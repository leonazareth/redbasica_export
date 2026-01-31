---
description: Workflow for debugging and fixing common export issues
---

# Troubleshooting RedBasica Export

Use this workflow when the user reports issues with the DXF export.

## 1. Identify the Symptom
- **Wrong Colors?** (Blue instead of White) -> See "Color Issues"
- **Missing Icons?** -> See "Icon Issues"
- **Upside Down Text?** -> See "Geometry Issues"
- **Data Not Saving?** -> See "Configuration Issues"

## 2. Common Fixes

### Color Issues (Blue Text/Arrows)
**Check**: `core/dxf_exporter.py`
**Action**:
1. Find the entity creation code (text, block insertion).
2. Check `dxfattribs`.
3. **Change**: Replace `'color': 5` (or any constant) with `'color': 256` (ByLayer).
4. **Verify**: Ensure the Layer definition in `core/template_manager.py` has the correct color (e.g., Red=1, Blue=5, White=7).

### Icon Issues
**Action**:
1. Run `pyrcc5 -o resources.py resources.qrc`.
2. Reload plugin in QGIS.

### Geometry Issues
**Action**:
1. Check `core/geometry_processor.py`.
2. Ensure rotation normalization is active:
   ```python
   while rot > 90: rot -= 180
   while rot < -90: rot += 180
   ```
3. Check scale factors match QEsg: `sc = scale_factor / 2000.0`.

## 3. Verification
After applying a fix:
1. Reload Plugin.
2. Run an export with a small dataset.
3. Open DXF in a viewer (TrueView, AutoCAD, or online viewer).
4. Verify the specific symptom is resolved.
