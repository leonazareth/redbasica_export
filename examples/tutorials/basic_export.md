# Tutorial: Basic Sewerage Network Export

This tutorial walks you through your first export using RedBasica Export plugin. We'll use the sample dataset to demonstrate the complete workflow from layer selection to DXF generation.

## Prerequisites

- QGIS 3.16 or later installed
- RedBasica Export plugin installed and activated
- Sample dataset downloaded (available in `examples/sample_sewerage_network/`)

## Step 1: Load Sample Project

1. **Open QGIS**
2. **Load the sample project**:
   - Go to **Project** → **Open**
   - Navigate to `examples/sample_sewerage_network/`
   - Open `sewerage_network.qgz`

3. **Verify layers are loaded**:
   - You should see two layers in the Layers panel:
     - `pipes` (line layer with sewerage pipes)
     - `junctions` (point layer with manholes)

4. **Examine the data**:
   - Right-click on `pipes` layer → **Open Attribute Table**
   - Note the field names: `DC_ID`, `PVM`, `PVJ`, `LENGTH`, `DIAMETER`, etc.
   - Right-click on `junctions` layer → **Open Attribute Table**
   - Note the field names: `DC_ID`, `CT`, `CF`

## Step 2: Launch RedBasica Export

1. **Find the plugin**:
   - Look for the RedBasica Export icon in the toolbar
   - Or go to **Plugins** → **RedBasica Export** → **Export Sewerage Network**

2. **Open the export dialog**:
   - Click the RedBasica Export icon
   - The main export dialog will open

## Step 3: Select Layers

1. **Select pipe layer**:
   - In the **Pipe Layer** dropdown, select `pipes`
   - The plugin automatically filters to show only line layers

2. **Select junction layer**:
   - In the **Junction Layer** dropdown, select `junctions`
   - The plugin automatically filters to show only point layers

3. **Verify layer information**:
   - Layer names and feature counts should be displayed
   - Geometry types should be confirmed as compatible

## Step 4: Configure Field Mapping

### Configure Pipe Fields

1. **Open pipe field mapping**:
   - Click **Configure Pipe Fields** button
   - The Attribute Mapper dialog opens

2. **Review auto-suggested mappings**:
   - The plugin automatically suggests field mappings based on field names
   - You should see mappings like:
     - `pipe_id` → `DC_ID`
     - `upstream_node` → `PVM`
     - `downstream_node` → `PVJ`
     - `length` → `LENGTH`
     - `diameter` → `DIAMETER`

3. **Verify required fields**:
   - All required fields should have suggested mappings
   - Green checkmarks indicate successful mappings
   - Red warnings indicate missing or problematic mappings

4. **Adjust mappings if needed**:
   - Use dropdown menus to change field assignments
   - Set default values for unmapped optional fields

5. **Apply and close**:
   - Click **OK** to save the pipe field mappings

### Configure Junction Fields

1. **Open junction field mapping**:
   - Click **Configure Junction Fields** button

2. **Review junction mappings**:
   - `node_id` → `DC_ID`
   - `ground_elevation` → `CT` (if available)
   - `invert_elevation` → `CF` (if available)

3. **Apply and close**:
   - Click **OK** to save the junction field mappings

## Step 5: Set Export Options

1. **Choose output location**:
   - Click **Browse** next to **Output Path**
   - Navigate to your desired output directory
   - Enter filename: `my_first_export.dxf`
   - Click **Save**

2. **Review export settings**:
   - **Scale Factor**: Leave as `2000` (good for most drawings)
   - **Layer Prefix**: Leave as `ESG_` (standard prefix)
   - **Template**: Leave empty to use default template

3. **Configure output options**:
   - ✅ **Include Arrows**: Flow direction arrows on pipes
   - ✅ **Include Labels**: Pipe ID and data labels
   - ✅ **Include Elevations**: 3D elevation data

## Step 6: Validate Configuration

1. **Run validation**:
   - Click **Validate** button
   - The plugin checks your configuration for completeness

2. **Review validation results**:
   - ✅ Green messages indicate successful validation
   - ⚠️ Yellow warnings indicate potential issues (usually safe to proceed)
   - ❌ Red errors must be resolved before export

3. **Common validation messages**:
   - "All required fields mapped successfully"
   - "X pipe features and Y junction features ready for export"
   - "Output path is writable"

## Step 7: Export to DXF

1. **Start export**:
   - Click **Export** button
   - A progress dialog shows export status

2. **Monitor progress**:
   - Watch the progress bar and status messages
   - Export typically takes a few seconds for small datasets

3. **Review results**:
   - Success message shows number of features exported
   - Note the output file location

## Step 8: Verify DXF Output

1. **Open in CAD software**:
   - Open the generated DXF file in AutoCAD, LibreCAD, or similar
   - Or import back into QGIS to verify structure

2. **Check layer organization**:
   - Layers should be organized with `ESG_` prefix:
     - `ESG_REDE` - Pipe network lines
     - `ESG_NUMERO` - Pipe ID labels
     - `ESG_TEXTO` - Pipe data labels (length-diameter-slope)
     - `ESG_PV` - Junction symbols
     - `ESG_NUMPV` - Junction ID labels
     - `ESG_SETA` - Flow arrows (if enabled)

3. **Verify content**:
   - Pipe lines should match your QGIS layer geometry
   - Labels should display correct pipe IDs and data
   - Flow arrows should point in flow direction
   - Junction symbols should be at correct locations

## Step 9: Save Configuration (Optional)

1. **Save for reuse**:
   - In the main export dialog, click **Save Configuration**
   - Enter a name: `My Standard Export`
   - Click **Save**

2. **Load saved configuration**:
   - Next time, click **Load Configuration**
   - Select your saved configuration
   - All settings will be restored

## Troubleshooting Common Issues

### Issue: "No compatible layers found"
**Solution**: Ensure your project has line layers (for pipes) and/or point layers (for junctions)

### Issue: "Required fields not mapped"
**Solution**: 
1. Open the field mapping dialog
2. Manually assign required fields to available layer fields
3. Set default values for missing fields

### Issue: "Export failed - file permissions"
**Solution**: 
1. Choose a different output directory
2. Ensure you have write permissions to the selected location
3. Close any CAD software that might have the file open

### Issue: "Invalid geometry detected"
**Solution**:
1. Use QGIS **Vector** → **Geometry Tools** → **Check Validity**
2. Fix invalid geometries before export
3. Or enable "Skip invalid features" option

## Next Steps

Now that you've completed your first export, try these advanced features:

1. **Custom Field Mapping**: Work with layers that have different field names
2. **Template Usage**: Create and use custom DXF templates
3. **Batch Processing**: Export multiple projects with saved configurations
4. **Data Conversion**: Handle different data formats and types

## Additional Resources

- **User Guide**: Complete documentation of all features
- **Field Mapping Tutorial**: Advanced field mapping techniques
- **Custom Templates Tutorial**: Creating custom DXF templates
- **Troubleshooting Guide**: Solutions for common problems

Congratulations! You've successfully exported your first sewerage network to DXF format using RedBasica Export.