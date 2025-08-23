"""
Comprehensive validation framework for the Flexible Sewerage DXF Export Plugin.

This module provides validation at layer, mapping, and export levels with
graceful error recovery and detailed progress reporting.
"""

import os
import stat
from typing import List, Dict, Tuple, Optional, Any, Callable
from pathlib import Path

from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsWkbTypes,
    QgsProject, QgsMessageLog, Qgis
)

from .exceptions import (
    ValidationError, LayerValidationError, MappingValidationError,
    ExportError, FilePermissionError, GeometryError
)
from .field_definitions import SewageNetworkFields
from .data_structures import GeometryType, FieldType
from .data_structures import LayerMapping, ExportConfiguration


class ValidationResult:
    """Container for validation results with detailed feedback."""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None, info: Optional[List[str]] = None):
        """
        Initialize validation result.
        
        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
            info: List of informational messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.info = info or []
    
    def add_error(self, message: str):
        """Add an error message and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an informational message."""
        self.info.append(message)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        if not other.is_valid:
            self.is_valid = False
    
    def get_summary(self) -> str:
        """Get a summary of validation results."""
        parts = []
        if self.errors:
            parts.append(f"Errors: {len(self.errors)}")
        if self.warnings:
            parts.append(f"Warnings: {len(self.warnings)}")
        if self.info:
            parts.append(f"Info: {len(self.info)}")
        
        status = "Valid" if self.is_valid else "Invalid"
        summary = f"Validation: {status}"
        if parts:
            summary += f" ({', '.join(parts)})"
        
        return summary


class ProgressReporter:
    """Progress reporting for validation and export operations."""
    
    def __init__(self, total_steps: int = 100, callback: Optional[Callable] = None):
        """
        Initialize progress reporter.
        
        Args:
            total_steps: Total number of steps in the operation
            callback: Optional callback function for progress updates
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
        self.messages = []
        self.errors = []
        self.warnings = []
    
    def update(self, step: int, message: str = ""):
        """Update progress with current step and message."""
        self.current_step = step
        if message:
            self.messages.append(f"Step {step}/{self.total_steps}: {message}")
        
        if self.callback:
            progress = int((step / self.total_steps) * 100)
            self.callback(progress, message)
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        QgsMessageLog.logMessage(f"Error: {message}", "RedBasica Export", Qgis.Critical)
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        QgsMessageLog.logMessage(f"Warning: {message}", "RedBasica Export", Qgis.Warning)
    
    def get_progress_percentage(self) -> int:
        """Get current progress as percentage."""
        return int((self.current_step / self.total_steps) * 100)


class LayerValidator:
    """Validates QGIS vector layers for sewerage network export."""
    
    @staticmethod
    def validate_layer_basic(layer: QgsVectorLayer) -> ValidationResult:
        """
        Perform basic layer validation.
        
        Args:
            layer: QGIS vector layer to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult()
        
        if not layer:
            result.add_error("Layer is None or invalid")
            return result
        
        if not layer.isValid():
            result.add_error(f"Layer '{layer.name()}' is not valid")
            return result
        
        if layer.featureCount() == 0:
            result.add_warning(f"Layer '{layer.name()}' contains no features")
        
        # Check if layer is editable (might indicate unsaved changes)
        if layer.isEditable():
            result.add_warning(f"Layer '{layer.name()}' is in edit mode - consider saving changes")
        
        result.add_info(f"Layer '{layer.name()}' has {layer.featureCount()} features")
        
        return result
    
    @staticmethod
    def validate_geometry_type(layer: QgsVectorLayer, required_type: GeometryType) -> ValidationResult:
        """
        Validate layer geometry type matches requirements.
        
        Args:
            layer: QGIS vector layer to validate
            required_type: Required geometry type
            
        Returns:
            ValidationResult with geometry type validation
        """
        result = ValidationResult()
        
        if not layer or not layer.isValid():
            result.add_error("Cannot validate geometry type - layer is invalid")
            return result
        
        layer_geom_type = layer.geometryType()
        
        # Map QGIS geometry types to our enum
        type_mapping = {
            QgsWkbTypes.LineGeometry: GeometryType.LINE,
            QgsWkbTypes.PointGeometry: GeometryType.POINT,
            QgsWkbTypes.PolygonGeometry: GeometryType.POLYGON
        }
        
        actual_type = type_mapping.get(layer_geom_type)
        
        if actual_type != required_type:
            result.add_error(
                f"Layer '{layer.name()}' has {actual_type.value if actual_type else 'unknown'} "
                f"geometry, but {required_type.value} is required"
            )
        else:
            result.add_info(f"Layer '{layer.name()}' has correct geometry type: {required_type.value}")
        
        return result
    
    @staticmethod
    def validate_layer_fields(layer: QgsVectorLayer, required_fields: List[str]) -> ValidationResult:
        """
        Validate that layer contains required fields.
        
        Args:
            layer: QGIS vector layer to validate
            required_fields: List of required field names
            
        Returns:
            ValidationResult with field validation
        """
        result = ValidationResult()
        
        if not layer or not layer.isValid():
            result.add_error("Cannot validate fields - layer is invalid")
            return result
        
        layer_fields = [field.name() for field in layer.fields()]
        missing_fields = [field for field in required_fields if field not in layer_fields]
        
        if missing_fields:
            result.add_warning(f"Layer '{layer.name()}' missing fields: {', '.join(missing_fields)}")
        else:
            result.add_info(f"Layer '{layer.name()}' contains all required fields")
        
        return result
    
    @staticmethod
    def validate_feature_geometries(layer: QgsVectorLayer, max_check: int = 100) -> ValidationResult:
        """
        Validate feature geometries in the layer.
        
        Args:
            layer: QGIS vector layer to validate
            max_check: Maximum number of features to check
            
        Returns:
            ValidationResult with geometry validation
        """
        result = ValidationResult()
        
        if not layer or not layer.isValid():
            result.add_error("Cannot validate geometries - layer is invalid")
            return result
        
        invalid_count = 0
        null_count = 0
        checked_count = 0
        
        for feature in layer.getFeatures():
            if checked_count >= max_check:
                break
            
            geometry = feature.geometry()
            if geometry.isNull():
                null_count += 1
            elif not geometry.isGeosValid():
                invalid_count += 1
            
            checked_count += 1
        
        if null_count > 0:
            result.add_warning(f"Layer '{layer.name()}' has {null_count} features with null geometry")
        
        if invalid_count > 0:
            result.add_warning(f"Layer '{layer.name()}' has {invalid_count} features with invalid geometry")
        
        if null_count == 0 and invalid_count == 0:
            result.add_info(f"All checked geometries in layer '{layer.name()}' are valid")
        
        return result


class MappingValidator:
    """Validates field mappings for sewerage network export."""
    
    @staticmethod
    def validate_mapping_completeness(mapping: LayerMapping, required_fields: List[str]) -> ValidationResult:
        """
        Validate that all required fields are mapped or have defaults.
        
        Args:
            mapping: Layer mapping to validate
            required_fields: List of required field names
            
        Returns:
            ValidationResult with mapping validation
        """
        result = ValidationResult()
        
        missing_mappings = []
        for field in required_fields:
            if field not in mapping.field_mappings and field not in mapping.default_values:
                missing_mappings.append(field)
        
        if missing_mappings:
            result.add_error(f"Missing mappings for required fields: {', '.join(missing_mappings)}")
        else:
            result.add_info("All required fields are mapped or have default values")
        
        return result
    
    @staticmethod
    def validate_field_existence(layer: QgsVectorLayer, mapping: LayerMapping) -> ValidationResult:
        """
        Validate that mapped fields exist in the layer.
        
        Args:
            layer: QGIS vector layer
            mapping: Layer mapping to validate
            
        Returns:
            ValidationResult with field existence validation
        """
        result = ValidationResult()
        
        if not layer or not layer.isValid():
            result.add_error("Cannot validate field existence - layer is invalid")
            return result
        
        layer_fields = [field.name() for field in layer.fields()]
        missing_fields = []
        
        for required_field, mapped_field in mapping.field_mappings.items():
            if mapped_field not in layer_fields:
                missing_fields.append(f"{required_field} -> {mapped_field}")
        
        if missing_fields:
            result.add_error(f"Mapped fields not found in layer: {', '.join(missing_fields)}")
        else:
            result.add_info("All mapped fields exist in the layer")
        
        return result
    
    @staticmethod
    def validate_data_types(layer: QgsVectorLayer, mapping: LayerMapping, 
                          field_definitions: Dict[str, FieldType]) -> ValidationResult:
        """
        Validate data types of mapped fields.
        
        Args:
            layer: QGIS vector layer
            mapping: Layer mapping to validate
            field_definitions: Expected field types
            
        Returns:
            ValidationResult with data type validation
        """
        result = ValidationResult()
        
        if not layer or not layer.isValid():
            result.add_error("Cannot validate data types - layer is invalid")
            return result
        
        layer_fields = {field.name(): field for field in layer.fields()}
        type_mismatches = []
        
        for required_field, mapped_field in mapping.field_mappings.items():
            if mapped_field in layer_fields and required_field in field_definitions:
                layer_field = layer_fields[mapped_field]
                expected_type = field_definitions[required_field]
                
                # Check type compatibility (simplified)
                qgis_type = layer_field.type()
                compatible = True
                
                if expected_type == FieldType.DOUBLE and qgis_type not in [6, 2]:  # QVariant.Double, Int
                    compatible = False
                elif expected_type == FieldType.INTEGER and qgis_type != 2:  # QVariant.Int
                    compatible = False
                elif expected_type == FieldType.STRING and qgis_type != 10:  # QVariant.String
                    compatible = False
                
                if not compatible:
                    type_mismatches.append(f"{required_field} ({expected_type.value}) -> {mapped_field} ({layer_field.typeName()})")
        
        if type_mismatches:
            result.add_warning(f"Type mismatches (will attempt conversion): {', '.join(type_mismatches)}")
        else:
            result.add_info("All mapped field types are compatible")
        
        return result


class ExportValidator:
    """Validates export configuration and file operations."""
    
    @staticmethod
    def validate_output_path(output_path: str) -> ValidationResult:
        """
        Validate output file path and permissions.
        
        Args:
            output_path: Path to output DXF file
            
        Returns:
            ValidationResult with path validation
        """
        result = ValidationResult()
        
        if not output_path:
            result.add_error("Output path is empty")
            return result
        
        try:
            path = Path(output_path)
            
            # Check if directory exists
            if not path.parent.exists():
                result.add_error(f"Output directory does not exist: {path.parent}")
                return result
            
            # Check write permissions on directory
            if not os.access(path.parent, os.W_OK):
                result.add_error(f"No write permission to directory: {path.parent}")
                return result
            
            # Check if file exists and is writable
            if path.exists():
                if not os.access(path, os.W_OK):
                    result.add_error(f"Cannot overwrite existing file: {path}")
                    return result
                result.add_warning(f"File will be overwritten: {path}")
            
            # Check file extension
            if path.suffix.lower() != '.dxf':
                result.add_warning(f"File extension is not .dxf: {path.suffix}")
            
            result.add_info(f"Output path is valid: {output_path}")
            
        except Exception as e:
            result.add_error(f"Invalid output path: {e}")
        
        return result
    
    @staticmethod
    def validate_template_path(template_path: Optional[str]) -> ValidationResult:
        """
        Validate DXF template file path.
        
        Args:
            template_path: Path to template DXF file (optional)
            
        Returns:
            ValidationResult with template validation
        """
        result = ValidationResult()
        
        if not template_path:
            result.add_info("No template specified - will use default template")
            return result
        
        try:
            path = Path(template_path)
            
            if not path.exists():
                result.add_error(f"Template file does not exist: {template_path}")
                return result
            
            if not os.access(path, os.R_OK):
                result.add_error(f"Cannot read template file: {template_path}")
                return result
            
            if path.suffix.lower() != '.dxf':
                result.add_warning(f"Template file extension is not .dxf: {path.suffix}")
            
            # Check file size (basic validation)
            file_size = path.stat().st_size
            if file_size == 0:
                result.add_error(f"Template file is empty: {template_path}")
            elif file_size > 50 * 1024 * 1024:  # 50MB
                result.add_warning(f"Template file is very large ({file_size / 1024 / 1024:.1f}MB)")
            
            result.add_info(f"Template file is valid: {template_path}")
            
        except Exception as e:
            result.add_error(f"Error validating template: {e}")
        
        return result
    
    @staticmethod
    def validate_export_configuration(config: ExportConfiguration) -> ValidationResult:
        """
        Validate complete export configuration.
        
        Args:
            config: Export configuration to validate
            
        Returns:
            ValidationResult with configuration validation
        """
        result = ValidationResult()
        
        # Validate output path
        path_result = ExportValidator.validate_output_path(config.output_path)
        result.merge(path_result)
        
        # Validate template path
        template_result = ExportValidator.validate_template_path(config.template_path)
        result.merge(template_result)
        
        # Validate scale factor
        if config.scale_factor <= 0:
            result.add_error(f"Scale factor must be positive: {config.scale_factor}")
        elif config.scale_factor < 100 or config.scale_factor > 10000:
            result.add_warning(f"Unusual scale factor: {config.scale_factor}")
        
        # Validate layer prefix
        if config.layer_prefix and len(config.layer_prefix) > 10:
            result.add_warning(f"Layer prefix is very long: '{config.layer_prefix}'")
        
        return result


class ComprehensiveValidator:
    """Main validator that orchestrates all validation levels."""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Initialize comprehensive validator.
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback
        self.layer_validator = LayerValidator()
        self.mapping_validator = MappingValidator()
        self.export_validator = ExportValidator()
    
    def validate_complete_configuration(self, config: ExportConfiguration) -> ValidationResult:
        """
        Perform complete validation of export configuration.
        
        Args:
            config: Export configuration to validate
            
        Returns:
            ValidationResult with complete validation results
        """
        reporter = ProgressReporter(10, self.progress_callback)
        result = ValidationResult()
        
        try:
            # Step 1: Validate export configuration
            reporter.update(1, "Validating export configuration...")
            config_result = self.export_validator.validate_export_configuration(config)
            result.merge(config_result)
            
            # Step 2: Validate pipes layer
            reporter.update(3, "Validating pipes layer...")
            if config.pipes_mapping and config.pipes_mapping.layer_id:
                layer = QgsProject.instance().mapLayer(config.pipes_mapping.layer_id)
                pipes_result = self._validate_layer_mapping(
                    layer, config.pipes_mapping, GeometryType.LINE, "pipes"
                )
                result.merge(pipes_result)
            else:
                result.add_error("No pipes layer configured")
            
            # Step 3: Validate junctions layer
            reporter.update(5, "Validating junctions layer...")
            if config.junctions_mapping and config.junctions_mapping.layer_id:
                layer = QgsProject.instance().mapLayer(config.junctions_mapping.layer_id)
                junctions_result = self._validate_layer_mapping(
                    layer, config.junctions_mapping, GeometryType.POINT, "junctions"
                )
                result.merge(junctions_result)
            else:
                result.add_warning("No junctions layer configured")
            
            # Step 4: Cross-validation
            reporter.update(8, "Performing cross-validation...")
            cross_result = self._validate_cross_references(config)
            result.merge(cross_result)
            
            reporter.update(10, "Validation complete")
            
        except Exception as e:
            result.add_error(f"Validation failed with exception: {e}")
            reporter.add_error(f"Validation exception: {e}")
        
        return result
    
    def _validate_layer_mapping(self, layer: QgsVectorLayer, mapping: LayerMapping,
                              required_geometry: GeometryType, layer_type: str) -> ValidationResult:
        """
        Validate a single layer mapping.
        
        Args:
            layer: QGIS vector layer
            mapping: Layer mapping configuration
            required_geometry: Required geometry type
            layer_type: Type description for error messages
            
        Returns:
            ValidationResult with layer mapping validation
        """
        result = ValidationResult()
        
        # Basic layer validation
        basic_result = self.layer_validator.validate_layer_basic(layer)
        result.merge(basic_result)
        
        if not basic_result.is_valid:
            return result
        
        # Geometry type validation
        geom_result = self.layer_validator.validate_geometry_type(layer, required_geometry)
        result.merge(geom_result)
        
        # Field mapping validation
        mapping_result = self.mapping_validator.validate_field_existence(layer, mapping)
        result.merge(mapping_result)
        
        # Get required fields based on layer type
        if layer_type == "pipes":
            required_fields = [field.name for field in SewageNetworkFields.PIPES_REQUIRED]
        else:
            required_fields = [field.name for field in SewageNetworkFields.JUNCTIONS_REQUIRED]
        
        completeness_result = self.mapping_validator.validate_mapping_completeness(mapping, required_fields)
        result.merge(completeness_result)
        
        # Geometry validation (sample)
        geometry_result = self.layer_validator.validate_feature_geometries(layer, max_check=50)
        result.merge(geometry_result)
        
        return result
    
    def _validate_cross_references(self, config: ExportConfiguration) -> ValidationResult:
        """
        Validate cross-references between pipes and junctions.
        
        Args:
            config: Export configuration
            
        Returns:
            ValidationResult with cross-reference validation
        """
        result = ValidationResult()
        
        # This is a simplified cross-reference validation
        # In a full implementation, you would check that pipe upstream/downstream
        # nodes reference valid junction IDs
        
        if config.pipes_mapping and config.junctions_mapping:
            result.add_info("Cross-reference validation would check pipe-junction connectivity")
        else:
            result.add_warning("Cannot perform cross-reference validation - missing layer mappings")
        
        return result