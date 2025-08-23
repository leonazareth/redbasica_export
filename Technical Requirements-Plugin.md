# Comprehensive Guide: Flexible Sewerage Network DXF Export Plugin

## 1. Plugin Architecture Overview

### Core Components Structure
```
SewageNetworkExporter/
├── __init__.py                          # Plugin initialization
├── metadata.txt                         # Plugin metadata
├── sewage_network_exporter.py          # Main plugin class
├── ui/
│   ├── main_dialog.py                   # Main export dialog
│   ├── main_dialog.ui                   # UI design file
│   ├── layer_selector_dialog.py        # Layer selection dialog
│   ├── layer_selector_dialog.ui        # Layer selection UI
│   ├── attribute_mapper_dialog.py      # Attribute mapping dialog
│   └── attribute_mapper_dialog.ui      # Attribute mapping UI
├── core/
│   ├── layer_manager.py                 # Layer validation and management
│   ├── attribute_mapper.py             # Attribute mapping logic
│   ├── dxf_exporter.py                 # DXF export engine
│   ├── geometry_processor.py           # Geometry processing utilities
│   └── template_manager.py             # DXF template management
├── resources/
│   ├── icons/                           # Plugin icons
│   ├── templates/                       # DXF templates
│   └── styles/                          # Default layer styles
└── vendor/
    └── ezdxf/                           # Bundled ezdxf library
```

## 2. User Interface Components

### 2.1 Main Export Dialog (`main_dialog.ui`)

**Essential Widgets:**
```python
class MainExportDialog(QDialog):
    def __init__(self):
        # File Selection Group
        self.file_path_edit = QLineEdit()           # Output DXF path
        self.browse_button = QPushButton("...")     # File browser
        
        # Layer Selection Group  
        self.pipes_layer_combo = QgsMapLayerComboBox()    # Pipes layer selector
        self.junctions_layer_combo = QgsMapLayerComboBox()  # Junctions layer selector
        self.configure_pipes_btn = QPushButton("Configure Pipes Mapping")
        self.configure_junctions_btn = QPushButton("Configure Junctions Mapping")
        
        # Export Options Group
        self.scale_spinbox = QSpinBox()             # Scale factor (1-1000000)
        self.layer_prefix_edit = QLineEdit()        # DXF layer prefix
        self.template_combo = QComboBox()           # Template selection
        
        # Advanced Options Group
        self.include_arrows_checkbox = QCheckBox()  # Flow direction arrows
        self.include_labels_checkbox = QCheckBox()  # Segment labels
        self.include_elevations_checkbox = QCheckBox()  # Elevation data
        self.label_format_edit = QLineEdit()        # Custom label format
        
        # Preview Group
        self.preview_tree = QTreeWidget()           # Export preview
        self.validation_text = QTextEdit()          # Validation messages
        
        # Action Buttons
        self.validate_button = QPushButton("Validate Layers")
        self.preview_button = QPushButton("Preview Export")
        self.export_button = QPushButton("Export DXF")
```

**Key Features:**
- **QgsMapLayerComboBox**: Automatically populates with project layers
- **Filter by geometry type**: Lines for pipes, points for junctions
- **Real-time validation**: Shows layer compatibility issues
- **Preview system**: Shows what will be exported before running

### 2.2 Layer Selector Dialog (`layer_selector_dialog.ui`)

```python
class LayerSelectorDialog(QDialog):
    def __init__(self):
        # Available Layers
        self.layers_list = QListWidget()            # All project layers
        self.geometry_filter = QComboBox()          # Filter by geometry type
        self.refresh_button = QPushButton("Refresh")
        
        # Layer Information
        self.layer_info_text = QTextEdit()          # Selected layer details
        self.field_list = QListWidget()             # Layer fields
        self.sample_data_table = QTableWidget()     # Sample feature data
        
        # Selection Actions
        self.select_button = QPushButton("Select Layer")
        self.cancel_button = QPushButton("Cancel")
```

### 2.3 Attribute Mapper Dialog (`attribute_mapper_dialog.ui`)

```python
class AttributeMapperDialog(QDialog):
    def __init__(self):
        # Required Attributes Section
        self.required_table = QTableWidget()        # Required → Layer field mapping
        
        # Optional Attributes Section  
        self.optional_table = QTableWidget()        # Optional → Layer field mapping
        
        # Default Values Section
        self.defaults_table = QTableWidget()        # Default values for missing fields
        
        # Label Configuration Section
        self.label_format_edit = QLineEdit()        # Label format string
        self.format_help_text = QLabel()            # Format help text
        self.preview_label = QLabel()               # Format preview
        
        # Validation Section
        self.validation_list = QListWidget()        # Mapping validation results
        
        # Actions
        self.auto_map_button = QPushButton("Auto-Map Fields")
        self.reset_button = QPushButton("Reset")
        self.apply_button = QPushButton("Apply Mapping")
```

## 3. Core Data Structures

### 3.1 Layer Configuration Classes

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class GeometryType(Enum):
    LINE = "LineString"
    POINT = "Point"
    POLYGON = "Polygon"

class FieldType(Enum):
    STRING = "String"
    INTEGER = "Integer"
    DOUBLE = "Double"
    BOOLEAN = "Boolean"

@dataclass
class RequiredField:
    name: str                    # Internal field name (e.g., "pipe_id")
    display_name: str           # User-friendly name (e.g., "Pipe Identifier")
    field_type: FieldType       # Expected data type
    description: str            # Field purpose description
    default_value: Optional[str] = None
    validation_rules: Optional[Dict] = None

@dataclass
class LayerMapping:
    layer_id: str               # QGIS layer ID
    layer_name: str             # Layer display name
    geometry_type: GeometryType # Required geometry type
    field_mappings: Dict[str, str]  # required_field -> layer_field
    default_values: Dict[str, str]  # required_field -> default_value
    is_valid: bool = False      # Validation status
    validation_errors: List[str] = None

@dataclass
class ExportConfiguration:
    pipes_mapping: LayerMapping
    junctions_mapping: LayerMapping
    output_path: str
    scale_factor: int = 2000
    layer_prefix: str = "ESG_"
    template_path: Optional[str] = None
    include_arrows: bool = True
    include_labels: bool = True
    include_elevations: bool = True
    label_format: str = "{length:.0f}-{diameter:.0f}-{slope:.5f}"
```

### 3.2 Required Fields Definitions

```python
# core/field_definitions.py
class SewageNetworkFields:
    PIPES_REQUIRED = [
        RequiredField("pipe_id", "Pipe Identifier", FieldType.STRING, 
                     "Unique identifier for each pipe segment"),
        RequiredField("upstream_node", "Upstream Node", FieldType.STRING,
                     "Identifier of upstream manhole"),
        RequiredField("downstream_node", "Downstream Node", FieldType.STRING,
                     "Identifier of downstream manhole"),
        RequiredField("length", "Length", FieldType.DOUBLE,
                     "Pipe length in meters"),
        RequiredField("diameter", "Diameter", FieldType.DOUBLE,
                     "Pipe diameter in millimeters"),
        RequiredField("upstream_invert", "Upstream Invert", FieldType.DOUBLE,
                     "Upstream invert elevation"),
        RequiredField("downstream_invert", "Downstream Invert", FieldType.DOUBLE,
                     "Downstream invert elevation"),
    ]
    
    PIPES_OPTIONAL = [
        RequiredField("upstream_ground", "Upstream Ground", FieldType.DOUBLE,
                     "Upstream ground elevation"),
        RequiredField("downstream_ground", "Downstream Ground", FieldType.DOUBLE,
                     "Downstream ground elevation"),
        RequiredField("slope", "Slope", FieldType.DOUBLE,
                     "Pipe slope in m/m"),
        RequiredField("material", "Material", FieldType.STRING,
                     "Pipe material"),
        RequiredField("notes", "Notes", FieldType.STRING,
                     "Additional notes"),
    ]
    
    JUNCTIONS_REQUIRED = [
        RequiredField("node_id", "Node Identifier", FieldType.STRING,
                     "Unique identifier for each junction"),
        RequiredField("ground_elevation", "Ground Elevation", FieldType.DOUBLE,
                     "Ground surface elevation"),
    ]
    
    JUNCTIONS_OPTIONAL = [
        RequiredField("invert_elevation", "Invert Elevation", FieldType.DOUBLE,
                     "Junction invert elevation"),
        RequiredField("depth", "Depth", FieldType.DOUBLE,
                     "Junction depth"),
        RequiredField("notes", "Notes", FieldType.STRING,
                     "Additional notes"),
    ]
```

## 4. Layer Management System

### 4.1 Layer Manager (`core/layer_manager.py`)

```python
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes
from typing import List, Dict, Optional

class LayerManager:
    def __init__(self):
        self.project = QgsProject.instance()
        
    def get_available_layers(self, geometry_type: GeometryType = None) -> List[QgsVectorLayer]:
        """Get all vector layers in project, optionally filtered by geometry type."""
        layers = []
        for layer in self.project.mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                if geometry_type is None:
                    layers.append(layer)
                elif self._matches_geometry_type(layer, geometry_type):
                    layers.append(layer)
        return layers
    
    def _matches_geometry_type(self, layer: QgsVectorLayer, geometry_type: GeometryType) -> bool:
        """Check if layer geometry matches required type."""
        geom_type = layer.geometryType()
        if geometry_type == GeometryType.LINE:
            return geom_type == QgsWkbTypes.LineGeometry
        elif geometry_type == GeometryType.POINT:
            return geom_type == QgsWkbTypes.PointGeometry
        elif geometry_type == GeometryType.POLYGON:
            return geom_type == QgsWkbTypes.PolygonGeometry
        return False
    
    def get_layer_fields(self, layer: QgsVectorLayer) -> Dict[str, FieldType]:
        """Get all fields in layer with their types."""
        fields = {}
        for field in layer.fields():
            field_type = self._qgs_type_to_field_type(field.type())
            fields[field.name()] = field_type
        return fields
    
    def validate_layer_mapping(self, mapping: LayerMapping, 
                              required_fields: List[RequiredField]) -> List[str]:
        """Validate if layer mapping satisfies requirements."""
        errors = []
        layer = self.project.mapLayer(mapping.layer_id)
        
        if not layer:
            errors.append(f"Layer not found: {mapping.layer_name}")
            return errors
            
        # Check geometry type
        if not self._matches_geometry_type(layer, mapping.geometry_type):
            errors.append(f"Invalid geometry type. Expected {mapping.geometry_type.value}")
        
        # Check required fields are mapped
        layer_fields = self.get_layer_fields(layer)
        for req_field in required_fields:
            if req_field.name not in mapping.field_mappings:
                if req_field.default_value is None:
                    errors.append(f"Required field '{req_field.display_name}' not mapped")
            else:
                mapped_field = mapping.field_mappings[req_field.name]
                if mapped_field not in layer_fields:
                    errors.append(f"Mapped field '{mapped_field}' not found in layer")
                elif layer_fields[mapped_field] != req_field.field_type:
                    errors.append(f"Field type mismatch for '{mapped_field}'")
        
        return errors
    
    def get_sample_data(self, layer: QgsVectorLayer, max_features: int = 5) -> List[Dict]:
        """Get sample feature data for preview."""
        sample_data = []
        for i, feature in enumerate(layer.getFeatures()):
            if i >= max_features:
                break
            feature_data = {}
            for field in layer.fields():
                feature_data[field.name()] = feature[field.name()]
            sample_data.append(feature_data)
        return sample_data
```

### 4.2 Attribute Mapper (`core/attribute_mapper.py`)

```python
class AttributeMapper:
    def __init__(self):
        self.field_definitions = SewageNetworkFields()
    
    def auto_map_fields(self, layer_fields: List[str], 
                       required_fields: List[RequiredField]) -> Dict[str, str]:
        """Attempt automatic field mapping based on common naming patterns."""
        mapping = {}
        
        # Common field name patterns
        patterns = {
            "pipe_id": ["id", "pipe_id", "dc_id", "segment_id", "pipe_name"],
            "upstream_node": ["upstream", "from_node", "pvm", "start_node"],
            "downstream_node": ["downstream", "to_node", "pvj", "end_node"],
            "length": ["length", "comprimento", "len", "distance"],
            "diameter": ["diameter", "diam", "dn", "size"],
            "upstream_invert": ["up_invert", "ccm", "invert_up", "start_elev"],
            "downstream_invert": ["down_invert", "ccj", "invert_down", "end_elev"],
            "node_id": ["id", "node_id", "dc_id", "pv_id"],
            "ground_elevation": ["ground", "surface", "cota_tn", "elevation"],
        }
        
        for req_field in required_fields:
            field_patterns = patterns.get(req_field.name, [])
            for layer_field in layer_fields:
                if any(pattern.lower() in layer_field.lower() for pattern in field_patterns):
                    mapping[req_field.name] = layer_field
                    break
        
        return mapping
    
    def validate_mapping(self, mapping: LayerMapping) -> List[str]:
        """Validate attribute mapping configuration."""
        errors = []
        
        # Check for required fields
        required_fields = (self.field_definitions.PIPES_REQUIRED 
                          if mapping.geometry_type == GeometryType.LINE 
                          else self.field_definitions.JUNCTIONS_REQUIRED)
        
        for req_field in required_fields:
            if req_field.name not in mapping.field_mappings:
                if req_field.name not in mapping.default_values:
                    errors.append(f"Required field '{req_field.display_name}' not mapped or defaulted")
        
        return errors
    
    def extract_feature_data(self, feature, mapping: LayerMapping) -> Dict[str, any]:
        """Extract data from feature using mapping configuration."""
        data = {}
        
        # Extract mapped fields
        for req_field, layer_field in mapping.field_mappings.items():
            data[req_field] = feature[layer_field]
        
        # Apply default values
        for req_field, default_value in mapping.default_values.items():
            if req_field not in data or data[req_field] is None:
                data[req_field] = default_value
        
        return data
```

## 5. DXF Export Engine

### 5.1 Main DXF Exporter (`core/dxf_exporter.py`)

```python
import ezdxf
from ezdxf import zoom
from ezdxf.enums import TextEntityAlignment
import math
from qgis.core import QgsGeometry, QgsPointXY

class DXFExporter:
    def __init__(self, config: ExportConfiguration):
        self.config = config
        self.drawing = None
        self.geometry_processor = GeometryProcessor()
        
    def export(self) -> bool:
        """Main export function."""
        try:
            # Initialize DXF document
            self._initialize_drawing()
            
            # Create layers
            self._create_dxf_layers()
            
            # Export pipes
            if self.config.pipes_mapping.is_valid:
                self._export_pipes()
            
            # Export junctions
            if self.config.junctions_mapping.is_valid:
                self._export_junctions()
            
            # Finalize and save
            self._finalize_drawing()
            self.drawing.saveas(self.config.output_path)
            
            return True
            
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")
    
    def _initialize_drawing(self):
        """Initialize DXF drawing with template or default."""
        if self.config.template_path:
            self.drawing = ezdxf.readfile(self.config.template_path)
        else:
            self.drawing = ezdxf.new('R2018')  # Modern DXF version
        
        # Set up app ID for extended data
        self.drawing.appids.new('SEWAGE_EXPORTER')
    
    def _create_dxf_layers(self):
        """Create organized DXF layers."""
        prefix = self.config.layer_prefix
        
        # Layer definitions: [name, color, description]
        layer_defs = [
            ('PIPES', 172, 'Sewage pipes/network'),
            ('PIPE_LABELS', 3, 'Pipe segment labels'),
            ('PIPE_ARROWS', 172, 'Flow direction arrows'),
            ('JUNCTIONS', 3, 'Manholes/junctions'),
            ('JUNCTION_LABELS', 3, 'Junction labels'),
            ('ELEVATION_DATA', 7, 'Elevation information'),
            ('ANNOTATIONS', 1, 'Additional annotations'),
        ]
        
        for name, color, description in layer_defs:
            layer_name = f"{prefix}{name}"
            self.drawing.layers.new(layer_name, dxfattribs={'color': color})
    
    def _export_pipes(self):
        """Export pipe network geometry and labels."""
        pipes_layer = QgsProject.instance().mapLayer(self.config.pipes_mapping.layer_id)
        msp = self.drawing.modelspace()
        prefix = self.config.layer_prefix
        
        # Calculate scale factor for text and symbols
        scale_factor = self.config.scale_factor / 2000.0
        
        for feature in pipes_layer.getFeatures():
            # Extract feature data using mapping
            data = AttributeMapper().extract_feature_data(feature, self.config.pipes_mapping)
            
            # Process geometry
            geometry = feature.geometry()
            if geometry.isMultipart():
                line_coords = geometry.asMultiPolyline()[0]
            else:
                line_coords = geometry.asPolyline()
            
            if len(line_coords) < 2:
                continue
                
            start_point = line_coords[0]
            end_point = line_coords[-1]
            
            # Create pipe line
            start_3d = (start_point.x(), start_point.y(), data.get('upstream_invert', 0))
            end_3d = (end_point.x(), end_point.y(), data.get('downstream_invert', 0))
            
            line = msp.add_line(start_3d, end_3d, 
                               dxfattribs={'layer': f"{prefix}PIPES", 'color': 256})
            
            # Add extended data for software compatibility
            self._add_pipe_extended_data(line, data)
            
            # Add labels if enabled
            if self.config.include_labels:
                self._add_pipe_labels(msp, start_point, end_point, data, scale_factor)
            
            # Add flow arrows if enabled
            if self.config.include_arrows and data.get('length', 0) > 20 * scale_factor:
                self._add_flow_arrow(msp, start_point, end_point, scale_factor)
            
            # Add elevation data if enabled
            if self.config.include_elevations:
                self._add_elevation_data(msp, start_point, end_point, data, scale_factor)
    
    def _export_junctions(self):
        """Export junction points and labels."""
        junctions_layer = QgsProject.instance().mapLayer(self.config.junctions_mapping.layer_id)
        msp = self.drawing.modelspace()
        prefix = self.config.layer_prefix
        scale_factor = self.config.scale_factor / 2000.0
        
        for feature in junctions_layer.getFeatures():
            data = AttributeMapper().extract_feature_data(feature, self.config.junctions_mapping)
            point = feature.geometry().asPoint()
            
            # Create junction symbol (circle)
            circle = msp.add_circle(
                center=(point.x(), point.y()),
                radius=2.99 * scale_factor,
                dxfattribs={'layer': f"{prefix}JUNCTIONS", 'color': 256}
            )
            
            # Add junction label
            label_pos = (point.x() + 3 * scale_factor, point.y() + 3 * scale_factor)
            msp.add_text(
                data.get('node_id', ''),
                height=3 * scale_factor,
                dxfattribs={
                    'layer': f"{prefix}JUNCTION_LABELS",
                    'color': 256,
                    'style': 'STANDARD'
                }
            ).set_placement(label_pos, align=TextEntityAlignment.BOTTOM_LEFT)
```

### 5.2 Geometry Processor (`core/geometry_processor.py`)

```python
from qgis.core import QgsPointXY
import math

class GeometryProcessor:
    """Utility class for geometric calculations."""
    
    @staticmethod
    def calculate_azimuth(pt1: QgsPointXY, pt2: QgsPointXY) -> float:
        """Calculate azimuth from pt1 to pt2 in degrees."""
        return pt1.azimuth(pt2)
    
    @staticmethod
    def calculate_midpoint(pt1: QgsPointXY, pt2: QgsPointXY) -> QgsPointXY:
        """Calculate midpoint between two points."""
        return QgsPointXY((pt1.x() + pt2.x()) / 2, (pt1.y() + pt2.y()) / 2)
    
    @staticmethod
    def point_along_line(pt1: QgsPointXY, pt2: QgsPointXY, distance: float) -> QgsPointXY:
        """Get point at specified distance from pt1 towards pt2."""
        total_length = math.sqrt(pt1.sqrDist(pt2))
        if total_length == 0:
            return pt1
        
        ratio = distance / total_length
        x = pt1.x() + ratio * (pt2.x() - pt1.x())
        y = pt1.y() + ratio * (pt2.y() - pt1.y())
        return QgsPointXY(x, y)
    
    @staticmethod
    def perpendicular_point(pt1: QgsPointXY, pt2: QgsPointXY, offset: float) -> QgsPointXY:
        """Get point perpendicular to line at pt1 with given offset."""
        length = math.sqrt(pt1.sqrDist(pt2))
        if length == 0:
            return pt1
        
        x = pt1.x() + offset * (pt2.y() - pt1.y()) / length
        y = pt1.y() + offset * (pt1.x() - pt2.x()) / length
        return QgsPointXY(x, y)
    
    @staticmethod
    def calculate_text_rotation(pt1: QgsPointXY, pt2: QgsPointXY) -> float:
        """Calculate text rotation to align with line direction."""
        azimuth = GeometryProcessor.calculate_azimuth(pt1, pt2)
        if azimuth < 0:
            azimuth += 360
        
        rotation = 90 - azimuth
        if 180 <= azimuth < 360:
            rotation -= 180
        
        return rotation
```

### 5.3 Template Manager (`core/template_manager.py`)

```python
import os
from typing import List, Dict

class TemplateManager:
    """Manage DXF templates and blocks."""
    
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.templates_dir = os.path.join(plugin_dir, 'resources', 'templates')
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """Get list of available DXF templates."""
        templates = []
        
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith('.dxf'):
                    template_path = os.path.join(self.templates_dir, file)
                    templates.append({
                        'name': os.path.splitext(file)[0],
                        'path': template_path,
                        'description': self._get_template_description(template_path)
                    })
        
        return templates
    
    def create_default_template(self) -> str:
        """Create a default template with standard blocks."""
        template_path = os.path.join(self.templates_dir, 'default_sewage.dxf')
        
        if not os.path.exists(template_path):
            doc = ezdxf.new('R2018')
            
            # Create standard text style
            doc.styles.new('ROMANS', {'font': 'romans.shx'})
            
            # Create arrow block
            arrow_block = doc.blocks.new('FLOW_ARROW')
            arrow_block.add_solid([(4, 0), (-4, -1.33), (-4, 1.33)], 
                                 dxfattribs={'color': 256})
            
            # Create manhole blocks for different orientations
            for direction in ['NE', 'NO', 'SE', 'SO']:
                block_name = f'MANHOLE_DATA_{direction}'
                manhole_block = doc.blocks.new(block_name)
                
                # Add attribute definitions for manhole data
                manhole_block.add_attdef('GROUND_ELEV', (0, 5), 
                                       dxfattribs={'height': 2.5, 'color': 7})
                manhole_block.add_attdef('INVERT_ELEV', (0, 2.5), 
                                       dxfattribs={'height': 2.5, 'color': 7})
                manhole_block.add_attdef('DEPTH', (0, 0), 
                                       dxfattribs={'height': 2.5, 'color': 7})
            
            doc.saveas(template_path)
        
        return template_path
    
    def _get_template_description(self, template_path: str) -> str:
        """Extract description from template file or return default."""
        # Could read from companion .txt file or DXF comments
        return "Custom DXF template"
```

## 6. Main Plugin Class

### 6.1 Plugin Entry Point (`sewage_network_exporter.py`)

```python
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject, Qgis
from qgis.utils import iface
import os.path

from .ui.main_dialog import MainExportDialog
from .core.layer_manager import LayerManager
from .core.template_manager import TemplateManager

class SewageNetworkExporter:
    """Main plugin class."""
    
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize components
        self.layer_manager = LayerManager()
        self.template_manager = TemplateManager(self.plugin_dir)
        
        # Initialize plugin directory
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'sewage_exporter_{locale}.qm')
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        
        self.actions = []
        self.menu = self.tr('&Sewage Network Exporter')
        self.first_start = None
    
    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('SewageNetworkExporter', message)
    
    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True, status_tip=None,
                   whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar."""
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        
        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)
        
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        
        self.actions.append(action)
        return action
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(self.plugin_dir, 'resources', 'icons', 'export_icon.png')
        self.add_action(
            icon_path,
            text=self.tr('Export Sewage Network to DXF'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )
        
        # Create default template if needed
        self.template_manager.create_default_template()
        
        self.first_start = True
    
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr('&Sewage Network Exporter'), action)
            self.iface.removeToolBarIcon(action)
    
    def run(self):
        """Run method that performs all the real work."""
        # Check if project has suitable layers
        line_layers = self.layer_manager.get_available_layers(GeometryType.LINE)
        point_layers = self.layer_manager.get_available_layers(GeometryType.POINT)
        
        if not line_layers:
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('No Suitable Layers'),
                self.tr('No line layers found in the project. Please add a sewage network layer.')
            )
            return
        
        # Create and show the dialog
        if self.first_start:
            self.first_start = False
            self.dlg = MainExportDialog(
                layer_manager=self.layer_manager,
                template_manager=self.template_manager
            )
        
        # Show the dialog
        self.dlg.show()
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        
        # See if OK was pressed
        if result:
            try:
                # Perform the export
                config = self.dlg.get_export_configuration()
                exporter = DXFExporter(config)
                
                if exporter.export():
                    self.iface.messageBar().pushMessage(
                        self.tr('Export Complete'),
                        self.tr(f'DXF exported successfully to: {config.output_path}'),
                        level=Qgis.Success,
                        duration=5
                    )
                
            except Exception as e:
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    self.tr('Export Error'),
                    self.tr(f'Export failed: {str(e)}')
                )
```

## 7. Implementation Steps

### 7.1 Phase 1: Basic Structure (Week 1-2)
1. **Set up plugin structure** using QGIS Plugin Builder
2. **Create basic UI dialogs** with Qt Designer
3. **Implement LayerManager** class for layer discovery
4. **Set up ezdxf integration** (bundle or dependency)

### 7.2 Phase 2: Core Functionality (Week 3-4)
1. **Implement AttributeMapper** with auto-mapping logic
2. **Create field validation system**
3. **Build basic DXF export engine**
4. **Add geometry processing utilities**

### 7.3 Phase 3: Advanced Features (Week 5-6)
1. **Implement template system**
2. **Add arrow and label generation**
3. **Create elevation data export**
4. **Build preview functionality**

### 7.4 Phase 4: Polish & Testing (Week 7-8)
1. **Add comprehensive error handling**
2. **Implement user preferences persistence**
3. **Create user documentation**
4. **Perform thorough testing**

## 8. Key Libraries and Dependencies

### 8.1 Required Libraries
```python
# Core QGIS
from qgis.core import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

# DXF handling
import ezdxf
from ezdxf import zoom
from ezdxf.enums import TextEntityAlignment

# Data handling
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from enum import Enum

# Standard library
import os
import math
import json
```

### 8.2 Plugin Dependencies (`metadata.txt`)
```ini
[general]
name=Sewage Network DXF Exporter
qgisMinimumVersion=3.16
description=Flexible DXF export for sewage network designs
version=1.0.0
author=Your Name
email=your.email@example.com

hasProcessingProvider=no
experimental=False

# Tags for plugin repository
tags=dxf,export,sewage,network,cad,autocad

# Plugin dependencies
requirements=ezdxf>=1.0.0
```

## 9. Configuration and Settings

### 9.1 Settings Management
```python
class PluginSettings:
    """Manage plugin settings and user preferences."""
    
    def __init__(self):
        self.settings = QSettings()
        self.settings.beginGroup('SewageNetworkExporter')
    
    def save_export_config(self, config: ExportConfiguration):
        """Save export configuration for reuse."""
        self.settings.setValue('last_scale_factor', config.scale_factor)
        self.settings.setValue('last_layer_prefix', config.layer_prefix)
        self.settings.setValue('last_template', config.template_path)
        self.settings.setValue('include_arrows', config.include_arrows)
        self.settings.setValue('include_labels', config.include_labels)
        self.settings.setValue('include_elevations', config.include_elevations)
    
    def load_export_config(self) -> Dict:
        """Load last used export configuration."""
        return {
            'scale_factor': self.settings.value('last_scale_factor', 2000, int),
            'layer_prefix': self.settings.value('last_layer_prefix', 'ESG_', str),
            'template_path': self.settings.value('last_template', '', str),
            'include_arrows': self.settings.value('include_arrows', True, bool),
            'include_labels': self.settings.value('include_labels', True, bool),
            'include_elevations': self.settings.value('include_elevations', True, bool),
        }
```
