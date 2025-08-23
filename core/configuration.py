# -*- coding: utf-8 -*-
"""
Configuration management for RedBasica Export plugin.

This module handles persistence of export configurations, user preferences,
template paths, and field mappings using QSettings for cross-session storage.
"""

import json
import os
from typing import Dict, List, Optional, Any

# Handle QGIS imports gracefully for testing
try:
    from qgis.PyQt.QtCore import QSettings
    QGIS_AVAILABLE = True
except ImportError:
    # Mock QSettings for testing outside QGIS
    class QSettings:
        def __init__(self, *args): 
            self._data = {}
        def setValue(self, key, value): 
            self._data[key] = value
        def value(self, key, default=None): 
            return self._data.get(key, default)
        def sync(self): 
            pass
        def clear(self): 
            self._data.clear()
        def remove(self, key): 
            self._data.pop(key, None)
        def beginGroup(self, group): 
            pass
        def endGroup(self): 
            pass
        def childKeys(self): 
            return []
    QGIS_AVAILABLE = False

from .data_structures import ExportConfiguration, LayerMapping, GeometryType


class Configuration:
    """
    Manages plugin settings persistence and configuration management.
    
    Uses QSettings to store user preferences, export configurations,
    template paths, and field mappings across QGIS sessions.
    """
    
    def __init__(self, organization: str = "RedBasica", application: str = "Export"):
        """
        Initialize configuration manager.
        
        Args:
            organization: Organization name for QSettings
            application: Application name for QSettings
        """
        self.settings = QSettings(organization, application)
        self._current_config: Optional[ExportConfiguration] = None
        
        # Configuration keys
        self.KEYS = {
            'last_export_config': 'export/last_configuration',
            'user_preferences': 'user/preferences',
            'template_paths': 'templates/paths',
            'field_mappings': 'mappings/field_mappings',
            'recent_outputs': 'export/recent_output_paths',
            'ui_settings': 'ui/settings',
            'layer_preferences': 'layers/preferences',
        }
    
    def save_export_configuration(self, config: ExportConfiguration, name: str = "last") -> bool:
        """
        Save an export configuration to persistent storage.
        
        Args:
            config: ExportConfiguration to save
            name: Configuration name (default: "last")
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            print(f"DEBUG: save_export_configuration called with config: {config}")
            print(f"DEBUG: config.pipes_mapping: {config.pipes_mapping}")
            print(f"DEBUG: config.junctions_mapping: {config.junctions_mapping}")
            
            config_dict = self._export_config_to_dict(config)
            print(f"DEBUG: config_dict after conversion: {config_dict}")
            
            json_str = json.dumps(config_dict)
            print(f"DEBUG: JSON string length: {len(json_str)}")
            
            if name == "last":
                self.settings.setValue(self.KEYS['last_export_config'], json_str)
            else:
                key = f"export/saved_configurations/{name}"
                self.settings.setValue(key, json_str)
            
            self.settings.sync()
            print(f"DEBUG: Configuration saved successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Error saving export configuration: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return False
    
    def load_export_configuration(self, name: str = "last") -> Optional[ExportConfiguration]:
        """
        Load an export configuration from persistent storage.
        
        Args:
            name: Configuration name to load (default: "last")
            
        Returns:
            ExportConfiguration if found, None otherwise
        """
        try:
            print(f"DEBUG: load_export_configuration called with name: {name}")
            
            if name == "last":
                config_json = self.settings.value(self.KEYS['last_export_config'])
            else:
                key = f"export/saved_configurations/{name}"
                config_json = self.settings.value(key)
            
            print(f"DEBUG: Loaded JSON string length: {len(config_json) if config_json else 0}")
            
            if config_json:
                config_dict = json.loads(config_json)
                print(f"DEBUG: Loaded config_dict keys: {list(config_dict.keys())}")
                result = self._dict_to_export_config(config_dict)
                print(f"DEBUG: Loaded configuration result: {result}")
                return result
            
            return None
            
        except Exception as e:
            print(f"Error loading export configuration: {e}")
            return None
    
    def has_export_configuration(self, name: str = "last") -> bool:
        """
        Check if an export configuration exists.
        
        Args:
            name: Configuration name to check (default: "last")
            
        Returns:
            True if configuration exists, False otherwise
        """
        try:
            if name == "last":
                config_json = self.settings.value(self.KEYS['last_export_config'])
            else:
                key = f"export/saved_configurations/{name}"
                config_json = self.settings.value(key)
            
            return config_json is not None and config_json != ""
            
        except Exception:
            return False
    
    def get_saved_configuration_names(self) -> List[str]:
        """
        Get list of saved configuration names.
        
        Returns:
            List of configuration names
        """
        try:
            self.settings.beginGroup("export/saved_configurations")
            names = self.settings.childKeys()
            self.settings.endGroup()
            return names
        except Exception:
            return []
    
    def delete_saved_configuration(self, name: str) -> bool:
        """
        Delete a saved configuration.
        
        Args:
            name: Configuration name to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            key = f"export/saved_configurations/{name}"
            self.settings.remove(key)
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Save user preferences.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.settings.setValue(self.KEYS['user_preferences'], json.dumps(preferences))
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error saving user preferences: {e}")
            return False
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """
        Load user preferences.
        
        Returns:
            Dictionary of user preferences with defaults
        """
        try:
            prefs_json = self.settings.value(self.KEYS['user_preferences'])
            if prefs_json:
                return json.loads(prefs_json)
        except Exception as e:
            print(f"Error loading user preferences: {e}")
        
        # Return default preferences
        return {
            'default_scale_factor': 2000,
            'default_layer_prefix': 'ESG_',
            'include_arrows_default': True,
            'include_labels_default': True,
            'include_elevations_default': True,
            'default_label_format': '{length:.0f}-{diameter:.0f}-{slope:.5f}',
            'auto_save_config': True,
            'show_validation_warnings': True,
            'remember_window_size': True,
        }
    
    def save_template_paths(self, template_paths: Dict[str, str]) -> bool:
        """
        Save template file paths.
        
        Args:
            template_paths: Dictionary mapping template names to file paths
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate paths exist before saving
            valid_paths = {}
            for name, path in template_paths.items():
                if path and os.path.exists(path):
                    valid_paths[name] = path
            
            self.settings.setValue(self.KEYS['template_paths'], json.dumps(valid_paths))
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error saving template paths: {e}")
            return False
    
    def load_template_paths(self) -> Dict[str, str]:
        """
        Load template file paths.
        
        Returns:
            Dictionary mapping template names to file paths
        """
        try:
            paths_json = self.settings.value(self.KEYS['template_paths'])
            if paths_json:
                paths = json.loads(paths_json)
                # Validate paths still exist
                valid_paths = {}
                for name, path in paths.items():
                    if path and os.path.exists(path):
                        valid_paths[name] = path
                return valid_paths
        except Exception as e:
            print(f"Error loading template paths: {e}")
        
        return {}
    
    def add_template_path(self, name: str, path: str) -> bool:
        """
        Add a new template path.
        
        Args:
            name: Template name
            path: File path to template
            
        Returns:
            True if added successfully, False otherwise
        """
        if not os.path.exists(path):
            return False
        
        template_paths = self.load_template_paths()
        template_paths[name] = path
        return self.save_template_paths(template_paths)
    
    def remove_template_path(self, name: str) -> bool:
        """
        Remove a template path.
        
        Args:
            name: Template name to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        template_paths = self.load_template_paths()
        if name in template_paths:
            del template_paths[name]
            return self.save_template_paths(template_paths)
        return False
    
    def save_field_mappings(self, layer_id: str, mappings: Dict[str, str]) -> bool:
        """
        Save field mappings for a specific layer.
        
        Args:
            layer_id: QGIS layer ID
            mappings: Dictionary mapping required fields to layer fields
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            all_mappings = self.load_all_field_mappings()
            all_mappings[layer_id] = mappings
            
            self.settings.setValue(self.KEYS['field_mappings'], json.dumps(all_mappings))
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error saving field mappings: {e}")
            return False
    
    def load_field_mappings(self, layer_id: str) -> Dict[str, str]:
        """
        Load field mappings for a specific layer.
        
        Args:
            layer_id: QGIS layer ID
            
        Returns:
            Dictionary mapping required fields to layer fields
        """
        all_mappings = self.load_all_field_mappings()
        return all_mappings.get(layer_id, {})
    
    def load_all_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Load all field mappings.
        
        Returns:
            Dictionary mapping layer IDs to field mappings
        """
        try:
            mappings_json = self.settings.value(self.KEYS['field_mappings'])
            if mappings_json:
                return json.loads(mappings_json)
        except Exception as e:
            print(f"Error loading field mappings: {e}")
        
        return {}
    
    def add_recent_output_path(self, path: str, max_recent: int = 10) -> bool:
        """
        Add a path to recent output paths list.
        
        Args:
            path: Output file path
            max_recent: Maximum number of recent paths to keep
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            recent_paths = self.get_recent_output_paths()
            
            # Remove if already exists
            if path in recent_paths:
                recent_paths.remove(path)
            
            # Add to beginning
            recent_paths.insert(0, path)
            
            # Limit to max_recent
            recent_paths = recent_paths[:max_recent]
            
            self.settings.setValue(self.KEYS['recent_outputs'], json.dumps(recent_paths))
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error adding recent output path: {e}")
            return False
    
    def get_recent_output_paths(self, validate_paths: bool = True) -> List[str]:
        """
        Get list of recent output paths.
        
        Args:
            validate_paths: Whether to validate that paths still exist
        
        Returns:
            List of recent output file paths
        """
        try:
            paths_json = self.settings.value(self.KEYS['recent_outputs'])
            if paths_json:
                paths = json.loads(paths_json)
                if validate_paths:
                    # Validate paths still exist
                    valid_paths = []
                    for path in paths:
                        if os.path.exists(os.path.dirname(path)):
                            valid_paths.append(path)
                    return valid_paths
                else:
                    return paths
        except Exception as e:
            print(f"Error loading recent output paths: {e}")
        
        return []
    
    def save_ui_settings(self, ui_settings: Dict[str, Any]) -> bool:
        """
        Save UI-related settings.
        
        Args:
            ui_settings: Dictionary of UI settings
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.settings.setValue(self.KEYS['ui_settings'], json.dumps(ui_settings))
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error saving UI settings: {e}")
            return False
    
    def load_ui_settings(self) -> Dict[str, Any]:
        """
        Load UI-related settings.
        
        Returns:
            Dictionary of UI settings with defaults
        """
        try:
            ui_json = self.settings.value(self.KEYS['ui_settings'])
            if ui_json:
                return json.loads(ui_json)
        except Exception as e:
            print(f"Error loading UI settings: {e}")
        
        # Return default UI settings
        return {
            'window_geometry': None,
            'splitter_state': None,
            'column_widths': {},
            'last_directory': '',
            'dialog_sizes': {},
        }
    
    def save_layer_preferences(self, layer_preferences: Dict[str, Any]) -> bool:
        """
        Save layer-related preferences.
        
        Args:
            layer_preferences: Dictionary of layer preferences
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.settings.setValue(self.KEYS['layer_preferences'], json.dumps(layer_preferences))
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error saving layer preferences: {e}")
            return False
    
    def load_layer_preferences(self) -> Dict[str, Any]:
        """
        Load layer-related preferences.
        
        Returns:
            Dictionary of layer preferences with defaults
        """
        try:
            prefs_json = self.settings.value(self.KEYS['layer_preferences'])
            if prefs_json:
                return json.loads(prefs_json)
        except Exception as e:
            print(f"Error loading layer preferences: {e}")
        
        # Return default layer preferences
        return {
            'remember_layer_selections': True,
            'auto_detect_geometry_type': True,
            'show_layer_preview': True,
            'max_preview_features': 5,
            'preferred_pipe_layers': [],
            'preferred_junction_layers': [],
        }
    
    def clear_all_settings(self) -> bool:
        """
        Clear all plugin settings.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            self.settings.clear()
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error clearing settings: {e}")
            return False
    
    def export_settings_to_file(self, file_path: str) -> bool:
        """
        Export all settings to a JSON file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            all_settings = {}
            
            # Export all setting groups
            for key_name, key_path in self.KEYS.items():
                value = self.settings.value(key_path)
                if value:
                    try:
                        # Try to parse as JSON first
                        all_settings[key_name] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # Store as string if not JSON
                        all_settings[key_name] = value
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_settings, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False
    
    def import_settings_from_file(self, file_path: str) -> bool:
        """
        Import settings from a JSON file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                all_settings = json.load(f)
            
            # Import all setting groups
            for key_name, value in all_settings.items():
                if key_name in self.KEYS:
                    key_path = self.KEYS[key_name]
                    if isinstance(value, (dict, list)):
                        self.settings.setValue(key_path, json.dumps(value))
                    else:
                        self.settings.setValue(key_path, value)
            
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False
    
    def _export_config_to_dict(self, config: ExportConfiguration) -> Dict[str, Any]:
        """
        Convert ExportConfiguration to dictionary for JSON serialization.
        
        Args:
            config: ExportConfiguration to convert
            
        Returns:
            Dictionary representation
        """
        config_dict = {
            'output_path': config.output_path,
            'scale_factor': config.scale_factor,
            'layer_prefix': config.layer_prefix,
            'template_path': config.template_path,
            'include_arrows': config.include_arrows,
            'include_labels': config.include_labels,
            'include_elevations': config.include_elevations,
            'label_format': config.label_format,
        }
        
        # Always include pipes_mapping and junctions_mapping, even if None
        if config.pipes_mapping:
            config_dict['pipes_mapping'] = self._layer_mapping_to_dict(config.pipes_mapping)
        else:
            config_dict['pipes_mapping'] = None
        
        if config.junctions_mapping:
            config_dict['junctions_mapping'] = self._layer_mapping_to_dict(config.junctions_mapping)
        else:
            config_dict['junctions_mapping'] = None
        
        return config_dict
    
    def _dict_to_export_config(self, config_dict: Dict[str, Any]) -> ExportConfiguration:
        """
        Convert dictionary to ExportConfiguration.
        
        Args:
            config_dict: Dictionary representation
            
        Returns:
            ExportConfiguration object
        """
        print(f"DEBUG: _dict_to_export_config called with config_dict type: {type(config_dict)}")
        print(f"DEBUG: config_dict keys: {list(config_dict.keys()) if isinstance(config_dict, dict) else 'NOT A DICT'}")
        
        config = ExportConfiguration(
            output_path=config_dict.get('output_path', ''),
            scale_factor=config_dict.get('scale_factor', 2000),
            layer_prefix=config_dict.get('layer_prefix', 'ESG_'),
            template_path=config_dict.get('template_path'),
            include_arrows=config_dict.get('include_arrows', True),
            include_labels=config_dict.get('include_labels', True),
            include_elevations=config_dict.get('include_elevations', True),
            label_format=config_dict.get('label_format', '{length:.0f}-{diameter:.0f}-{slope:.5f}'),
        )
        
        if 'pipes_mapping' in config_dict and config_dict['pipes_mapping'] is not None:
            print(f"DEBUG: Processing pipes_mapping, type: {type(config_dict['pipes_mapping'])}")
            print(f"DEBUG: pipes_mapping content: {config_dict['pipes_mapping']}")
            config.pipes_mapping = self._dict_to_layer_mapping(config_dict['pipes_mapping'])
        else:
            print(f"DEBUG: pipes_mapping is None or not present")
            config.pipes_mapping = None
        
        if 'junctions_mapping' in config_dict and config_dict['junctions_mapping'] is not None:
            print(f"DEBUG: Processing junctions_mapping, type: {type(config_dict['junctions_mapping'])}")
            print(f"DEBUG: junctions_mapping content: {config_dict['junctions_mapping']}")
            config.junctions_mapping = self._dict_to_layer_mapping(config_dict['junctions_mapping'])
        else:
            print(f"DEBUG: junctions_mapping is None or not present")
            config.junctions_mapping = None
        
        return config
    
    def _layer_mapping_to_dict(self, mapping: LayerMapping) -> Dict[str, Any]:
        """
        Convert LayerMapping to dictionary for JSON serialization.
        
        Args:
            mapping: LayerMapping to convert
            
        Returns:
            Dictionary representation
        """
        return {
            'layer_id': mapping.layer_id,
            'layer_name': mapping.layer_name,
            'geometry_type': mapping.geometry_type.value,
            'field_mappings': mapping.field_mappings,
            'default_values': mapping.default_values,
            'calculated_fields': mapping.calculated_fields,
            'is_valid': mapping.is_valid,
            'validation_errors': mapping.validation_errors if mapping.validation_errors is not None else [],
            'auto_mapped_fields': mapping.auto_mapped_fields,
        }
    
    def _dict_to_layer_mapping(self, mapping_dict: Dict[str, Any]) -> LayerMapping:
        """
        Convert dictionary to LayerMapping.
        
        Args:
            mapping_dict: Dictionary representation
            
        Returns:
            LayerMapping object
        """
        print(f"DEBUG: _dict_to_layer_mapping called with mapping_dict type: {type(mapping_dict)}")
        print(f"DEBUG: mapping_dict content: {mapping_dict}")
        
        # Safely extract dictionary fields with validation
        def safe_get_dict(key: str, default: dict = None) -> dict:
            if default is None:
                default = {}
            value = mapping_dict.get(key, default)
            print(f"DEBUG: safe_get_dict for key '{key}': type={type(value)}, value={value}")
            # Ensure the value is actually a dictionary
            if not isinstance(value, dict):
                print(f"WARNING: {key} is not a dictionary, using empty dict. Got: {type(value)}")
                return {}
            return value
        
        def safe_get_list(key: str, default: list = None) -> list:
            if default is None:
                default = []
            value = mapping_dict.get(key, default)
            print(f"DEBUG: safe_get_list for key '{key}': type={type(value)}, value={value}")
            # Ensure the value is actually a list
            if not isinstance(value, list):
                print(f"WARNING: {key} is not a list, using empty list. Got: {type(value)}")
                return []
            return value
        
        print("DEBUG: About to create LayerMapping object...")
        try:
            result = LayerMapping(
                layer_id=mapping_dict.get('layer_id', ''),
                layer_name=mapping_dict.get('layer_name', ''),
                geometry_type=GeometryType(mapping_dict.get('geometry_type', GeometryType.LINE.value)),
                field_mappings=safe_get_dict('field_mappings'),
                default_values=safe_get_dict('default_values'),
                calculated_fields=safe_get_dict('calculated_fields'),
                is_valid=mapping_dict.get('is_valid', False),
                validation_errors=safe_get_list('validation_errors'),
                auto_mapped_fields=safe_get_dict('auto_mapped_fields'),
            )
            print("DEBUG: LayerMapping created successfully")
            return result
        except Exception as e:
            print(f"DEBUG: Error creating LayerMapping: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            raise
    
    @property
    def current_config(self) -> Optional[ExportConfiguration]:
        """Get the current export configuration."""
        return self._current_config
    
    @current_config.setter
    def current_config(self, config: Optional[ExportConfiguration]):
        """Set the current export configuration."""
        self._current_config = config
        
        # Auto-save if enabled
        user_prefs = self.load_user_preferences()
        if user_prefs.get('auto_save_config', True) and config:
            self.save_export_configuration(config, "last")
    
    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """
        Get a simple setting value.
        
        Args:
            key: Setting key
            default_value: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        return self.settings.value(key, default_value)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a simple setting value.
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            self.settings.setValue(key, value)
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def get_pipes_mapping(self) -> Optional[LayerMapping]:
        """
        Get the pipes mapping from the current configuration.
        
        Returns:
            LayerMapping for pipes or None if not available
        """
        if self._current_config and self._current_config.pipes_mapping:
            return self._current_config.pipes_mapping
        return None
    
    def get_junctions_mapping(self) -> Optional[LayerMapping]:
        """
        Get the junctions mapping from the current configuration.
        
        Returns:
            LayerMapping for junctions or None if not available
        """
        if self._current_config and self._current_config.junctions_mapping:
            return self._current_config.junctions_mapping
        return None