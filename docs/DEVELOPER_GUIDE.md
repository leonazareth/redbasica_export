# RedBasica Export - Developer Guide

## Architecture Overview

RedBasica Export follows a modular architecture with clear separation of concerns between UI, business logic, and data processing components.

### Project Structure

```
redbasica_export/
├── __init__.py                          # Plugin initialization
├── redbasica_export.py                  # Main plugin class
├── metadata.txt                         # Plugin metadata
├── ui/                                  # User Interface Components
│   ├── __init__.py
│   ├── main_export_dialog.py           # Main export dialog
│   ├── main_export_dialog.ui           # Main dialog UI design
│   ├── layer_selector_dialog.py        # Layer selection dialog
│   ├── layer_selector_dialog.ui        # Layer selector UI
│   ├── attribute_mapper_dialog.py      # Attribute mapping dialog
│   └── attribute_mapper_dialog.ui      # Attribute mapper UI
├── core/                                # Core Business Logic
│   ├── __init__.py
│   ├── layer_manager.py                # Layer discovery and validation
│   ├── attribute_mapper.py             # Field mapping logic
│   ├── dxf_exporter.py                 # DXF export engine
│   ├── geometry_processor.py           # Geometry utilities
│   ├── template_manager.py             # DXF template handling
│   ├── field_definitions.py            # Required field definitions
│   ├── data_structures.py              # Data classes and enums
│   ├── data_converter.py               # Data type conversion
│   ├── configuration.py                # Settings management
│   ├── validation.py                   # Validation logic
│   ├── exceptions.py                   # Custom exceptions
│   ├── error_recovery.py               # Error handling and recovery
│   ├── error_messages.py               # User-friendly error messages
│   ├── i18n_manager.py                 # Internationalization
│   └── file_utils.py                   # File operations
├── addon/                               # Bundled Libraries
│   ├── ezdxf/                          # Bundled ezdxf library
│   └── c3d/                            # Bundled c3d library
├── resources/                           # Resources
│   ├── icons/                          # Plugin icons
│   ├── templates/                      # DXF templates
│   └── __init__.py
├── i18n/                               # Translation files
│   ├── redbasica_export_en.ts
│   ├── redbasica_export_pt.ts
│   └── ...
├── docs/                               # Documentation
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   └── API_REFERENCE.md
└── tests/                              # Test files
    ├── test_*.py
    └── ...
```

## Core Components

### 1. Layer Manager (`core/layer_manager.py`)

Handles discovery and validation of layers in the QGIS project.

```python
class LayerManager:
    """Manages layer discovery and validation for flexible sewerage export."""
    
    def get_available_layers(self, geometry_type: GeometryType = None) -> List[QgsVectorLayer]:
        """Get all available vector layers, optionally filtered by geometry type."""
        
    def get_layer_fields(self, layer: QgsVectorLayer) -> Dict[str, FieldType]:
        """Extract field information from a layer."""
        
    def validate_layer_compatibility(self, layer: QgsVectorLayer, required_geometry: GeometryType) -> List[str]:
        """Validate layer compatibility for export requirements."""
        
    def get_sample_data(self, layer: QgsVectorLayer, max_features: int = 5) -> List[Dict]:
        """Get sample data from layer for preview and mapping verification."""
```

**Key Features:**
- Works with ANY layer names (not restricted to 'PIPES'/'JUNCTIONS')
- Filters by geometry type (Line for pipes, Point for junctions)
- Extracts field metadata for mapping interface
- Provides sample data for user verification

### 2. Attribute Mapper (`core/attribute_mapper.py`)

Manages flexible field mapping from user fields to required sewerage attributes.

```python
class AttributeMapper:
    """Handles flexible attribute mapping with auto-suggestion and validation."""
    
    def suggest_field_mappings(self, layer_fields: List[str], required_fields: List[RequiredField]) -> Dict[str, str]:
        """Suggest field mappings based on common naming patterns."""
        
    def validate_mappings(self, mappings: Dict[str, str], required_fields: List[RequiredField]) -> List[str]:
        """Validate mapping completeness and compatibility."""
        
    def extract_feature_data(self, feature: QgsFeature, mappings: Dict[str, str]) -> Dict[str, Any]:
        """Extract and convert feature data using configured mappings."""
```

**Auto-mapping Patterns:**
```python
FIELD_SUGGESTION_PATTERNS = {
    "pipe_id": ["DC_ID", "id", "pipe_id", "segment_id", "codigo"],
    "upstream_node": ["PVM", "upstream", "from_node", "no_montante"],
    "downstream_node": ["PVJ", "downstream", "to_node", "no_jusante"],
    "length": ["LENGTH", "length", "comprimento", "len"],
    "diameter": ["DIAMETER", "diameter", "diam", "dn", "diametro"],
    # ... more patterns
}
```

### 3. Data Converter (`core/data_converter.py`)

Handles robust data type conversion for various input formats.

```python
class DataConverter:
    """Robust data type conversion with graceful error handling."""
    
    @staticmethod
    def to_string(value) -> str:
        """Convert any value to string, handling NULL/None."""
        
    @staticmethod
    def to_double(value) -> float:
        """Convert to float, handling string numbers and Portuguese decimals."""
        
    @staticmethod
    def to_integer(value) -> int:
        """Convert to integer with fallback to zero."""
```

**Conversion Examples:**
- `"1.05"` → `1.05`
- `"2,50"` → `2.50` (Portuguese decimal)
- `NULL` → `0.0` (numeric) or `""` (string)
- Invalid data → Default values with logging

### 4. DXF Exporter (`core/dxf_exporter.py`)

Core DXF export functionality with comprehensive styling.

```python
class DXFExporter:
    """Professional DXF export with QEsg-compatible output."""
    
    def __init__(self, template_manager: TemplateManager):
        """Initialize with template manager for DXF templates."""
        
    def export_network(self, config: ExportConfiguration) -> str:
        """Export complete sewerage network to DXF format."""
        
    def create_pipe_entities(self, pipe_data: List[Dict]) -> None:
        """Create pipe entities with labels and arrows."""
        
    def create_junction_entities(self, junction_data: List[Dict]) -> None:
        """Create junction entities with elevation blocks."""
```

**DXF Layer Structure:**
```python
LAYER_DEFINITIONS = [
    ('REDE', 172, 'Sewage pipes/network'),
    ('NUMERO', 3, 'Pipe ID labels'),
    ('TEXTO', 3, 'Pipe data labels'),
    ('TEXTOPVS', 7, 'Manhole elevation data'),
    ('PV', 3, 'Manholes/junctions'),
    ('NUMPV', 3, 'Manhole ID labels'),
    ('SETA', 172, 'Flow direction arrows'),
    # ... more layers
]
```

### 5. Geometry Processor (`core/geometry_processor.py`)

Utility functions for geometric calculations.

```python
class GeometryProcessor:
    """Geometric calculations and transformations for DXF export."""
    
    @staticmethod
    def calculate_azimuth(start_point: QgsPointXY, end_point: QgsPointXY) -> float:
        """Calculate azimuth between two points."""
        
    @staticmethod
    def point_along_line(start: QgsPointXY, end: QgsPointXY, distance: float) -> QgsPointXY:
        """Calculate point at specified distance along line."""
        
    @staticmethod
    def perpendicular_point(line_start: QgsPointXY, line_end: QgsPointXY, 
                          point: QgsPointXY, distance: float) -> QgsPointXY:
        """Calculate perpendicular point for label placement."""
```

## Data Structures

### Core Data Classes

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
    name: str                           # Internal field name
    display_name: str                   # User-friendly name
    field_type: FieldType              # Expected data type
    description: str                    # Field purpose
    default_value: Optional[str] = None # Default if not mapped
    validation_rules: Optional[Dict] = None

@dataclass
class LayerMapping:
    layer_id: str                      # QGIS layer ID
    layer_name: str                    # Display name
    geometry_type: GeometryType        # Required geometry
    field_mappings: Dict[str, str]     # required_field -> layer_field
    default_values: Dict[str, str]     # required_field -> default_value
    is_valid: bool = False             # Validation status
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

## User Interface Components

### Main Export Dialog

The primary interface for configuring exports:

```python
class MainExportDialog(QDialog):
    """Main export configuration dialog."""
    
    def __init__(self, layer_manager: LayerManager, template_manager: TemplateManager):
        """Initialize dialog with business logic components."""
        
    def setup_ui(self):
        """Set up UI components and connections."""
        
    def populate_layer_combos(self):
        """Populate layer selection dropdowns."""
        
    def validate_configuration(self) -> List[str]:
        """Validate current export configuration."""
        
    def on_export_clicked(self):
        """Handle export button click."""
```

### Attribute Mapper Dialog

Comprehensive field mapping interface:

```python
class AttributeMapperDialog(QDialog):
    """Dialog for configuring field mappings."""
    
    def __init__(self, layer: QgsVectorLayer, required_fields: List[RequiredField]):
        """Initialize with layer and required field definitions."""
        
    def setup_mapping_tables(self):
        """Set up required and optional field mapping tables."""
        
    def suggest_auto_mappings(self):
        """Apply auto-suggested field mappings."""
        
    def validate_mappings(self) -> List[str]:
        """Validate current field mappings."""
```

## Error Handling and Validation

### Exception Hierarchy

```python
class ValidationError(Exception):
    """Base validation error."""
    pass

class LayerValidationError(ValidationError):
    """Layer-specific validation issues."""
    pass

class MappingValidationError(ValidationError):
    """Field mapping issues."""
    pass

class ExportError(Exception):
    """Export process errors."""
    pass

class GeometryProcessingError(Exception):
    """Geometry calculation errors."""
    pass
```

### Error Recovery Strategy

```python
class ErrorRecovery:
    """Handles graceful error recovery during export."""
    
    @staticmethod
    def handle_invalid_feature(feature: QgsFeature, error: Exception) -> bool:
        """Handle invalid feature - skip and continue or fail."""
        
    @staticmethod
    def handle_conversion_error(value: Any, target_type: type, field_name: str) -> Any:
        """Handle data conversion errors with appropriate defaults."""
        
    @staticmethod
    def handle_geometry_error(geometry: QgsGeometry, operation: str) -> Optional[QgsGeometry]:
        """Handle geometry processing errors."""
```

## Internationalization

### Translation System

```python
class I18nManager:
    """Manages plugin internationalization."""
    
    def __init__(self):
        """Initialize translation system."""
        
    def setup_translator(self, locale: str = None):
        """Set up QTranslator for specified locale."""
        
    def tr(self, text: str, context: str = None) -> str:
        """Translate text using current locale."""
        
    def get_available_locales(self) -> List[str]:
        """Get list of available translation locales."""
```

### Translation Files

Translation files are stored in `i18n/` directory:
- `redbasica_export_en.ts` - English translations
- `redbasica_export_pt.ts` - Portuguese translations
- Additional languages can be added as needed

## Testing Framework

### Unit Tests

```python
class TestLayerManager(unittest.TestCase):
    """Test LayerManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        
    def test_get_available_layers(self):
        """Test layer discovery functionality."""
        
    def test_layer_field_extraction(self):
        """Test field metadata extraction."""
        
    def test_layer_validation(self):
        """Test layer compatibility validation."""

class TestAttributeMapper(unittest.TestCase):
    """Test AttributeMapper functionality."""
    
    def test_auto_mapping_suggestions(self):
        """Test automatic field mapping suggestions."""
        
    def test_data_conversion(self):
        """Test robust data type conversion."""
        
    def test_mapping_validation(self):
        """Test field mapping validation."""
```

### Integration Tests

```python
class TestExportWorkflow(unittest.TestCase):
    """Test complete export workflows."""
    
    def test_complete_export_workflow(self):
        """Test end-to-end export process."""
        
    def test_error_handling_scenarios(self):
        """Test error handling and recovery."""
        
    def test_dxf_output_validation(self):
        """Validate DXF output structure and content."""
```

## Configuration Management

### Settings Persistence

```python
class Configuration:
    """Manages plugin configuration and settings persistence."""
    
    def __init__(self):
        """Initialize configuration with QSettings."""
        
    def save_export_configuration(self, config: ExportConfiguration):
        """Save export configuration for reuse."""
        
    def load_export_configuration(self) -> Optional[ExportConfiguration]:
        """Load previously saved configuration."""
        
    def save_field_mappings(self, layer_id: str, mappings: Dict[str, str]):
        """Save field mappings for specific layer."""
        
    def load_field_mappings(self, layer_id: str) -> Dict[str, str]:
        """Load field mappings for specific layer."""
```

## Bundled Dependencies

### ezdxf Library Integration

The plugin includes a bundled ezdxf library for DXF operations:

```python
# Import bundled ezdxf
import sys
import os

addon_path = os.path.join(os.path.dirname(__file__), 'addon')
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

import ezdxf
from ezdxf import zoom
from ezdxf.enums import TextEntityAlignment
```

### Dependency Management

```python
def check_dependencies():
    """Check if bundled dependencies are available."""
    try:
        import ezdxf
        version = getattr(ezdxf, '__version__', 'unknown')
        return True, f"ezdxf {version} available"
    except ImportError as e:
        return False, f"Bundled libraries not accessible: {e}"
```

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Load layer data only when needed
2. **Batch Processing**: Process features in batches for large datasets
3. **Memory Management**: Efficient geometry processing and cleanup
4. **Caching**: Cache layer metadata and field information

### Memory Management

```python
class MemoryManager:
    """Manages memory usage during large exports."""
    
    @staticmethod
    def process_features_in_batches(layer: QgsVectorLayer, batch_size: int = 1000):
        """Process features in batches to manage memory usage."""
        
    @staticmethod
    def cleanup_geometry_cache():
        """Clean up cached geometry objects."""
```

## Extending the Plugin

### Adding New Field Types

```python
# Add new field type to enum
class FieldType(Enum):
    STRING = "String"
    INTEGER = "Integer"
    DOUBLE = "Double"
    BOOLEAN = "Boolean"
    DATE = "Date"          # New field type
    DATETIME = "DateTime"  # New field type

# Add conversion method
class DataConverter:
    @staticmethod
    def to_date(value) -> Optional[datetime.date]:
        """Convert value to date object."""
        # Implementation here
```

### Adding New Export Formats

```python
class ExportFormat(Enum):
    DXF = "dxf"
    DWG = "dwg"      # New format
    SHAPEFILE = "shp" # New format

class ExporterFactory:
    @staticmethod
    def create_exporter(format_type: ExportFormat):
        """Factory method to create appropriate exporter."""
        if format_type == ExportFormat.DXF:
            return DXFExporter()
        elif format_type == ExportFormat.DWG:
            return DWGExporter()  # New exporter
        # ... more formats
```

### Custom Validation Rules

```python
class CustomValidationRule:
    """Base class for custom validation rules."""
    
    def validate(self, value: Any, context: Dict) -> List[str]:
        """Validate value and return list of error messages."""
        raise NotImplementedError

class PipeSlopeValidationRule(CustomValidationRule):
    """Validate pipe slope is within reasonable range."""
    
    def validate(self, value: Any, context: Dict) -> List[str]:
        """Validate pipe slope value."""
        errors = []
        try:
            slope = float(value)
            if slope < 0.001 or slope > 0.5:
                errors.append(f"Pipe slope {slope} is outside reasonable range (0.001-0.5)")
        except (ValueError, TypeError):
            errors.append(f"Invalid slope value: {value}")
        return errors
```

## API Reference

### Public API

The plugin exposes a public API for programmatic use:

```python
from redbasica_export.core.api import RedBasicaExportAPI

# Initialize API
api = RedBasicaExportAPI()

# Get available layers
layers = api.get_available_layers(geometry_type=GeometryType.LINE)

# Configure export
config = ExportConfiguration(
    pipes_mapping=pipe_mapping,
    junctions_mapping=junction_mapping,
    output_path="/path/to/output.dxf"
)

# Execute export
result = api.export_network(config)
```

### Plugin Integration

For integration with other QGIS plugins:

```python
# Check if RedBasica Export is available
def is_redbasica_available():
    try:
        import redbasica_export
        return True
    except ImportError:
        return False

# Use RedBasica Export functionality
if is_redbasica_available():
    from redbasica_export.core.api import RedBasicaExportAPI
    api = RedBasicaExportAPI()
    # Use API methods
```

## Contributing

### Development Setup

1. Clone the repository
2. Set up QGIS development environment
3. Install development dependencies
4. Run tests to verify setup

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for all public methods
- Document all classes and methods with docstrings
- Write comprehensive unit tests for new functionality

### Submitting Changes

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation as needed
4. Submit pull request with detailed description

### Testing Requirements

- All new code must have unit tests
- Integration tests for major features
- UI tests for dialog functionality
- Performance tests for large datasets

## License

This plugin is released under the GNU General Public License v3.0. See LICENSE file for complete terms.