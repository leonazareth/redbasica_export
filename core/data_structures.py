# -*- coding: utf-8 -*-
"""
Core data structures for RedBasica Export plugin.

This module defines the fundamental data classes used throughout the plugin
for representing layer mappings, field definitions, and export configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class GeometryType(Enum):
    """Enumeration of supported geometry types."""
    LINE = "LineString"
    POINT = "Point"
    POLYGON = "Polygon"


class FieldType(Enum):
    """Enumeration of supported field data types."""
    STRING = "String"
    INTEGER = "Integer"
    DOUBLE = "Double"
    BOOLEAN = "Boolean"


@dataclass
class RequiredField:
    """Definition of a required field for sewerage network export."""
    name: str                           # Internal field name (e.g., "pipe_id")
    display_name: str                   # User-friendly name (e.g., "Pipe Identifier")
    field_type: FieldType              # Expected data type
    description: str                    # Field purpose description
    default_value: Optional[Any] = None # Default value if not mapped
    validation_rules: Optional[Dict] = None  # Additional validation rules
    is_calculated: bool = False         # Whether this field is calculated from others
    is_required: bool = True            # Whether this field is mandatory for export
    calculation_dependencies: List[str] = field(default_factory=list)  # Fields needed for calculation
    
    def validate_value(self, value: Any) -> tuple[bool, str]:
        """
        Validate a value against this field's rules.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None and self.is_required:
            return False, f"{self.display_name} is required"
        
        if self.validation_rules:
            # Check minimum value
            if "min_value" in self.validation_rules and value is not None:
                try:
                    if float(value) < self.validation_rules["min_value"]:
                        return False, f"{self.display_name} must be >= {self.validation_rules['min_value']}"
                except (ValueError, TypeError):
                    pass
            
            # Check maximum value
            if "max_value" in self.validation_rules and value is not None:
                try:
                    if float(value) > self.validation_rules["max_value"]:
                        return False, f"{self.display_name} must be <= {self.validation_rules['max_value']}"
                except (ValueError, TypeError):
                    pass
            
            # Check string length
            if "max_length" in self.validation_rules and isinstance(value, str):
                if len(value) > self.validation_rules["max_length"]:
                    return False, f"{self.display_name} must be <= {self.validation_rules['max_length']} characters"
        
        return True, ""


@dataclass
class LayerMapping:
    """Configuration for mapping a QGIS layer to sewerage network requirements."""
    layer_id: str                      # QGIS layer ID
    layer_name: str                    # Layer display name
    geometry_type: GeometryType        # Required geometry type
    field_mappings: Dict[str, str] = field(default_factory=dict)  # required_field -> layer_field
    default_values: Dict[str, Any] = field(default_factory=dict)  # required_field -> default_value
    calculated_fields: Dict[str, bool] = field(default_factory=dict)  # required_field -> is_calculated
    is_valid: bool = False             # Validation status
    validation_errors: List[str] = field(default_factory=list)  # Validation error messages
    auto_mapped_fields: Dict[str, str] = field(default_factory=dict)  # Track auto-mapped fields
    
    def __post_init__(self):
        """Debug initialization of LayerMapping."""
        print(f"DEBUG: LayerMapping.__post_init__ called")
        print(f"DEBUG: layer_id: {self.layer_id}")
        print(f"DEBUG: layer_name: {self.layer_name}")
        print(f"DEBUG: geometry_type: {self.geometry_type}")
        print(f"DEBUG: field_mappings type: {type(self.field_mappings)}, value: {self.field_mappings}")
        print(f"DEBUG: default_values type: {type(self.default_values)}, value: {self.default_values}")
        print(f"DEBUG: calculated_fields type: {type(self.calculated_fields)}, value: {self.calculated_fields}")
        print(f"DEBUG: auto_mapped_fields type: {type(self.auto_mapped_fields)}, value: {self.auto_mapped_fields}")
    
    def get_mapped_field(self, required_field: str) -> Optional[str]:
        """Get the layer field mapped to a required field."""
        return self.field_mappings.get(required_field)
    
    def get_default_value(self, required_field: str) -> Any:
        """Get the default value for a required field."""
        return self.default_values.get(required_field)
    
    def is_field_calculated(self, required_field: str) -> bool:
        """Check if a field is marked as calculated."""
        return self.calculated_fields.get(required_field, False)
    
    def set_field_mapping(self, required_field: str, layer_field: Optional[str], default_value: Any = None, is_calculated: bool = False):
        """Set mapping for a required field."""
        print(f"DEBUG: LayerMapping.set_field_mapping called")
        print(f"DEBUG: required_field: {required_field}, layer_field: {layer_field}")
        print(f"DEBUG: self.field_mappings before: {self.field_mappings}")
        print(f"DEBUG: self.field_mappings type before: {type(self.field_mappings)}")
        
        if layer_field:
            self.field_mappings[required_field] = layer_field
        elif required_field in self.field_mappings:
            del self.field_mappings[required_field]
        
        print(f"DEBUG: self.field_mappings after: {self.field_mappings}")
        print(f"DEBUG: self.field_mappings type after: {type(self.field_mappings)}")
        
        if default_value is not None:
            self.default_values[required_field] = default_value
        elif required_field in self.default_values:
            del self.default_values[required_field]
        
        self.calculated_fields[required_field] = is_calculated
    
    def get_unmapped_required_fields(self, required_fields: List[str]) -> List[str]:
        """Get list of required fields that are not mapped and have no default values."""
        unmapped = []
        for field_name in required_fields:
            if (field_name not in self.field_mappings and 
                field_name not in self.default_values and 
                not self.is_field_calculated(field_name)):
                unmapped.append(field_name)
        return unmapped



class ExportMode(Enum):
    """Enumeration of export modes."""
    STANDARD = "Standard (Layers)"
    ENHANCED = "Enhanced (MTEXT/Multileader)"


class LabelStyle(Enum):
    """Enumeration of pipe label styles."""
    COMPACT = "Compact (2 lines)"
    STACKED = "Stacked (4 lines)"


@dataclass
class ExportConfiguration:
    """Complete configuration for DXF export operation."""
    pipes_mapping: Optional[LayerMapping] = None
    junctions_mapping: Optional[LayerMapping] = None
    output_path: str = ""
    scale_factor: int = 2000
    layer_prefix: str = "RB_"
    template_path: Optional[str] = None
    include_arrows: bool = True
    include_labels: bool = True
    include_elevations: bool = True
    export_node_id: bool = False  # Whether to include node ID in MULTILEADER labels
    include_slope_unit: bool = False  # Whether to append 'm/m' after slope value
    label_format: str = "{length:.0f}-{diameter:.0f}-{slope:.5f}"
    export_mode: ExportMode = ExportMode.STANDARD
    label_style: LabelStyle = LabelStyle.COMPACT
    
    def __post_init__(self):
        """Debug ExportConfiguration creation."""
        print(f"DEBUG: ExportConfiguration.__post_init__ called")
        print(f"DEBUG: pipes_mapping: {self.pipes_mapping}")
        print(f"DEBUG: junctions_mapping: {self.junctions_mapping}")
        print(f"DEBUG: output_path: {self.output_path}")
    
    def is_valid(self) -> bool:
        """Check if the configuration is valid for export."""
        return (
            self.pipes_mapping is not None and 
            self.pipes_mapping.is_valid and
            bool(self.output_path.strip())
        )
    
    def get_validation_errors(self) -> List[str]:
        """Get all validation errors for this configuration."""
        errors = []
        
        if not self.output_path.strip():
            errors.append("Output path is required")
        
        if self.pipes_mapping is None:
            errors.append("Pipes layer mapping is required")
        elif not self.pipes_mapping.is_valid:
            errors.extend([f"Pipes: {error}" for error in self.pipes_mapping.validation_errors])
        
        if self.junctions_mapping is not None and not self.junctions_mapping.is_valid:
            errors.extend([f"Junctions: {error}" for error in self.junctions_mapping.validation_errors])
        
        if self.scale_factor <= 0:
            errors.append("Scale factor must be positive")
        
        return errors