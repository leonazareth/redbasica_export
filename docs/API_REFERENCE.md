# RedBasica Export - API Reference

## Overview

This document provides a comprehensive reference for the RedBasica Export plugin API. The plugin exposes both internal APIs for extension and external APIs for integration with other QGIS plugins.

## Core API Classes

### RedBasicaExportAPI

Main API class for programmatic access to plugin functionality.

```python
from redbasica_export.core.api import RedBasicaExportAPI

class RedBasicaExportAPI:
    """Main API for RedBasica Export plugin functionality."""
    
    def __init__(self):
        """Initialize API with default managers."""
        
    def get_available_layers(self, geometry_type: GeometryType = None) -> List[QgsVectorLayer]:
        """Get available vector layers from current QGIS project."""
        
    def suggest_field_mappings(self, layer: QgsVectorLayer, 
                             required_fields: List[RequiredField]) -> Dict[str, str]:
        """Suggest field mappings for given layer."""
        
    def validate_export_configuration(self, config: ExportConfiguration) -> List[str]:
        """Validate export configuration and return error messages."""
        
    def export_network(self, config: ExportConfiguration) -> ExportResult:
        """Export sewerage network to DXF format."""
```

## Data Structures

### GeometryType

Enumeration of supported geometry types.

```python
class GeometryType(Enum):
    LINE = "LineString"      # For pipe networks
    POINT = "Point"          # For junctions/manholes
    POLYGON = "Polygon"      # For catchment areas (future)
```

### FieldType

Enumeration of supported field data types.

```python
class FieldType(Enum):
    STRING = "String"        # Text fields
    INTEGER = "Integer"      # Whole numbers
    DOUBLE = "Double"        # Decimal numbers
    BOOLEAN = "Boolean"      # True/False values
```

### RequiredField

Definition of required fields for export.

```python
@dataclass
class RequiredField:
    name: str                           # Internal field identifier
    display_name: str                   # User-friendly display name
    field_type: FieldType              # Expected data type
    description: str                    # Field description/purpose
    default_value: Optional[str] = None # Default value if not mapped
    validation_rules: Optional[Dict] = None # Custom validation rules
    
    # Example usage
    pipe_id_field = RequiredField(
        name="pipe_id",
        display_name="Pipe Identifier",
        field_type=FieldType.STRING,
        description="Unique identifier for each pipe segment",
        default_value="UNKNOWN"
    )
```

### LayerMapping

Configuration for mapping layer fields to required attributes.

```python
@dataclass
class LayerMapping:
    layer_id: str                      # QGIS layer ID
    layer_name: str                    # Human-readable layer name
    geometry_type: GeometryType        # Required geometry type
    field_mappings: Dict[str, str]     # required_field -> layer_field
    default_values: Dict[str, str]     # required_field -> default_value
    is_valid: bool = False             # Validation status
    validation_errors: List[str] = None # Validation error messages
    
    # Example usage
    pipe_mapping = LayerMapping(
        layer_id="pipes_layer_123",
        layer_name="Sewer Pipes",
        geometry_type=GeometryType.LINE,
        field_mappings={
            "pipe_id": "DC_ID",
            "length": "LENGTH",
            "diameter": "DIAMETER"
        },
        default_values={
            "material": "PVC"
        }
    )
```

### ExportConfiguration

Complete configuration for DXF export.

```python
@dataclass
class ExportConfiguration:
    pipes_mapping: LayerMapping         # Pipe layer configuration
    junctions_mapping: LayerMapping     # Junction layer configuration
    output_path: str                    # Output DXF file path
    scale_factor: int = 2000           # Drawing scale factor
    layer_prefix: str = "ESG_"         # DXF layer prefix
    template_path: Optional[str] = None # Custom DXF template
    include_arrows: bool = True         # Include flow arrows
    include_labels: bool = True         # Include pipe labels
    include_elevations: bool = True     # Include elevation data
    label_format: str = "{length:.0f}-{diameter:.0f}-{slope:.5f}"
    
    # Example usage
    config = ExportConfiguration(
        pipes_mapping=pipe_mapping,
        junctions_mapping=junction_mapping,
        output_path="/path/to/output.dxf",
        scale_factor=1000,
        layer_prefix="SEWER_"
    )
```

### ExportResult

Result of export operation with status and details.

```python
@dataclass
class ExportResult:
    success: bool                       # Export success status
    output_path: str                    # Path to generated DXF file
    features_exported: int              # Number of features exported
    features_skipped: int               # Number of features skipped
    warnings: List[str]                 # Warning messages
    errors: List[str]                   # Error messages
    execution_time: float               # Export execution time in seconds
    
    # Example usage
    result = api.export_network(config)
    if result.success:
        print(f"Export successful: {result.features_exported} features exported")
    else:
        print(f"Export failed: {result.errors}")
```

## Core Manager Classes

### LayerManager

Manages layer discovery and validation.

```python
class LayerManager:
    """Manages QGIS layer operations for flexible export."""
    
    def __init__(self):
        """Initialize layer manager."""
        
    def get_available_layers(self, geometry_type: GeometryType = None) -> List[QgsVectorLayer]:
        """
        Get available vector layers from current QGIS project.
        
        Args:
            geometry_type: Optional filter by geometry type
            
        Returns:
            List of compatible vector layers
        """
        
    def get_layer_fields(self, layer: QgsVectorLayer) -> Dict[str, FieldType]:
        """
        Extract field information from layer.
        
        Args:
            layer: QGIS vector layer
            
        Returns:
            Dictionary mapping field names to field types
        """
        
    def validate_layer_compatibility(self, layer: QgsVectorLayer, 
                                   required_geometry: GeometryType) -> List[str]:
        """
        Validate layer compatibility for export.
        
        Args:
            layer: QGIS vector layer to validate
            required_geometry: Required geometry type
            
        Returns:
            List of validation error messages (empty if valid)
        """
        
    def get_sample_data(self, layer: QgsVectorLayer, max_features: int = 5) -> List[Dict]:
        """
        Get sample feature data for preview.
        
        Args:
            layer: QGIS vector layer
            max_features: Maximum number of sample features
            
        Returns:
            List of feature attribute dictionaries
        """
```

### AttributeMapper

Handles field mapping and data conversion.

```python
class AttributeMapper:
    """Manages attribute mapping and data conversion."""
    
    def __init__(self, data_converter: DataConverter):
        """Initialize with data converter."""
        
    def suggest_field_mappings(self, layer_fields: List[str], 
                             required_fields: List[RequiredField]) -> Dict[str, str]:
        """
        Suggest field mappings based on naming patterns.
        
        Args:
            layer_fields: Available field names in layer
            required_fields: Required field definitions
            
        Returns:
            Dictionary of suggested mappings (required_field -> layer_field)
        """
        
    def validate_mappings(self, mappings: Dict[str, str], 
                         required_fields: List[RequiredField]) -> List[str]:
        """
        Validate field mappings for completeness.
        
        Args:
            mappings: Current field mappings
            required_fields: Required field definitions
            
        Returns:
            List of validation error messages
        """
        
    def extract_feature_data(self, feature: QgsFeature, 
                           mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract and convert feature data using mappings.
        
        Args:
            feature: QGIS feature to extract data from
            mappings: Field mappings configuration
            
        Returns:
            Dictionary of converted feature data
        """
```

### DataConverter

Handles robust data type conversion.

```python
class DataConverter:
    """Robust data type conversion with error handling."""
    
    @staticmethod
    def to_string(value: Any) -> str:
        """
        Convert value to string with NULL handling.
        
        Args:
            value: Input value of any type
            
        Returns:
            String representation (empty string for NULL/None)
        """
        
    @staticmethod
    def to_double(value: Any) -> float:
        """
        Convert value to float with robust parsing.
        
        Args:
            value: Input value (string, number, or NULL)
            
        Returns:
            Float value (0.0 for invalid/NULL values)
            
        Examples:
            to_double("1.05") -> 1.05
            to_double("2,50") -> 2.50  # Portuguese decimal
            to_double(None) -> 0.0
            to_double("invalid") -> 0.0
        """
        
    @staticmethod
    def to_integer(value: Any) -> int:
        """
        Convert value to integer with error handling.
        
        Args:
            value: Input value of any type
            
        Returns:
            Integer value (0 for invalid/NULL values)
        """
        
    @staticmethod
    def convert_field_value(value: Any, target_type: FieldType) -> Any:
        """
        Convert value to specified field type.
        
        Args:
            value: Input value
            target_type: Target FieldType
            
        Returns:
            Converted value of appropriate type
        """
```

### DXFExporter

Core DXF export functionality.

```python
class DXFExporter:
    """Professional DXF export with comprehensive styling."""
    
    def __init__(self, template_manager: TemplateManager, 
                 geometry_processor: GeometryProcessor):
        """Initialize with required managers."""
        
    def export_network(self, config: ExportConfiguration) -> ExportResult:
        """
        Export complete sewerage network to DXF.
        
        Args:
            config: Complete export configuration
            
        Returns:
            ExportResult with status and details
        """
        
    def create_dxf_document(self, template_path: Optional[str] = None) -> ezdxf.Drawing:
        """
        Create DXF document from template or default.
        
        Args:
            template_path: Optional path to DXF template
            
        Returns:
            ezdxf Drawing object
        """
        
    def setup_layers(self, doc: ezdxf.Drawing, prefix: str = "ESG_") -> None:
        """
        Set up organized DXF layer structure.
        
        Args:
            doc: ezdxf Drawing object
            prefix: Layer name prefix
        """
        
    def export_pipes(self, doc: ezdxf.Drawing, pipe_data: List[Dict], 
                    config: ExportConfiguration) -> int:
        """
        Export pipe entities to DXF.
        
        Args:
            doc: ezdxf Drawing object
            pipe_data: List of pipe feature data
            config: Export configuration
            
        Returns:
            Number of pipes exported
        """
        
    def export_junctions(self, doc: ezdxf.Drawing, junction_data: List[Dict], 
                        config: ExportConfiguration) -> int:
        """
        Export junction entities to DXF.
        
        Args:
            doc: ezdxf Drawing object
            junction_data: List of junction feature data
            config: Export configuration
            
        Returns:
            Number of junctions exported
        """
```

### GeometryProcessor

Geometric calculations and transformations.

```python
class GeometryProcessor:
    """Geometric calculations for DXF export."""
    
    @staticmethod
    def calculate_azimuth(start_point: QgsPointXY, end_point: QgsPointXY) -> float:
        """
        Calculate azimuth between two points.
        
        Args:
            start_point: Starting point
            end_point: Ending point
            
        Returns:
            Azimuth in degrees (0-360)
        """
        
    @staticmethod
    def point_along_line(start: QgsPointXY, end: QgsPointXY, distance: float) -> QgsPointXY:
        """
        Calculate point at specified distance along line.
        
        Args:
            start: Line start point
            end: Line end point
            distance: Distance from start (0.0-1.0 for relative, >1.0 for absolute)
            
        Returns:
            Point at specified distance
        """
        
    @staticmethod
    def perpendicular_point(line_start: QgsPointXY, line_end: QgsPointXY, 
                          point: QgsPointXY, distance: float) -> QgsPointXY:
        """
        Calculate perpendicular point for label placement.
        
        Args:
            line_start: Line start point
            line_end: Line end point
            point: Reference point on line
            distance: Perpendicular distance
            
        Returns:
            Perpendicular point for label placement
        """
        
    @staticmethod
    def calculate_text_rotation(start_point: QgsPointXY, end_point: QgsPointXY) -> float:
        """
        Calculate text rotation angle for line alignment.
        
        Args:
            start_point: Line start point
            end_point: Line end point
            
        Returns:
            Rotation angle in degrees
        """
```

## Field Definitions

### Standard Sewerage Fields

Pre-defined field definitions for sewerage networks.

```python
class SewageNetworkFields:
    """Standard field definitions for sewerage networks."""
    
    # Required pipe fields
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
    
    # Optional pipe fields
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
    
    # Required junction fields
    JUNCTIONS_REQUIRED = [
        RequiredField("node_id", "Node Identifier", FieldType.STRING,
                     "Unique identifier for each junction"),
    ]
    
    # Optional junction fields
    JUNCTIONS_OPTIONAL = [
        RequiredField("ground_elevation", "Ground Elevation", FieldType.DOUBLE,
                     "Ground surface elevation"),
        RequiredField("invert_elevation", "Invert Elevation", FieldType.DOUBLE,
                     "Junction invert elevation"),
    ]
```

## Exception Classes

### Validation Exceptions

```python
class ValidationError(Exception):
    """Base class for validation errors."""
    
    def __init__(self, message: str, field_name: str = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_name: Optional field name causing error
        """
        super().__init__(message)
        self.field_name = field_name

class LayerValidationError(ValidationError):
    """Layer-specific validation error."""
    
    def __init__(self, message: str, layer_name: str = None):
        """
        Initialize layer validation error.
        
        Args:
            message: Error message
            layer_name: Optional layer name causing error
        """
        super().__init__(message)
        self.layer_name = layer_name

class MappingValidationError(ValidationError):
    """Field mapping validation error."""
    pass

class GeometryProcessingError(Exception):
    """Geometry processing error."""
    
    def __init__(self, message: str, feature_id: str = None):
        """
        Initialize geometry processing error.
        
        Args:
            message: Error message
            feature_id: Optional feature ID causing error
        """
        super().__init__(message)
        self.feature_id = feature_id

class ExportError(Exception):
    """DXF export error."""
    
    def __init__(self, message: str, output_path: str = None):
        """
        Initialize export error.
        
        Args:
            message: Error message
            output_path: Optional output path causing error
        """
        super().__init__(message)
        self.output_path = output_path
```

## Configuration Management

### Configuration API

```python
class Configuration:
    """Plugin configuration management."""
    
    def __init__(self):
        """Initialize configuration with QSettings."""
        
    def save_export_configuration(self, config: ExportConfiguration) -> None:
        """
        Save export configuration for reuse.
        
        Args:
            config: Export configuration to save
        """
        
    def load_export_configuration(self) -> Optional[ExportConfiguration]:
        """
        Load previously saved export configuration.
        
        Returns:
            Saved configuration or None if not found
        """
        
    def save_field_mappings(self, layer_id: str, mappings: Dict[str, str]) -> None:
        """
        Save field mappings for specific layer.
        
        Args:
            layer_id: QGIS layer ID
            mappings: Field mappings to save
        """
        
    def load_field_mappings(self, layer_id: str) -> Dict[str, str]:
        """
        Load field mappings for specific layer.
        
        Args:
            layer_id: QGIS layer ID
            
        Returns:
            Saved field mappings or empty dict
        """
        
    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """
        Get configuration setting value.
        
        Args:
            key: Setting key
            default_value: Default value if not found
            
        Returns:
            Setting value or default
        """
        
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set configuration setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
```

## Internationalization API

### Translation Management

```python
class I18nManager:
    """Internationalization management."""
    
    def __init__(self):
        """Initialize translation system."""
        
    def setup_translator(self, locale: str = None) -> bool:
        """
        Set up translator for specified locale.
        
        Args:
            locale: Locale code (e.g., 'pt', 'en') or None for auto-detect
            
        Returns:
            True if translator set up successfully
        """
        
    def tr(self, text: str, context: str = None) -> str:
        """
        Translate text using current locale.
        
        Args:
            text: Text to translate
            context: Optional translation context
            
        Returns:
            Translated text or original if translation not found
        """
        
    def get_available_locales(self) -> List[str]:
        """
        Get list of available translation locales.
        
        Returns:
            List of locale codes
        """
        
    def get_current_locale(self) -> str:
        """
        Get current active locale.
        
        Returns:
            Current locale code
        """
```

## Usage Examples

### Basic Export

```python
from redbasica_export.core.api import RedBasicaExportAPI
from redbasica_export.core.data_structures import *

# Initialize API
api = RedBasicaExportAPI()

# Get available layers
pipe_layers = api.get_available_layers(GeometryType.LINE)
junction_layers = api.get_available_layers(GeometryType.POINT)

# Select layers
pipe_layer = pipe_layers[0]  # First line layer
junction_layer = junction_layers[0]  # First point layer

# Get field suggestions
pipe_fields = SewageNetworkFields.PIPES_REQUIRED
pipe_mappings = api.suggest_field_mappings(pipe_layer, pipe_fields)

junction_fields = SewageNetworkFields.JUNCTIONS_REQUIRED
junction_mappings = api.suggest_field_mappings(junction_layer, junction_fields)

# Create layer mappings
pipe_mapping = LayerMapping(
    layer_id=pipe_layer.id(),
    layer_name=pipe_layer.name(),
    geometry_type=GeometryType.LINE,
    field_mappings=pipe_mappings,
    default_values={}
)

junction_mapping = LayerMapping(
    layer_id=junction_layer.id(),
    layer_name=junction_layer.name(),
    geometry_type=GeometryType.POINT,
    field_mappings=junction_mappings,
    default_values={}
)

# Create export configuration
config = ExportConfiguration(
    pipes_mapping=pipe_mapping,
    junctions_mapping=junction_mapping,
    output_path="/path/to/output.dxf"
)

# Validate configuration
errors = api.validate_export_configuration(config)
if errors:
    print(f"Configuration errors: {errors}")
else:
    # Execute export
    result = api.export_network(config)
    if result.success:
        print(f"Export successful: {result.features_exported} features exported")
    else:
        print(f"Export failed: {result.errors}")
```

### Custom Field Mapping

```python
# Manual field mapping for custom data structure
custom_pipe_mappings = {
    "pipe_id": "codigo_tubo",
    "upstream_node": "poco_inicial", 
    "downstream_node": "poco_final",
    "length": "comprimento_m",
    "diameter": "diametro_mm",
    "upstream_invert": "cota_montante",
    "downstream_invert": "cota_jusante"
}

# Create mapping with custom fields
pipe_mapping = LayerMapping(
    layer_id=pipe_layer.id(),
    layer_name=pipe_layer.name(),
    geometry_type=GeometryType.LINE,
    field_mappings=custom_pipe_mappings,
    default_values={
        "material": "PVC",
        "notes": "Imported from custom system"
    }
)
```

### Error Handling

```python
try:
    result = api.export_network(config)
    if not result.success:
        for error in result.errors:
            print(f"Export error: {error}")
        for warning in result.warnings:
            print(f"Warning: {warning}")
except ValidationError as e:
    print(f"Validation error: {e}")
except ExportError as e:
    print(f"Export error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Configuration Persistence

```python
from redbasica_export.core.configuration import Configuration

# Save configuration for reuse
config_manager = Configuration()
config_manager.save_export_configuration(config)

# Load saved configuration
saved_config = config_manager.load_export_configuration()
if saved_config:
    result = api.export_network(saved_config)
```

## Plugin Integration

### Checking Plugin Availability

```python
def is_redbasica_available():
    """Check if RedBasica Export plugin is available."""
    try:
        import redbasica_export
        return True
    except ImportError:
        return False

# Use in other plugins
if is_redbasica_available():
    from redbasica_export.core.api import RedBasicaExportAPI
    api = RedBasicaExportAPI()
    # Use API functionality
else:
    print("RedBasica Export plugin not available")
```

### Processing Framework Integration

```python
from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterVectorLayer

class RedBasicaExportAlgorithm(QgsProcessingAlgorithm):
    """Processing algorithm using RedBasica Export."""
    
    def processAlgorithm(self, parameters, context, feedback):
        """Process algorithm using RedBasica API."""
        
        # Get input layers
        pipe_layer = self.parameterAsVectorLayer(parameters, 'PIPE_LAYER', context)
        junction_layer = self.parameterAsVectorLayer(parameters, 'JUNCTION_LAYER', context)
        
        # Use RedBasica API
        api = RedBasicaExportAPI()
        
        # Configure and execute export
        # ... implementation
        
        return {}
```

This API reference provides comprehensive documentation for all public interfaces, data structures, and usage patterns in the RedBasica Export plugin. Use this reference when extending the plugin or integrating it with other QGIS tools.