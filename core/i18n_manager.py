# -*- coding: utf-8 -*-
"""
Internationalization manager for RedBasica Export plugin.

This module provides comprehensive translation support including:
- UI string translations
- Field display names and descriptions
- Error messages
- Locale detection and QTranslator integration
"""

import os
from typing import Dict, Optional

# Handle QGIS imports gracefully for testing
try:
    from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QSettings
    from qgis.core import QgsMessageLog, Qgis
    QGIS_AVAILABLE = True
except ImportError:
    # Mock classes for testing outside QGIS
    class QTranslator:
        def load(self, *args): return False
        def translate(self, *args): return args[-1] if args else ""
    
    class QCoreApplication:
        @staticmethod
        def installTranslator(translator): pass
        @staticmethod
        def removeTranslator(translator): pass
        @staticmethod
        def translate(context, text, disambiguation=None, n=-1): return text
    
    class QSettings:
        def value(self, key, default=None): return default
    
    class QgsMessageLog:
        @staticmethod
        def logMessage(message, tag="", level=0): print(f"[{tag}] {message}")
    
    class Qgis:
        Info = 0
        Warning = 1
        Critical = 2
    
    QGIS_AVAILABLE = False


class I18nManager:
    """
    Manages internationalization for the RedBasica Export plugin.
    
    Provides translation services for UI strings, field names, error messages,
    and integrates with QGIS locale detection.
    """
    
    def __init__(self, plugin_dir: str):
        """
        Initialize the internationalization manager.
        
        Args:
            plugin_dir: Path to the plugin directory
        """
        self.plugin_dir = plugin_dir
        self.translator = None
        self.current_locale = None
        self.available_locales = ['en', 'pt']  # English and Portuguese
        
        # Initialize translation system
        self._setup_translation()
    
    def _setup_translation(self):
        """Set up translation system with QGIS locale detection."""
        try:
            # Get QGIS locale setting
            locale = QSettings().value('locale/userLocale', 'en')[0:2]
            
            # Fallback to English if locale not supported
            if locale not in self.available_locales:
                locale = 'en'
            
            self.current_locale = locale
            
            # Load translation file
            self._load_translation(locale)
            
            QgsMessageLog.logMessage(
                f"I18n initialized for locale: {locale}",
                "RedBasica Export", Qgis.Info
            )
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Failed to setup translation: {e}",
                "RedBasica Export", Qgis.Warning
            )
            self.current_locale = 'en'
    
    def _load_translation(self, locale: str):
        """
        Load translation file for the specified locale.
        
        Args:
            locale: Language code (e.g., 'en', 'pt')
        """
        if locale == 'en':
            # English is the source language, no translation needed
            return
        
        translation_file = os.path.join(
            self.plugin_dir, 'i18n', f'redbasica_export_{locale}.qm'
        )
        
        if os.path.exists(translation_file):
            self.translator = QTranslator()
            if self.translator.load(translation_file):
                QCoreApplication.installTranslator(self.translator)
                QgsMessageLog.logMessage(
                    f"Translation loaded: {translation_file}",
                    "RedBasica Export", Qgis.Info
                )
            else:
                QgsMessageLog.logMessage(
                    f"Failed to load translation: {translation_file}",
                    "RedBasica Export", Qgis.Warning
                )
        else:
            QgsMessageLog.logMessage(
                f"Translation file not found: {translation_file}",
                "RedBasica Export", Qgis.Info
            )
    
    def tr(self, message: str, context: str = 'RedBasicaExport') -> str:
        """
        Translate a string using Qt translation system.
        
        Args:
            message: String to translate
            context: Translation context (default: 'RedBasicaExport')
            
        Returns:
            Translated string
        """
        return QCoreApplication.translate(context, message)
    
    def get_field_display_name(self, field_name: str) -> str:
        """
        Get localized display name for a field.
        
        Args:
            field_name: Internal field name
            
        Returns:
            Localized display name
        """
        field_names = {
            # Pipe fields
            'pipe_id': self.tr('Pipe Identifier'),
            'upstream_node': self.tr('Upstream Node'),
            'downstream_node': self.tr('Downstream Node'),
            'length': self.tr('Length'),
            'diameter': self.tr('Diameter'),
            'upstream_invert': self.tr('Upstream Invert'),
            'downstream_invert': self.tr('Downstream Invert'),
            'upstream_ground': self.tr('Upstream Ground'),
            'downstream_ground': self.tr('Downstream Ground'),
            'slope': self.tr('Slope'),
            'material': self.tr('Material'),
            'notes': self.tr('Notes'),
            
            # Junction fields
            'node_id': self.tr('Node Identifier'),
            'ground_elevation': self.tr('Ground Elevation'),
            'invert_elevation': self.tr('Invert Elevation'),
            
            # Calculated fields
            'upstream_depth': self.tr('Upstream Depth'),
            'downstream_depth': self.tr('Downstream Depth'),
            'calculated_slope': self.tr('Calculated Slope'),
        }
        
        return field_names.get(field_name, field_name)
    
    def get_field_description(self, field_name: str) -> str:
        """
        Get localized description for a field.
        
        Args:
            field_name: Internal field name
            
        Returns:
            Localized field description
        """
        descriptions = {
            # Pipe fields
            'pipe_id': self.tr('Unique identifier for each pipe segment'),
            'upstream_node': self.tr('Identifier of upstream manhole or junction'),
            'downstream_node': self.tr('Identifier of downstream manhole or junction'),
            'length': self.tr('Pipe length in meters'),
            'diameter': self.tr('Pipe diameter in millimeters'),
            'upstream_invert': self.tr('Upstream invert elevation in meters'),
            'downstream_invert': self.tr('Downstream invert elevation in meters'),
            'upstream_ground': self.tr('Upstream ground surface elevation in meters'),
            'downstream_ground': self.tr('Downstream ground surface elevation in meters'),
            'slope': self.tr('Pipe slope in meters per meter (m/m)'),
            'material': self.tr('Pipe material (e.g., PVC, concrete, etc.)'),
            'notes': self.tr('Additional notes or observations'),
            
            # Junction fields
            'node_id': self.tr('Unique identifier for each junction or manhole'),
            'ground_elevation': self.tr('Ground surface elevation at junction in meters'),
            'invert_elevation': self.tr('Junction invert elevation in meters'),
            
            # Calculated fields
            'upstream_depth': self.tr('Calculated depth at upstream end (ground - invert)'),
            'downstream_depth': self.tr('Calculated depth at downstream end (ground - invert)'),
            'calculated_slope': self.tr('Calculated slope from elevation difference and length'),
        }
        
        return descriptions.get(field_name, '')
    
    def get_error_message(self, error_key: str, **kwargs) -> str:
        """
        Get localized error message.
        
        Args:
            error_key: Error message key
            **kwargs: Format parameters for the message
            
        Returns:
            Localized error message
        """
        error_messages = {
            # Layer validation errors
            'layer_not_found': self.tr('Layer "{layer_name}" not found in project'),
            'invalid_geometry_type': self.tr('Layer "{layer_name}" has invalid geometry type. Expected: {expected}, Found: {found}'),
            'no_features': self.tr('Layer "{layer_name}" contains no features'),
            'missing_required_fields': self.tr('Layer "{layer_name}" is missing required fields: {fields}'),
            
            # Mapping validation errors
            'field_not_mapped': self.tr('Required field "{field_name}" is not mapped'),
            'invalid_field_mapping': self.tr('Field "{field_name}" is mapped to non-existent layer field "{layer_field}"'),
            'type_conversion_failed': self.tr('Failed to convert value "{value}" to {target_type} for field "{field_name}"'),
            
            # Export errors
            'output_path_invalid': self.tr('Output path is invalid or not writable: {path}'),
            'template_not_found': self.tr('Template file not found: {template_path}'),
            'dxf_creation_failed': self.tr('Failed to create DXF file: {error}'),
            'geometry_processing_failed': self.tr('Failed to process geometry for feature {feature_id}: {error}'),
            
            # General errors
            'dependency_missing': self.tr('Required dependency not available: {dependency}'),
            'file_permission_denied': self.tr('Permission denied accessing file: {file_path}'),
            'unexpected_error': self.tr('An unexpected error occurred: {error}'),
        }
        
        message_template = error_messages.get(error_key, error_key)
        
        try:
            return message_template.format(**kwargs)
        except KeyError as e:
            return f"{message_template} (Missing parameter: {e})"
    
    def get_ui_text(self, key: str) -> str:
        """
        Get localized UI text.
        
        Args:
            key: UI text key
            
        Returns:
            Localized UI text
        """
        ui_texts = {
            # Dialog titles
            'main_dialog_title': self.tr('Flexible Sewerage Network DXF Export'),
            'layer_selector_title': self.tr('Select Layer'),
            'attribute_mapper_title': self.tr('Configure Field Mapping'),
            
            # Group titles
            'layer_selection': self.tr('Layer Selection'),
            'export_options': self.tr('Export Options'),
            'advanced_options': self.tr('Advanced Options'),
            'validation_results': self.tr('Validation Results'),
            
            # Labels
            'pipes_layer': self.tr('Pipes Layer:'),
            'junctions_layer': self.tr('Junctions Layer:'),
            'output_file': self.tr('Output File:'),
            'scale_factor': self.tr('Scale Factor:'),
            'layer_prefix': self.tr('Layer Prefix:'),
            'template_file': self.tr('Template File:'),
            
            # Buttons
            'configure_fields': self.tr('Configure Fields...'),
            'browse': self.tr('Browse...'),
            'export': self.tr('Export'),
            'cancel': self.tr('Cancel'),
            'ok': self.tr('OK'),
            'apply': self.tr('Apply'),
            'reset': self.tr('Reset'),
            'auto_map': self.tr('Auto Map'),
            
            # Checkboxes
            'include_arrows': self.tr('Include flow arrows'),
            'include_labels': self.tr('Include pipe labels'),
            'include_elevations': self.tr('Include elevation data'),
            'use_template': self.tr('Use custom template'),
            
            # Status messages
            'validation_passed': self.tr('Validation passed - ready to export'),
            'validation_failed': self.tr('Validation failed - please fix errors'),
            'export_in_progress': self.tr('Exporting sewerage network...'),
            'export_complete': self.tr('Export completed successfully'),
            'export_failed': self.tr('Export failed'),
            
            # Tooltips
            'pipes_layer_tooltip': self.tr('Select any line layer containing pipe/conduit data'),
            'junctions_layer_tooltip': self.tr('Select any point layer containing junction/manhole data'),
            'output_path_tooltip': self.tr('Path where the DXF file will be saved'),
            'scale_factor_tooltip': self.tr('Scale factor for text and symbol sizing'),
            'layer_prefix_tooltip': self.tr('Prefix added to all DXF layer names'),
            'template_tooltip': self.tr('Optional DXF template file with predefined blocks and styles'),
        }
        
        return ui_texts.get(key, key)
    
    def get_current_locale(self) -> str:
        """
        Get current locale code.
        
        Returns:
            Current locale code (e.g., 'en', 'pt')
        """
        return self.current_locale
    
    def get_available_locales(self) -> list:
        """
        Get list of available locale codes.
        
        Returns:
            List of available locale codes
        """
        return self.available_locales.copy()


# Global instance (will be initialized by plugin)
i18n_manager: Optional[I18nManager] = None


def tr(message: str, context: str = 'RedBasicaExport') -> str:
    """
    Global translation function.
    
    Args:
        message: String to translate
        context: Translation context
        
    Returns:
        Translated string
    """
    if i18n_manager:
        return i18n_manager.tr(message, context)
    else:
        # Fallback to Qt translation if manager not initialized
        return QCoreApplication.translate(context, message)


def init_i18n(plugin_dir: str) -> I18nManager:
    """
    Initialize global i18n manager.
    
    Args:
        plugin_dir: Path to plugin directory
        
    Returns:
        Initialized I18nManager instance
    """
    global i18n_manager
    i18n_manager = I18nManager(plugin_dir)
    return i18n_manager