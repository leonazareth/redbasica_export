#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the Configuration management system.

This script demonstrates how to use the Configuration class to manage
plugin settings, export configurations, and user preferences.
"""

import sys
import os

# Add the core directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.configuration import Configuration
from core.data_structures import ExportConfiguration, LayerMapping, GeometryType


def main():
    """Demonstrate configuration management functionality."""
    
    print("=== RedBasica Export Configuration Management Demo ===\n")
    
    # Initialize configuration manager
    config_manager = Configuration("RedBasica", "ExportDemo")
    
    # 1. User Preferences Management
    print("1. Managing User Preferences:")
    
    # Set some user preferences
    user_prefs = {
        'default_scale_factor': 1000,
        'default_layer_prefix': 'DEMO_',
        'include_arrows_default': False,
        'include_labels_default': True,
        'auto_save_config': True,
        'show_validation_warnings': True
    }
    
    # Save preferences
    if config_manager.save_user_preferences(user_prefs):
        print("✓ User preferences saved successfully")
    else:
        print("✗ Failed to save user preferences")
    
    # Load preferences
    loaded_prefs = config_manager.load_user_preferences()
    print(f"✓ Loaded preferences: scale_factor={loaded_prefs['default_scale_factor']}, "
          f"prefix='{loaded_prefs['default_layer_prefix']}'")
    
    # 2. Template Path Management
    print("\n2. Managing Template Paths:")
    
    # Create a dummy template file for demonstration
    demo_template_path = "demo_template.dxf"
    with open(demo_template_path, 'w') as f:
        f.write("Demo DXF template content")
    
    # Add template path
    if config_manager.add_template_path("demo_template", demo_template_path):
        print("✓ Template path added successfully")
    else:
        print("✗ Failed to add template path")
    
    # Load template paths
    template_paths = config_manager.load_template_paths()
    print(f"✓ Available templates: {list(template_paths.keys())}")
    
    # 3. Field Mappings Management
    print("\n3. Managing Field Mappings:")
    
    # Define field mappings for a layer
    layer_id = "demo_pipes_layer_123"
    field_mappings = {
        "pipe_id": "DC_ID",
        "length": "LENGTH", 
        "diameter": "DIAMETER",
        "upstream_node": "PVM",
        "downstream_node": "PVJ",
        "upstream_invert": "CCM",
        "downstream_invert": "CCJ"
    }
    
    # Save field mappings
    if config_manager.save_field_mappings(layer_id, field_mappings):
        print("✓ Field mappings saved successfully")
    else:
        print("✗ Failed to save field mappings")
    
    # Load field mappings
    loaded_mappings = config_manager.load_field_mappings(layer_id)
    print(f"✓ Loaded {len(loaded_mappings)} field mappings for layer")
    
    # 4. Export Configuration Management
    print("\n4. Managing Export Configurations:")
    
    # Create a sample layer mapping
    pipes_mapping = LayerMapping(
        layer_id=layer_id,
        layer_name="Demo Pipes Layer",
        geometry_type=GeometryType.LINE,
        field_mappings=field_mappings,
        default_values={
            "material": "PVC",
            "slope": 0.001
        },
        is_valid=True
    )
    
    # Create export configuration
    export_config = ExportConfiguration(
        pipes_mapping=pipes_mapping,
        output_path="demo_output.dxf",
        scale_factor=1000,
        layer_prefix="DEMO_",
        template_path=demo_template_path,
        include_arrows=False,
        include_labels=True,
        include_elevations=True,
        label_format="{length:.1f}m-D{diameter:.0f}-S{slope:.4f}"
    )
    
    # Save export configuration
    if config_manager.save_export_configuration(export_config, "demo_config"):
        print("✓ Export configuration saved successfully")
    else:
        print("✗ Failed to save export configuration")
    
    # Load export configuration
    loaded_config = config_manager.load_export_configuration("demo_config")
    if loaded_config:
        print(f"✓ Loaded export config: output='{loaded_config.output_path}', "
              f"scale={loaded_config.scale_factor}")
        print(f"  Validation: {'✓ Valid' if loaded_config.is_valid() else '✗ Invalid'}")
    else:
        print("✗ Failed to load export configuration")
    
    # 5. Recent Output Paths
    print("\n5. Managing Recent Output Paths:")
    
    # Add some recent paths
    recent_paths = [
        "C:/exports/project1.dxf",
        "C:/exports/project2.dxf", 
        "C:/exports/project3.dxf"
    ]
    
    for path in recent_paths:
        config_manager.add_recent_output_path(path)
    
    # Get recent paths
    loaded_recent = config_manager.get_recent_output_paths(validate_paths=False)
    print(f"✓ Recent output paths ({len(loaded_recent)} total):")
    for i, path in enumerate(loaded_recent[:3], 1):
        print(f"  {i}. {path}")
    
    # 6. UI Settings
    print("\n6. Managing UI Settings:")
    
    ui_settings = {
        'window_geometry': 'demo_geometry_data',
        'splitter_state': 'demo_splitter_state',
        'column_widths': {'field_name': 150, 'layer_field': 200, 'default_value': 100},
        'last_directory': 'C:/demo/exports',
        'dialog_sizes': {'main_dialog': (800, 600), 'mapper_dialog': (600, 400)}
    }
    
    if config_manager.save_ui_settings(ui_settings):
        print("✓ UI settings saved successfully")
    
    loaded_ui = config_manager.load_ui_settings()
    print(f"✓ Loaded UI settings: last_directory='{loaded_ui['last_directory']}'")
    
    # 7. Configuration Export/Import
    print("\n7. Configuration Export/Import:")
    
    export_file = "demo_settings_export.json"
    
    # Export all settings
    if config_manager.export_settings_to_file(export_file):
        print(f"✓ Settings exported to '{export_file}'")
        
        # Show file size
        file_size = os.path.getsize(export_file)
        print(f"  Export file size: {file_size} bytes")
    else:
        print("✗ Failed to export settings")
    
    # 8. Configuration Names Management
    print("\n8. Saved Configuration Management:")
    
    # Save multiple configurations
    config_names = ["demo_config", "test_config", "backup_config"]
    for name in config_names[1:]:  # Skip first one as it's already saved
        config_manager.save_export_configuration(export_config, name)
    
    # List saved configurations
    saved_configs = config_manager.get_saved_configuration_names()
    print(f"✓ Saved configurations: {saved_configs}")
    
    # Delete a configuration
    if config_manager.delete_saved_configuration("test_config"):
        print("✓ Deleted 'test_config' configuration")
    
    # List again to confirm deletion
    saved_configs = config_manager.get_saved_configuration_names()
    print(f"✓ Remaining configurations: {saved_configs}")
    
    # 9. Validation Examples
    print("\n9. Configuration Validation:")
    
    # Valid configuration
    if export_config.is_valid():
        print("✓ Export configuration is valid")
    else:
        errors = export_config.get_validation_errors()
        print(f"✗ Export configuration has errors: {errors}")
    
    # Invalid configuration example
    invalid_config = ExportConfiguration(
        pipes_mapping=None,  # Missing required mapping
        output_path="",      # Empty output path
        scale_factor=-100    # Invalid scale factor
    )
    
    if not invalid_config.is_valid():
        errors = invalid_config.get_validation_errors()
        print(f"✓ Invalid configuration correctly identified {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n=== Configuration Management Demo Complete ===")
    
    # Cleanup demo files
    try:
        os.remove(demo_template_path)
        os.remove(export_file)
        print("\n✓ Demo files cleaned up")
    except OSError:
        pass


if __name__ == "__main__":
    main()