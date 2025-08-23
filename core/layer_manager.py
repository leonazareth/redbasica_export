# -*- coding: utf-8 -*-
"""
Layer management for flexible sewerage network export.

This module provides the LayerManager class that discovers and validates
ANY layers from the current QGIS project, regardless of naming conventions.
It supports flexible layer selection and field mapping for maximum compatibility.
"""

from typing import List, Dict, Optional, Any, Tuple
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsWkbTypes,
    QgsExpression, QgsExpressionContext, QgsExpressionContextUtils
)
from qgis.PyQt.QtCore import QVariant

from .data_structures import GeometryType, FieldType, LayerMapping
from .field_definitions import SewageNetworkFields
from .exceptions import LayerValidationError, ValidationError
from .validation import ValidationResult, LayerValidator


class LayerManager:
    """
    Manages discovery, validation, and analysis of ANY project layers.
    
    This class provides flexible layer management without hardcoded layer name
    dependencies, allowing users to select any layers from their QGIS project
    for sewerage network export.
    """
    
    def __init__(self):
        """Initialize the LayerManager."""
        self.project = QgsProject.instance()
    
    def get_available_layers(self, geometry_type: Optional[GeometryType] = None) -> List[QgsVectorLayer]:
        """
        Get ALL available vector layers from the current QGIS project.
        
        Args:
            geometry_type: Optional filter by geometry type (LINE, POINT, POLYGON)
            
        Returns:
            List of QgsVectorLayer objects matching the criteria
        """
        layers = []
        
        # Get all vector layers from the project
        for layer in self.project.mapLayers().values():
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                # Filter by geometry type if specified
                if geometry_type is not None:
                    layer_geom_type = self._get_layer_geometry_type(layer)
                    if layer_geom_type != geometry_type:
                        continue
                
                layers.append(layer)
        
        # Sort layers by name for consistent ordering
        layers.sort(key=lambda x: x.name().lower())
        return layers
    
    def get_pipe_layers(self) -> List[QgsVectorLayer]:
        """Get all line layers suitable for pipe networks."""
        return self.get_available_layers(GeometryType.LINE)
    
    def get_junction_layers(self) -> List[QgsVectorLayer]:
        """Get all point layers suitable for junctions/manholes."""
        return self.get_available_layers(GeometryType.POINT)
    
    def get_layer_fields(self, layer: QgsVectorLayer) -> Dict[str, FieldType]:
        """
        Extract field information from ANY layer.
        
        Args:
            layer: QgsVectorLayer to analyze
            
        Returns:
            Dictionary mapping field_name -> FieldType
        """
        if not layer or not layer.isValid():
            return {}
        
        fields_info = {}
        
        for field in layer.fields():
            field_name = field.name()
            field_type = self._qgis_type_to_field_type(field.type())
            fields_info[field_name] = field_type
        
        return fields_info
    
    def get_layer_field_names(self, layer: QgsVectorLayer) -> List[str]:
        """
        Get list of field names from a layer.
        
        Args:
            layer: QgsVectorLayer to analyze
            
        Returns:
            List of field names
        """
        if not layer or not layer.isValid():
            return []
        
        return [field.name() for field in layer.fields()]
    
    def validate_layer_compatibility(self, layer: QgsVectorLayer, required_geometry: GeometryType) -> ValidationResult:
        """
        Validate layer compatibility using the comprehensive validation framework.
        
        Args:
            layer: QgsVectorLayer to validate
            required_geometry: Required geometry type
            
        Returns:
            ValidationResult with detailed validation information
        """
        validator = LayerValidator()
        result = ValidationResult()
        
        # Basic layer validation
        basic_result = validator.validate_layer_basic(layer)
        result.merge(basic_result)
        
        if not basic_result.is_valid:
            return result
        
        # Geometry type validation
        geom_result = validator.validate_geometry_type(layer, required_geometry)
        result.merge(geom_result)
        
        # Feature geometry validation (sample)
        geometry_result = validator.validate_feature_geometries(layer, max_check=10)
        result.merge(geometry_result)
        
        return result
    
    def get_sample_data(self, layer: QgsVectorLayer, max_features: int = 5) -> List[Dict[str, Any]]:
        """
        Extract sample data from a layer for preview and mapping verification.
        
        Args:
            layer: QgsVectorLayer to sample
            max_features: Maximum number of features to sample
            
        Returns:
            List of dictionaries containing feature attributes
        """
        if not layer or not layer.isValid():
            return []
        
        sample_data = []
        field_names = self.get_layer_field_names(layer)
        
        # Get sample features
        features = layer.getFeatures()
        count = 0
        
        for feature in features:
            if count >= max_features:
                break
            
            feature_data = {}
            for field_name in field_names:
                value = feature[field_name]
                # Convert QVariant NULL to None for consistency
                if isinstance(value, QVariant) and value.isNull():
                    value = None
                feature_data[field_name] = value
            
            sample_data.append(feature_data)
            count += 1
        
        return sample_data
    
    def get_layer_statistics(self, layer: QgsVectorLayer) -> Dict[str, Any]:
        """
        Get basic statistics about a layer.
        
        Args:
            layer: QgsVectorLayer to analyze
            
        Returns:
            Dictionary with layer statistics
        """
        if not layer or not layer.isValid():
            return {}
        
        stats = {
            'name': layer.name(),
            'feature_count': layer.featureCount(),
            'field_count': len(layer.fields()),
            'geometry_type': self._get_layer_geometry_type(layer).value,
            'crs': layer.crs().authid() if layer.crs().isValid() else 'Unknown',
            'extent': {
                'xmin': layer.extent().xMinimum(),
                'ymin': layer.extent().yMinimum(),
                'xmax': layer.extent().xMaximum(),
                'ymax': layer.extent().yMaximum()
            } if not layer.extent().isEmpty() else None
        }
        
        return stats
    
    def suggest_field_mappings(self, layer: QgsVectorLayer, geometry_type: GeometryType) -> Dict[str, List[str]]:
        """
        Suggest field mappings for a layer based on common naming patterns.
        
        Args:
            layer: QgsVectorLayer to analyze
            geometry_type: Type of geometry (LINE for pipes, POINT for junctions)
            
        Returns:
            Dictionary mapping required_field -> [suggested_layer_fields]
        """
        if not layer or not layer.isValid():
            return {}
        
        layer_fields = self.get_layer_field_names(layer)
        
        # Determine the type for field suggestions
        if geometry_type == GeometryType.LINE:
            suggestion_type = 'pipes'
        elif geometry_type == GeometryType.POINT:
            suggestion_type = 'junctions'
        else:
            return {}
        
        return SewageNetworkFields.suggest_field_mapping(layer_fields, suggestion_type)
    
    def create_layer_mapping(self, layer: QgsVectorLayer, geometry_type: GeometryType) -> LayerMapping:
        """
        Create a LayerMapping object for a given layer.
        
        Args:
            layer: QgsVectorLayer to map
            geometry_type: Required geometry type
            
        Returns:
            LayerMapping object with basic information filled
        """
        if not layer or not layer.isValid():
            raise ValueError("Invalid layer provided")
        
        mapping = LayerMapping(
            layer_id=layer.id(),
            layer_name=layer.name(),
            geometry_type=geometry_type
        )
        
        # Validate the layer
        validation_result = self.validate_layer_compatibility(layer, geometry_type)
        mapping.validation_errors = validation_result.errors + validation_result.warnings
        mapping.is_valid = validation_result.is_valid
        
        # Add auto-mapping suggestions
        suggestions = self.suggest_field_mappings(layer, geometry_type)
        for required_field, suggested_fields in suggestions.items():
            if suggested_fields:
                # Use the first (best) suggestion as auto-mapping
                mapping.auto_mapped_fields[required_field] = suggested_fields[0]
                mapping.field_mappings[required_field] = suggested_fields[0]
        
        return mapping
    
    def validate_layer_mapping(self, mapping: LayerMapping) -> Tuple[bool, List[str]]:
        """
        Validate a complete layer mapping configuration.
        
        Args:
            mapping: LayerMapping to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Get the layer
        layer = self.project.mapLayer(mapping.layer_id)
        if not layer or not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            errors.append("Layer is no longer available or valid")
            return False, errors
        
        # Validate geometry type
        validation_result = self.validate_layer_compatibility(layer, mapping.geometry_type)
        errors.extend(validation_result.errors)
        
        # Get required fields based on geometry type
        if mapping.geometry_type == GeometryType.LINE:
            required_fields = SewageNetworkFields.get_required_pipe_fields()
        elif mapping.geometry_type == GeometryType.POINT:
            required_fields = SewageNetworkFields.get_required_junction_fields()
        else:
            errors.append(f"Unsupported geometry type: {mapping.geometry_type}")
            return False, errors
        
        # Check that all required fields are mapped or have defaults
        unmapped_fields = mapping.get_unmapped_required_fields(required_fields)
        if unmapped_fields:
            errors.append(f"Required fields not mapped: {', '.join(unmapped_fields)}")
        
        # Validate that mapped fields exist in the layer
        layer_field_names = self.get_layer_field_names(layer)
        for required_field, layer_field in mapping.field_mappings.items():
            if layer_field not in layer_field_names:
                errors.append(f"Mapped field '{layer_field}' for '{required_field}' does not exist in layer")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _get_layer_geometry_type(self, layer: QgsVectorLayer) -> GeometryType:
        """
        Get the geometry type of a layer.
        
        Args:
            layer: QgsVectorLayer to analyze
            
        Returns:
            GeometryType enum value
        """
        if not layer or not layer.isValid():
            raise ValueError("Invalid layer")
        
        wkb_type = layer.wkbType()
        
        if QgsWkbTypes.geometryType(wkb_type) == QgsWkbTypes.LineGeometry:
            return GeometryType.LINE
        elif QgsWkbTypes.geometryType(wkb_type) == QgsWkbTypes.PointGeometry:
            return GeometryType.POINT
        elif QgsWkbTypes.geometryType(wkb_type) == QgsWkbTypes.PolygonGeometry:
            return GeometryType.POLYGON
        else:
            # Default to LINE for unknown types
            return GeometryType.LINE
    
    def _qgis_type_to_field_type(self, qvariant_type: QVariant.Type) -> FieldType:
        """
        Convert QGIS field type to plugin FieldType.
        
        Args:
            qvariant_type: QVariant.Type from QGIS field
            
        Returns:
            FieldType enum value
        """
        if qvariant_type in (QVariant.Int, QVariant.LongLong, QVariant.UInt, QVariant.ULongLong):
            return FieldType.INTEGER
        elif qvariant_type == QVariant.Double:
            return FieldType.DOUBLE
        elif qvariant_type == QVariant.Bool:
            return FieldType.BOOLEAN
        else:
            # Default to STRING for text and unknown types
            return FieldType.STRING
    
    def get_layer_by_id(self, layer_id: str) -> Optional[QgsVectorLayer]:
        """
        Get a layer by its ID.
        
        Args:
            layer_id: QGIS layer ID
            
        Returns:
            QgsVectorLayer if found, None otherwise
        """
        layer = self.project.mapLayer(layer_id)
        if isinstance(layer, QgsVectorLayer) and layer.isValid():
            return layer
        return None
    
    def refresh_layer_mapping(self, mapping: LayerMapping) -> LayerMapping:
        """
        Refresh a layer mapping with current layer information.
        
        Args:
            mapping: Existing LayerMapping to refresh
            
        Returns:
            Updated LayerMapping
        """
        layer = self.get_layer_by_id(mapping.layer_id)
        if not layer:
            mapping.is_valid = False
            mapping.validation_errors = ["Layer no longer exists"]
            return mapping
        
        # Update layer name in case it changed
        mapping.layer_name = layer.name()
        
        # Re-validate the mapping
        is_valid, errors = self.validate_layer_mapping(mapping)
        mapping.is_valid = is_valid
        mapping.validation_errors = errors
        
        return mapping