# QGIS Plugin Technical Rules

These rules are CRITICAL for the RedBasica Export plugin. The agent must adhere to them to ensure compatibility with AutoCAD and QEsg standards.

## 1. DXF Entity Colors
- **CONSTRAINT**: All DXF entities (TEXT, INSERT, ARROWS) **MUST** use `dxfattribs={'color': 256}`.
- **REASON**: Explicit colors (e.g. `color=5`) override ByLayer settings, causing blue text in AutoCAD instead of white.
- **BAD PATTERN**: `dxfattribs={'color': 5, ...}`
- **GOOD PATTERN**: `dxfattribs={'color': 256, ...}`

## 2. Text Rotation
- **CONSTRAINT**: Text rotation must be normalized to [-90, 90] degrees.
- **REASON**: Prevents labels from appearing upside down.
- **IMPLEMENTATION**:
  ```python
  while rot > 90: rot -= 180
  while rot < -90: rot += 180
  ```

## 3. Scale and Dimensions
- **CONSTRAINT**: Use exact QEsg formulas for all dimensions.
- **Scale Factor**: `sc = scale_factor / 2000.0`
- **Text Height**: `3 * sc`
- **Arrow Size**: `4 * sc`

## 4. Resource Handling
- **CONSTRAINT**: Never hardcode paths to icons. Use Qt Resources.
- **PATTERN**: `':/plugins/redbasica_export/icon_2.png'`

## 5. Dependencies
- **CONSTRAINT**: Do NOT pip install `ezdxf`.
- **REASON**: It is bundled in the `addon/` directory.
