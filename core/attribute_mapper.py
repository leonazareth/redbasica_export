# -*- coding: utf-8 -*-
"""
Flexible attribute mapping for sewerage network export.

This module provides the AttributeMapper class that handles flexible field mapping
from ANY user field names to required sewerage network attributes with robust
data type conversion and calculated field support.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from qgis.core import QgsVectorLayer, QgsFeature, QgsExpression, QgsExpressionContext

from .data_structures import LayerMapping, GeometryType, FieldType
from .field_definitions import SewageNetworkFields
from .data_converter import DataConverter, CalculatedFields

logger = logging.getLogger(__name__)


class AttributeMapper:
    """
    Manages flexible field mapping and data extraction with robust conversion.
    
    This class provides comprehensive attribute mapping capabilities that work
    with ANY field names and data formats, including auto-mapping suggestions,
    manual mapping, and calculated field support.
    """
    
    def __init__(self):
        """Initialize the AttributeMapper."""
        self.data_converter = DataConverter()
        self.calculated_fields = CalculatedFields()
    
    def create_auto_mapping(self, layer: QgsVectorLayer, geometry_type: GeometryType) -> LayerMapping:
        """
        Create automatic field mapping suggestions based on common naming patterns.
        
        Args:
            layer: QgsVectorLayer to analyze
            geometry_type: Type of geometry (LINE for pipes, POINT for junctions)
            
        Returns:
            LayerMapping with auto-suggested field mappings
        """
        if not layer or not layer.isValid():
            raise ValueError("Invalid layer provided")
        
        # Create base mapping
        mapping = LayerMapping(
            layer_id=layer.id(),
            layer_name=layer.name(),
            geometry_type=geometry_type
        )
        
        # Get layer field names
        layer_fields = [field.name() for field in layer.fields()]
        
        # Get field suggestions based on geometry type
        if geometry_type == GeometryType.LINE:
            suggestion_type = 'pipes'
            required_fields = SewageNetworkFields.get_required_pipe_fields()
            all_fields = SewageNetworkFields.get_all_pipe_fields()
        elif geometry_type == GeometryType.POINT:
            suggestion_type = 'junctions'
            required_fields = SewageNetworkFields.get_required_junction_fields()
            all_fields = SewageNetworkFields.get_all_junction_fields()
        else:
            raise ValueError(f"Unsupported geometry type: {geometry_type}")
        
        # Get suggestions from field definitions
        suggestions = SewageNetworkFields.suggest_field_mapping(layer_fields, suggestion_type)
        
        # Apply auto-mapping for fields with suggestions
        print(f"DEBUG: AttributeMapper applying auto-mapping suggestions: {suggestions}")
        for required_field, suggested_fields in suggestions.items():
            if suggested_fields:
                # Use the first (best) suggestion
                best_match = suggested_fields[0]
                print(f"DEBUG: Auto-mapping {required_field} -> {best_match}")
                mapping.field_mappings[required_field] = best_match
                mapping.auto_mapped_fields[required_field] = best_match
                print(f"DEBUG: field_mappings after adding {required_field}: {mapping.field_mappings}")
                print(f"DEBUG: field_mappings type: {type(mapping.field_mappings)}")
        
        # Validate the mapping
        mapping = self._validate_mapping(mapping, layer)
        
        return mapping
    
    def update_field_mapping(self, mapping: LayerMapping, required_field: str, 
                           layer_field: Optional[str] = None, 
                           default_value: Any = None,
                           is_calculated: bool = False) -> LayerMapping:
        """
        Update field mapping for a specific required field.
        
        Args:
            mapping: LayerMapping to update
            required_field: Name of the required field
            layer_field: Layer field to map to (None to unmap)
            default_value: Default value to use if not mapped
            is_calculated: Whether this field should be calculated
            
        Returns:
            Updated LayerMapping
        """
        # Clear existing mapping
        if required_field in mapping.field_mappings:
            del mapping.field_mappings[required_field]
        if required_field in mapping.default_values:
            del mapping.default_values[required_field]
        
        # Set new mapping
        if layer_field:
            mapping.field_mappings[required_field] = layer_field
        elif default_value is not None:
            mapping.default_values[required_field] = default_value
        
        # Set calculated field flag
        mapping.calculated_fields[required_field] = is_calculated
        
        # Re-validate mapping
        from .layer_manager import LayerManager
        layer_manager = LayerManager()
        layer = layer_manager.get_layer_by_id(mapping.layer_id)
        if layer:
            mapping = self._validate_mapping(mapping, layer)
        
        return mapping
    
    def extract_feature_data(self, feature: QgsFeature, mapping: LayerMapping, 
                           layer: QgsVectorLayer) -> Dict[str, Any]:
        """
        Extract and convert feature data using configured mappings.
        
        Args:
            feature: QgsFeature to extract data from
            mapping: LayerMapping configuration
            layer: Source QgsVectorLayer
            
        Returns:
            Dictionary with converted feature data
        """
        extracted_data = {}
        
        # Get all relevant field definitions
        if mapping.geometry_type == GeometryType.LINE:
            all_fields = SewageNetworkFields.get_all_pipe_fields()
        else:
            all_fields = SewageNetworkFields.get_all_junction_fields()
        
        # Extract mapped fields with type conversion
        for field_def in all_fields:
            field_name = field_def.name
            
            # Skip calculated fields for now (will be calculated later)
            if mapping.is_field_calculated(field_name):
                continue
            
            # Get value from mapping or default
            if field_name in mapping.field_mappings:
                layer_field = mapping.field_mappings[field_name]
                raw_value = feature[layer_field]
            elif field_name in mapping.default_values:
                raw_value = mapping.default_values[field_name]
            else:
                # Use field definition default
                raw_value = field_def.default_value
            
            # Convert value to appropriate type
            converted_value = self._convert_value(raw_value, field_def.field_type)
            extracted_data[field_name] = converted_value
        
        # Calculate derived fields
        calculated_data = self._calculate_derived_fields(extracted_data, mapping)
        extracted_data.update(calculated_data)
        
        return extracted_data
    
    def extract_all_features_data(self, layer: QgsVectorLayer, mapping: LayerMapping) -> List[Dict[str, Any]]:
        """
        Extract data from all features in a layer.
        
        Args:
            layer: QgsVectorLayer to process
            mapping: LayerMapping configuration
            
        Returns:
            List of dictionaries with feature data
        """
        if not layer or not layer.isValid():
            return []
        
        features_data = []
        
        for feature in layer.getFeatures():
            try:
                feature_data = self.extract_feature_data(feature, mapping, layer)
                features_data.append(feature_data)
            except Exception as e:
                logger.warning(f"Failed to extract data from feature {feature.id()}: {e}")
                continue
        
        return features_data
    
    def validate_mapping_completeness(self, mapping: LayerMapping) -> Tuple[bool, List[str]]:
        """
        Validate that all required fields are properly mapped or have defaults.
        
        Args:
            mapping: LayerMapping to validate
            
        Returns:
            Tuple of (is_complete, missing_fields)
        """
        # Get required fields based on geometry type
        if mapping.geometry_type == GeometryType.LINE:
            required_fields = SewageNetworkFields.get_required_pipe_fields()
        elif mapping.geometry_type == GeometryType.POINT:
            required_fields = SewageNetworkFields.get_required_junction_fields()
        else:
            return False, [f"Unsupported geometry type: {mapping.geometry_type}"]
        
        missing_fields = []
        
        for field_name in required_fields:
            # Check if field is mapped, has default, or is calculated
            if (field_name not in mapping.field_mappings and 
                field_name not in mapping.default_values and 
                not mapping.is_field_calculated(field_name)):
                missing_fields.append(field_name)
        
        is_complete = len(missing_fields) == 0
        return is_complete, missing_fields
    
    def get_mapping_summary(self, mapping: LayerMapping) -> Dict[str, Any]:
        """
        Get a summary of the current mapping configuration.
        
        Args:
            mapping: LayerMapping to summarize
            
        Returns:
            Dictionary with mapping summary information
        """
        # Get field definitions
        if mapping.geometry_type == GeometryType.LINE:
            all_fields = SewageNetworkFields.get_all_pipe_fields()
            required_fields = SewageNetworkFields.get_required_pipe_fields()
        else:
            all_fields = SewageNetworkFields.get_all_junction_fields()
            required_fields = SewageNetworkFields.get_required_junction_fields()
        
        summary = {
            'layer_name': mapping.layer_name,
            'geometry_type': mapping.geometry_type.value,
            'total_fields': len(all_fields),
            'required_fields': len(required_fields),
            'mapped_fields': len(mapping.field_mappings),
            'default_fields': len(mapping.default_values),
            'calculated_fields': len([f for f in mapping.calculated_fields if mapping.calculated_fields[f]]),
            'auto_mapped_fields': len(mapping.auto_mapped_fields),
            'is_valid': mapping.is_valid,
            'validation_errors': mapping.validation_errors
        }
        
        # Check completeness
        is_complete, missing_fields = self.validate_mapping_completeness(mapping)
        summary['is_complete'] = is_complete
        summary['missing_required_fields'] = missing_fields
        
        return summary
    
    def get_available_calculated_fields(self, mapping: LayerMapping) -> List[str]:
        """
        Get list of calculated fields that can be computed with current mappings.
        
        Args:
            mapping: LayerMapping to analyze
            
        Returns:
            List of calculated field names that can be computed
        """
        available_calculated = []
        
        # Get all mapped and default field names
        available_fields = set(mapping.field_mappings.keys()) | set(mapping.default_values.keys())
        
        # Check each calculated field
        for field_def in SewageNetworkFields.CALCULATED_FIELDS:
            if SewageNetworkFields.can_calculate_field(field_def.name, list(available_fields)):
                available_calculated.append(field_def.name)
        
        return available_calculated
    
    def suggest_calculated_fields(self, mapping: LayerMapping) -> Dict[str, List[str]]:
        """
        Suggest calculated fields that can be enabled based on current mappings.
        
        Args:
            mapping: LayerMapping to analyze
            
        Returns:
            Dictionary mapping calculated_field -> [required_dependencies]
        """
        suggestions = {}
        available_fields = set(mapping.field_mappings.keys()) | set(mapping.default_values.keys())
        
        for field_def in SewageNetworkFields.CALCULATED_FIELDS:
            dependencies = field_def.calculation_dependencies
            if all(dep in available_fields for dep in dependencies):
                suggestions[field_def.name] = dependencies
        
        return suggestions
    
    def _convert_value(self, value: Any, field_type: FieldType) -> Any:
        """
        Convert a value to the specified field type.
        
        Args:
            value: Raw value to convert
            field_type: Target FieldType
            
        Returns:
            Converted value
        """
        if field_type == FieldType.STRING:
            return self.data_converter.to_string(value)
        elif field_type == FieldType.DOUBLE:
            return self.data_converter.to_double(value)
        elif field_type == FieldType.INTEGER:
            return self.data_converter.to_integer(value)
        elif field_type == FieldType.BOOLEAN:
            return self.data_converter.to_boolean(value)
        else:
            logger.warning(f"Unknown field type {field_type}, using string conversion")
            return self.data_converter.to_string(value)
    
    def _calculate_derived_fields(self, data: Dict[str, Any], mapping: LayerMapping) -> Dict[str, Any]:
        """
        Calculate derived/calculated fields from extracted data.
        
        Args:
            data: Extracted feature data
            mapping: LayerMapping configuration
            
        Returns:
            Dictionary with calculated field values
        """
        calculated_data = {}
        
        # Only calculate fields that are marked as calculated in the mapping
        for field_name, is_calculated in mapping.calculated_fields.items():
            if not is_calculated:
                continue
            
            try:
                if field_name == "calculated_slope":
                    if all(key in data for key in ["upstream_invert", "downstream_invert", "length"]):
                        calculated_data[field_name] = self.calculated_fields.calculate_slope(
                            data["upstream_invert"], data["downstream_invert"], data["length"]
                        )
                
                elif field_name == "upstream_depth":
                    if all(key in data for key in ["upstream_ground", "upstream_invert"]):
                        calculated_data[field_name] = self.calculated_fields.calculate_depth(
                            data["upstream_ground"], data["upstream_invert"]
                        )
                
                elif field_name == "downstream_depth":
                    if all(key in data for key in ["downstream_ground", "downstream_invert"]):
                        calculated_data[field_name] = self.calculated_fields.calculate_depth(
                            data["downstream_ground"], data["downstream_invert"]
                        )
                
                elif field_name == "junction_depth":
                    if all(key in data for key in ["ground_elevation", "invert_elevation"]):
                        calculated_data[field_name] = self.calculated_fields.calculate_depth(
                            data["ground_elevation"], data["invert_elevation"]
                        )
                
            except Exception as e:
                logger.warning(f"Failed to calculate field {field_name}: {e}")
                # Use default value from field definition
                field_def = SewageNetworkFields.get_field_by_name(field_name)
                if field_def:
                    calculated_data[field_name] = field_def.default_value
        
        return calculated_data
    
    def _validate_mapping(self, mapping: LayerMapping, layer: QgsVectorLayer) -> LayerMapping:
        """
        Validate a layer mapping and update validation status.
        
        Args:
            mapping: LayerMapping to validate
            layer: Source QgsVectorLayer
            
        Returns:
            Updated LayerMapping with validation results
        """
        errors = []
        
        # Check layer validity
        if not layer or not layer.isValid():
            errors.append("Layer is not valid")
            mapping.is_valid = False
            mapping.validation_errors = errors
            return mapping
        
        # Get layer field names
        layer_field_names = [field.name() for field in layer.fields()]
        
        # Validate mapped fields exist in layer
        for required_field, layer_field in mapping.field_mappings.items():
            if layer_field not in layer_field_names:
                errors.append(f"Mapped field '{layer_field}' for '{required_field}' does not exist in layer")
        
        # Check mapping completeness
        is_complete, missing_fields = self.validate_mapping_completeness(mapping)
        if not is_complete:
            errors.append(f"Required fields not mapped: {', '.join(missing_fields)}")
        
        # Update validation status
        mapping.is_valid = len(errors) == 0
        mapping.validation_errors = errors
        
        return mapping
    
    def reset_auto_mapping(self, mapping: LayerMapping, layer: QgsVectorLayer) -> LayerMapping:
        """
        Reset and regenerate auto-mapping for a layer mapping.
        
        Args:
            mapping: LayerMapping to reset
            layer: Source QgsVectorLayer
            
        Returns:
            LayerMapping with fresh auto-mapping
        """
        # Clear existing mappings but preserve manual overrides
        manual_mappings = {}
        for field, layer_field in mapping.field_mappings.items():
            if field not in mapping.auto_mapped_fields:
                manual_mappings[field] = layer_field
        
        # Clear and regenerate
        mapping.field_mappings.clear()
        mapping.auto_mapped_fields.clear()
        mapping.default_values.clear()
        
        # Regenerate auto-mapping
        new_mapping = self.create_auto_mapping(layer, mapping.geometry_type)
        
        # Restore manual mappings (they take precedence)
        for field, layer_field in manual_mappings.items():
            mapping.field_mappings[field] = layer_field
        
        # Copy auto-mappings that don't conflict with manual ones
        for field, layer_field in new_mapping.field_mappings.items():
            if field not in manual_mappings:
                mapping.field_mappings[field] = layer_field
                mapping.auto_mapped_fields[field] = layer_field
        
        # Copy default values
        mapping.default_values.update(new_mapping.default_values)
        
        # Re-validate
        mapping = self._validate_mapping(mapping, layer)
        
        return mapping