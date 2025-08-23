"""
Exception classes for the Flexible Sewerage DXF Export Plugin.

This module defines custom exception classes for different types of validation
and export errors, providing structured error handling throughout the plugin.
"""

from typing import List, Optional, Dict, Any


class ValidationError(Exception):
    """Base validation error for all validation-related issues."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 suggestions: Optional[List[str]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            details: Additional error details for debugging
            suggestions: List of suggested solutions
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.suggestions = suggestions or []
    
    def get_user_message(self) -> str:
        """Get user-friendly error message with suggestions."""
        msg = self.message
        if self.suggestions:
            msg += "\n\nSuggested solutions:"
            for i, suggestion in enumerate(self.suggestions, 1):
                msg += f"\n{i}. {suggestion}"
        return msg


class LayerValidationError(ValidationError):
    """Layer-specific validation issues."""
    
    def __init__(self, layer_name: str, message: str, 
                 validation_issues: Optional[List[str]] = None,
                 suggestions: Optional[List[str]] = None):
        """
        Initialize layer validation error.
        
        Args:
            layer_name: Name of the problematic layer
            message: Error message
            validation_issues: List of specific validation problems
            suggestions: List of suggested solutions
        """
        details = {
            'layer_name': layer_name,
            'validation_issues': validation_issues or []
        }
        
        # Default suggestions for layer issues
        default_suggestions = [
            f"Check that layer '{layer_name}' has the correct geometry type",
            "Verify the layer contains valid features",
            "Ensure the layer has the required attribute fields"
        ]
        
        super().__init__(message, details, suggestions or default_suggestions)
        self.layer_name = layer_name
        self.validation_issues = validation_issues or []


class MappingValidationError(ValidationError):
    """Field mapping validation issues."""
    
    def __init__(self, message: str, missing_fields: Optional[List[str]] = None,
                 invalid_mappings: Optional[Dict[str, str]] = None,
                 suggestions: Optional[List[str]] = None):
        """
        Initialize mapping validation error.
        
        Args:
            message: Error message
            missing_fields: List of required fields that are not mapped
            invalid_mappings: Dictionary of invalid field mappings
            suggestions: List of suggested solutions
        """
        details = {
            'missing_fields': missing_fields or [],
            'invalid_mappings': invalid_mappings or {}
        }
        
        # Generate default suggestions based on the error
        default_suggestions = []
        if missing_fields:
            default_suggestions.append("Map the missing required fields or set default values")
            default_suggestions.append("Use the auto-mapping feature to suggest field mappings")
        if invalid_mappings:
            default_suggestions.append("Review and correct the invalid field mappings")
            default_suggestions.append("Check that mapped fields exist in the selected layer")
        
        super().__init__(message, details, suggestions or default_suggestions)
        self.missing_fields = missing_fields or []
        self.invalid_mappings = invalid_mappings or {}


class ExportError(Exception):
    """Export process errors."""
    
    def __init__(self, message: str, error_type: str = "general",
                 failed_features: Optional[List[str]] = None,
                 suggestions: Optional[List[str]] = None):
        """
        Initialize export error.
        
        Args:
            message: Error message
            error_type: Type of export error (file, permission, data, etc.)
            failed_features: List of features that failed to export
            suggestions: List of suggested solutions
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.failed_features = failed_features or []
        self.suggestions = suggestions or []
    
    def get_user_message(self) -> str:
        """Get user-friendly error message with suggestions."""
        msg = self.message
        
        if self.failed_features:
            msg += f"\n\nFailed features ({len(self.failed_features)}):"
            for feature in self.failed_features[:5]:  # Show first 5
                msg += f"\n- {feature}"
            if len(self.failed_features) > 5:
                msg += f"\n... and {len(self.failed_features) - 5} more"
        
        if self.suggestions:
            msg += "\n\nSuggested solutions:"
            for i, suggestion in enumerate(self.suggestions, 1):
                msg += f"\n{i}. {suggestion}"
        
        return msg


class FilePermissionError(ExportError):
    """File permission and access errors."""
    
    def __init__(self, file_path: str, operation: str = "write"):
        """
        Initialize file permission error.
        
        Args:
            file_path: Path to the problematic file
            operation: Type of operation that failed (read, write, create)
        """
        message = f"Cannot {operation} file: {file_path}"
        suggestions = [
            "Check that you have write permissions to the target directory",
            "Ensure the file is not open in another application",
            "Try selecting a different output location",
            "Run QGIS as administrator if necessary"
        ]
        super().__init__(message, "file_permission", suggestions=suggestions)
        self.file_path = file_path
        self.operation = operation


class TemplateError(ExportError):
    """Template loading and processing errors."""
    
    def __init__(self, template_path: str, message: str):
        """
        Initialize template error.
        
        Args:
            template_path: Path to the problematic template
            message: Specific error message
        """
        full_message = f"Template error ({template_path}): {message}"
        suggestions = [
            "Check that the template file exists and is accessible",
            "Verify the template is a valid DXF file",
            "Try using the default template instead",
            "Ensure the template file is not corrupted"
        ]
        super().__init__(full_message, "template", suggestions=suggestions)
        self.template_path = template_path


class GeometryError(ExportError):
    """Geometry processing errors."""
    
    def __init__(self, feature_id: str, geometry_issue: str):
        """
        Initialize geometry error.
        
        Args:
            feature_id: ID of the feature with geometry issues
            geometry_issue: Description of the geometry problem
        """
        message = f"Geometry error in feature {feature_id}: {geometry_issue}"
        suggestions = [
            "Check the feature geometry for validity in QGIS",
            "Use QGIS geometry validation tools to fix issues",
            "Consider excluding invalid features from export",
            "Verify coordinate system compatibility"
        ]
        super().__init__(message, "geometry", [feature_id], suggestions)
        self.feature_id = feature_id
        self.geometry_issue = geometry_issue