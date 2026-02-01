"""
Flexible DXF export engine for sewerage network data.

This module provides the core DXF export functionality that works with ANY
user-selected layers and field mappings, maintaining QEsg-compatible output
while providing maximum flexibility for different data structures.
"""

import os
import sys
import math
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Add addon directory to path for bundled libraries
addon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'addon')
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    from ezdxf import units
except ImportError as e:
    raise ImportError(f"Failed to import bundled ezdxf library: {e}")

from qgis.core import QgsVectorLayer, QgsFeature, QgsProject, QgsMessageLog, Qgis
from .data_structures import ExportConfiguration, LayerMapping, GeometryType, FieldType
from .field_definitions import SewageNetworkFields
from .template_manager import TemplateManager
from .geometry_processor import GeometryProcessor
from .data_converter import DataConverter
from .exceptions import ExportError, GeometryError, TemplateError, FilePermissionError
from .error_recovery import ErrorRecoveryManager, ProgressTracker, ErrorSeverity, create_error_recovery_context, handle_feature_processing_error
from .file_utils import validate_and_prepare_output_path
from .error_messages import create_error_formatter


class DXFExporter:
    """
    Core DXF export engine with flexible layer and field mapping support.
    
    Exports sewerage network data to DXF format using user-configured layer
    and field mappings while maintaining QEsg-compatible output structure.
    """
    
    # === CAD STYLING CONSTANTS ===
    # Font
    CAD_FONT = "SIMPLEX"  # Sans-serif CAD font
    
    # Colors (RGB tuples)
    COLOR_ARROW = (152, 152, 152)      # Gray #989898
    COLOR_PIPE = (166, 166, 255)       # Light blue #a6a6ff
    COLOR_PIPE_NAME = (255, 97, 0)     # Orange #ff6100
    COLOR_DEPTH_LENGTH = (140, 140, 140)  # Darker Gray #8c8c8c
    COLOR_DEPTH_LENGTH = (140, 140, 140)  # Darker Gray #8c8c8c
    COLOR_WHITE = (255, 255, 255)      # White for other labels
    COLOR_RED = (255, 0, 0)            # Red for Tubo de Queda (TC)
    COLOR_BLUE = (0, 0, 255)           # Blue for Degrau (D)
    
    # Dimensions
    DROP_CIRCLE_RADIUS = 1.0           # Base radius for drop markers (scaled by config)
    
    @staticmethod
    def rgb_to_int(rgb_tuple):
        """Convert RGB tuple (r, g, b) to 24-bit integer for DXF true_color."""
        r, g, b = rgb_tuple
        return (r << 16) | (g << 8) | b
    
    @staticmethod
    def format_mtext_color_rgb(rgb_tuple):
        """Return MTEXT formatting code for closest ACI Color (R12 compatible): \C<index>;"""
        # Convert RGB to closest ACI index for R12 compatibility
        aci = DXFExporter.get_aci_color(rgb_tuple)
        return f"\\C{aci};"

    @staticmethod
    def format_mtext_color_aci(aci_index):
        """Return MTEXT formatting code for ACI Color: \C7;"""
        return f"\\C{aci_index};"
        
    @staticmethod
    def get_aci_color(rgb_tuple):
        """Get closest ACI color index from RGB tuple using Euclidean distance."""
        try:
            return ezdxf.colors.rgb2aci(rgb_tuple)
        except AttributeError:
            # Fallback for older ezdxf versions
            r, g, b = rgb_tuple
            
            # Standard Colors
            if r == 255 and g == 0 and b == 0: return 1 # Red
            if r == 255 and g == 255 and b == 0: return 2 # Yellow
            if r == 0 and g == 255 and b == 0: return 3 # Green
            if r == 0 and g == 255 and b == 255: return 4 # Cyan
            if r == 0 and g == 0 and b == 255: return 5 # Blue
            if r == 255 and g == 0 and b == 255: return 6 # Magenta
            if r == 255 and g == 255 and b == 255: return 7 # White
            
            # Manual mapping for our specific colors
            if rgb_tuple == (152, 152, 152): return 8   # Dark Gray (Arrow)
            if rgb_tuple == (140, 140, 140): return 252 # Darker Gray (Depth) - ACI 252
            if rgb_tuple == (255, 97, 0): return 30     # Orange (Pipe Name)
            
            # Simple approximation for grays
            if r == g == b:
                if r < 30: return 250
                if r > 240: return 255
                return 250 + int((r - 30) / 42) # Maps to 250-255 range partially
                
            return 7 # Default to white/adaptive if unknown
    
    def __init__(self, template_manager: TemplateManager = None, 
                 progress_callback: Optional[callable] = None):
        """
        Initialize DXF exporter.
        
        Args:
            template_manager: Template manager instance (creates default if None)
            progress_callback: Optional callback for progress updates
        """
        self.template_manager = template_manager or TemplateManager()
        self.progress_callback = progress_callback
        self.error_manager = ErrorRecoveryManager()
        self.error_formatter = create_error_formatter()
        self.geometry_processor = GeometryProcessor()
        self.data_converter = DataConverter()
        self.geometry_processor = GeometryProcessor()
        self.data_converter = DataConverter()
        
        # Export statistics
        self.stats = {
            'pipes_exported': 0,
            'junctions_exported': 0,
            'pipes_skipped': 0,
            'junctions_skipped': 0,
            'errors': []
        }
    
    def export_to_dxf(self, config: ExportConfiguration) -> Tuple[bool, str, Dict]:
        """
        Export sewerage network to DXF file.
        
        Args:
            config: Complete export configuration
            
        Returns:
            (success, message, statistics) tuple
        """
        try:
            # Reset statistics
            self._reset_stats()
            
            # Validate configuration
            if not config.is_valid():
                errors = config.get_validation_errors()
                return False, f"Configuration invalid: {'; '.join(errors)}", self.stats
            
            # DEBUG: Trace Config via QGIS Message Log
            QgsMessageLog.logMessage(f"DEBUG EXPORT: config.export_mode = {config.export_mode}", 'RedBasicaExport', Qgis.Info)
            try:
                QgsMessageLog.logMessage(f"DEBUG EXPORT: config.export_mode name = {config.export_mode.name}", 'RedBasicaExport', Qgis.Info)
            except:
                pass
            
            # Load or create DXF document
            doc = self.template_manager.load_template(config.template_path)
            
            # Set up document properties
            self.template_manager.setup_document_properties(doc)
            
            # Create layers with prefix
            self.template_manager.create_layers_with_prefix(doc, config.layer_prefix)
            
            # Get model space
            msp = doc.modelspace()
            
            # Export pipes
            if config.pipes_mapping:
                success = self._export_pipes(doc, msp, config)
                if not success:
                    return False, "Failed to export pipes", self.stats
            
            # Export junctions
            if config.junctions_mapping:
                success = self._export_junctions(doc, msp, config)
                if not success:
                    return False, "Failed to export junctions", self.stats
            
            # Save DXF file
            doc.saveas(config.output_path)
            
            # Generate success message
            message = self._generate_success_message(config.output_path)
            
            return True, message, self.stats
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            return False, error_msg, self.stats
    
    def _export_pipes(self, doc: ezdxf.document.Drawing, msp, config: ExportConfiguration) -> bool:
        """
        Export pipe features to DXF.
        
        Args:
            doc: ezdxf Drawing document
            msp: Model space
            config: Export configuration
            
        Returns:
            True if successful
        """
        try:
            from .data_structures import ExportMode
            from .utils.geometry_utils import (
                get_cad_angle, get_readable_rotation, 
                get_perpendicular_offset_point, clamp
            )
            from qgis.core import QgsPointXY


            # Get pipes layer
            pipes_layer = self._get_layer_by_id(config.pipes_mapping.layer_id)
            if not pipes_layer:
                self.stats['errors'].append(f"Pipes layer not found: {config.pipes_mapping.layer_id}")
                return False
            
            # Get layer names
            pipes_layer_name = self.template_manager.get_layer_name('REDE', config.layer_prefix)
            labels_layer_name = self.template_manager.get_layer_name('NUMERO', config.layer_prefix)
            text_layer_name = self.template_manager.get_layer_name('LEG_REDE', config.layer_prefix)
            arrows_layer_name = self.template_manager.get_layer_name('SETA_FLUXO', config.layer_prefix)
            
            # Process each pipe feature
            for feature in pipes_layer.getFeatures():
                try:
                    # Extract feature data using mappings
                    pipe_data = self._extract_pipe_data(feature, config.pipes_mapping)
                    if not pipe_data:
                        self.stats['pipes_skipped'] += 1
                        continue
                    
                    # Get geometry coordinates
                    geometry = feature.geometry()
                    coordinates = self.geometry_processor.extract_line_coordinates(geometry)
                    if len(coordinates) < 2:
                        self.stats['pipes_skipped'] += 1
                        continue
                    
                    start_point = coordinates[0]
                    end_point = coordinates[-1]
                    
                    # Add pipe line with elevation data
                    # Add pipe line with elevation data
                    self._add_pipe_line(msp, start_point, end_point, pipe_data, pipes_layer_name)
                    
                    # --- LABELING LOGIC ---
                    if config.include_labels:
                        if config.export_mode.name == 'STANDARD':
                            # Legacy TEXT entities
                            if pipe_data.get('pipe_id'):
                                self._add_pipe_id_label(msp, start_point, end_point, pipe_data, 
                                                      labels_layer_name, config.scale_factor)
                            
                            self._add_pipe_data_label(msp, start_point, end_point, pipe_data, 
                                                    text_layer_name, config.scale_factor, config.label_format)
                        else:
                            # Enhanced MTEXT entity
                            # Convert tuples to QgsPointXY for helper
                            p1 = QgsPointXY(start_point[0], start_point[1])
                            p2 = QgsPointXY(end_point[0], end_point[1])
                            self._add_enhanced_pipe_label(
                                msp, p1, p2, pipe_data, 
                                text_layer_name, config.scale_factor, config
                            )

                    
                    # Add flow arrow
                    if config.include_arrows:
                        self._add_flow_arrow(msp, start_point, end_point, arrows_layer_name, config.scale_factor)
                        
                    # Add Drop / Drop Pipe marker if present
                    self._add_drop_marker(msp, start_point, end_point, pipe_data, arrows_layer_name, config.scale_factor)
                    
                    # Add Collector Depth Label (h_col_p2) if enabled
                    if config.include_collector_depth:
                        self._add_collector_depth_label(msp, start_point, end_point, pipe_data, text_layer_name, config.scale_factor)
                    
                    # Add extended entity data (XDATA)
                    self._add_pipe_xdata(msp, pipe_data)
                    
                    self.stats['pipes_exported'] += 1
                    
                except Exception as e:
                    self.stats['pipes_skipped'] += 1
                    self.stats['errors'].append(f"Error processing pipe feature: {str(e)}")
            
            return True
            
        except Exception as e:
            self.stats['errors'].append(f"Error exporting pipes: {str(e)}")
            return False
    
    def _export_junctions(self, doc: ezdxf.document.Drawing, msp, config: ExportConfiguration) -> bool:
        """
        Export junction features to DXF.
        
        Args:
            doc: ezdxf Drawing document
            msp: Model space
            config: Export configuration
            
        Returns:
            True if successful
        """
        try:
            from .data_structures import ExportMode
            from qgis.core import QgsPointXY
            
            # Get junctions layer
            junctions_layer = self._get_layer_by_id(config.junctions_mapping.layer_id)
            if not junctions_layer:
                self.stats['errors'].append(f"Junctions layer not found: {config.junctions_mapping.layer_id}")
                return False
            
            # Get layer names
            junctions_layer_name = self.template_manager.get_layer_name('PV', config.layer_prefix)
            labels_layer_name = self.template_manager.get_layer_name('NUMPV', config.layer_prefix)
            elevation_layer_name = self.template_manager.get_layer_name('LEG_PV', config.layer_prefix)
            
            # Process each junction feature
            for feature in junctions_layer.getFeatures():
                try:
                    # Extract feature data using mappings
                    junction_data = self._extract_junction_data(feature, config.junctions_mapping)
                    if not junction_data:
                        self.stats['junctions_skipped'] += 1
                        continue
                    
                    # Get geometry coordinates
                    geometry = feature.geometry()
                    coordinates = self.geometry_processor.extract_point_coordinates(geometry)
                    if not coordinates:
                        self.stats['junctions_skipped'] += 1
                        continue
                    
                    # Add junction symbol (circle)
                    self._add_junction_symbol(msp, coordinates, junction_data, junctions_layer_name, config.scale_factor)
                    
                    # --- LABELING LOGIC ---
                    if config.export_mode.name == 'STANDARD':
                        # Legacy TEXT/BLOCK labels
                        if junction_data.get('node_id'):
                            self._add_junction_id_label(msp, coordinates, junction_data, 
                                                       labels_layer_name, config.scale_factor)
                        
                        if config.include_elevations and (junction_data.get('ground_elevation') or junction_data.get('invert_elevation')):
                            self._add_elevation_block(msp, coordinates, junction_data, 
                                                    elevation_layer_name, config.scale_factor)
                    else:
                        # Enhanced MULTILEADER entity
                        if config.include_elevations or junction_data.get('node_id'):
                            point_xy = QgsPointXY(coordinates[0], coordinates[1])
                            self._add_multileader_node_label(
                                msp, point_xy, junction_data, 
                                elevation_layer_name, config.scale_factor,
                                export_node_id=config.export_node_id
                            )

                    
                    # Add extended entity data (XDATA)
                    self._add_junction_xdata(msp, junction_data)
                    
                    self.stats['junctions_exported'] += 1
                    
                except Exception as e:
                    self.stats['junctions_skipped'] += 1
                    self.stats['errors'].append(f"Error processing junction feature: {str(e)}")
            
            return True
            
        except Exception as e:
            self.stats['errors'].append(f"Error exporting junctions: {str(e)}")
            return False
    
    def _extract_pipe_data(self, feature: QgsFeature, mapping: LayerMapping) -> Optional[Dict[str, Any]]:
        """
        Extract pipe data from feature using field mappings.
        
        Args:
            feature: QGIS feature
            mapping: Layer mapping configuration
            
        Returns:
            Dictionary of pipe data or None if extraction fails
        """
        try:
            pipe_data = {}
            
            # Extract mapped fields
            print(f"DEBUG: About to iterate over field_mappings in _extract_pipe_data")
            print(f"DEBUG: mapping.field_mappings type: {type(mapping.field_mappings)}")
            print(f"DEBUG: mapping.field_mappings: {mapping.field_mappings}")
            print(f"DEBUG: mapping.field_mappings.items() type: {type(mapping.field_mappings.items())}")
            
            try:
                # Ensure field_mappings is actually a dictionary
                if not isinstance(mapping.field_mappings, dict):
                    print(f"ERROR: field_mappings is not a dict: {type(mapping.field_mappings)}")
                    # Try to convert if it's a proper dictionary-like sequence
                    if hasattr(mapping.field_mappings, 'items'):
                        mapping.field_mappings = dict(mapping.field_mappings)
                        print(f"DEBUG: Converted field_mappings to dict: {mapping.field_mappings}")
                    else:
                        # Fallback: create empty dict if completely invalid
                        mapping.field_mappings = {}
                        print(f"DEBUG: Fallback: created empty field_mappings dict")
                
                items_list = list(mapping.field_mappings.items())
                print(f"DEBUG: items_list: {items_list}")
                print(f"DEBUG: items_list length: {len(items_list)}")
                if items_list:
                    print(f"DEBUG: first item: {items_list[0]}")
                    print(f"DEBUG: first item type: {type(items_list[0])}")
            except Exception as e:
                print(f"DEBUG: Error converting items to list: {e}")
            
            for required_field, layer_field in mapping.field_mappings.items():
                if layer_field in feature.fields().names():
                    raw_value = feature[layer_field]
                    # Convert value based on field type
                    field_def = SewageNetworkFields.get_field_by_name(required_field)
                    if field_def:
                        converted_value = self.data_converter.convert_value(raw_value, field_def.field_type)
                        pipe_data[required_field] = converted_value
            
            # Add default values for unmapped fields
            if isinstance(mapping.default_values, dict):
                for required_field, default_value in mapping.default_values.items():
                    if required_field not in pipe_data:
                        pipe_data[required_field] = default_value
            
            # Calculate derived fields
            pipe_data = self._calculate_pipe_fields(pipe_data)
            
            # Validate required fields
            required_fields = SewageNetworkFields.get_required_pipe_fields()
            for field_name in required_fields:
                if field_name not in pipe_data or pipe_data[field_name] is None:
                    # Use field default if available
                    field_def = SewageNetworkFields.get_field_by_name(field_name)
                    if field_def and field_def.default_value is not None:
                        pipe_data[field_name] = field_def.default_value
                    else:
                        return None  # Skip feature if required field missing
            
            return pipe_data
            
        except Exception as e:
            self.stats['errors'].append(f"Error extracting pipe data: {str(e)}")
            return None
    
    def _extract_junction_data(self, feature: QgsFeature, mapping: LayerMapping) -> Optional[Dict[str, Any]]:
        """
        Extract junction data from feature using field mappings.
        
        Args:
            feature: QGIS feature
            mapping: Layer mapping configuration
            
        Returns:
            Dictionary of junction data or None if extraction fails
        """
        try:
            junction_data = {}
            
            # Extract mapped fields
            # Ensure field_mappings is actually a dictionary
            if not isinstance(mapping.field_mappings, dict):
                print(f"ERROR: junction field_mappings is not a dict: {type(mapping.field_mappings)}")
                if hasattr(mapping.field_mappings, 'items'):
                    mapping.field_mappings = dict(mapping.field_mappings)
                else:
                    mapping.field_mappings = {}
            
            for required_field, layer_field in mapping.field_mappings.items():
                if layer_field in feature.fields().names():
                    raw_value = feature[layer_field]
                    # Convert value based on field type
                    field_def = SewageNetworkFields.get_field_by_name(required_field)
                    if field_def:
                        converted_value = self.data_converter.convert_value(raw_value, field_def.field_type)
                        junction_data[required_field] = converted_value
            
            # Add default values for unmapped fields
            if isinstance(mapping.default_values, dict):
                for required_field, default_value in mapping.default_values.items():
                    if required_field not in junction_data:
                        junction_data[required_field] = default_value
            
            # Calculate derived fields
            junction_data = self._calculate_junction_fields(junction_data)
            
            # Validate required fields
            required_fields = SewageNetworkFields.get_required_junction_fields()
            for field_name in required_fields:
                if field_name not in junction_data or junction_data[field_name] is None:
                    # Use field default if available
                    field_def = SewageNetworkFields.get_field_by_name(field_name)
                    if field_def and field_def.default_value is not None:
                        junction_data[field_name] = field_def.default_value
                    else:
                        return None  # Skip feature if required field missing
            
            return junction_data
            
        except Exception as e:
            self.stats['errors'].append(f"Error extracting junction data: {str(e)}")
            return None
    
    def _calculate_pipe_fields(self, pipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate derived fields for pipes.
        
        Args:
            pipe_data: Pipe data dictionary
            
        Returns:
            Updated pipe data with calculated fields
        """
        # Calculate slope if not provided
        if ('slope' not in pipe_data or pipe_data['slope'] == 0) and all(
            field in pipe_data for field in ['upstream_invert_elev', 'downstream_invert_elev', 'length']
        ):
            try:
                upstream_invert = float(pipe_data['upstream_invert_elev'])
                downstream_invert = float(pipe_data['downstream_invert_elev'])
                length = float(pipe_data['length'])
                
                if length > 0:
                    calculated_slope = (upstream_invert - downstream_invert) / length
                    pipe_data['calculated_slope'] = calculated_slope
                    if 'slope' not in pipe_data:
                        pipe_data['slope'] = calculated_slope
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        # Calculate depths if ground elevations available
        if all(field in pipe_data for field in ['upstream_ground_elev', 'upstream_invert_elev']):
            try:
                upstream_depth = float(pipe_data['upstream_ground_elev']) - float(pipe_data['upstream_invert_elev'])
                pipe_data['upstream_depth'] = max(0, upstream_depth)
            except (ValueError, TypeError):
                pass
        
        if all(field in pipe_data for field in ['downstream_ground_elev', 'downstream_invert_elev']):
            try:
                downstream_depth = float(pipe_data['downstream_ground_elev']) - float(pipe_data['downstream_invert_elev'])
                pipe_data['downstream_depth'] = max(0, downstream_depth)
            except (ValueError, TypeError):
                pass
        
        return pipe_data
    
    def _calculate_junction_fields(self, junction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate derived fields for junctions.
        
        Args:
            junction_data: Junction data dictionary
            
        Returns:
            Updated junction data with calculated fields
        """
        # Calculate depth if ground and invert elevations available
        if all(field in junction_data for field in ['ground_elevation', 'invert_elevation']):
            try:
                depth = float(junction_data['ground_elevation']) - float(junction_data['invert_elevation'])
                junction_data['junction_depth'] = max(0, depth)
                if 'depth' not in junction_data:
                    junction_data['depth'] = junction_data['junction_depth']
            except (ValueError, TypeError):
                pass
        
        return junction_data 
   
    def _add_pipe_line(self, msp, start_point: Tuple[float, float], end_point: Tuple[float, float], 
                      pipe_data: Dict[str, Any], layer_name: str) -> None:
        """
        Add pipe line to DXF with elevation data.
        
        Args:
            msp: Model space
            start_point: (x, y) coordinates of pipe start
            end_point: (x, y) coordinates of pipe end
            pipe_data: Pipe data dictionary
            layer_name: DXF layer name
        """
        # Get elevations (use invert elevations for 3D coordinates)
        start_z = pipe_data.get('upstream_invert_elev', 0.0)
        end_z = pipe_data.get('downstream_invert_elev', 0.0)
        
        # Add 3D line
        line = msp.add_line(
            start=(start_point[0], start_point[1], start_z),
            end=(end_point[0], end_point[1], end_z),
            dxfattribs={'layer': layer_name, 'color': 256}  # ByLayer color
        )
        
        return line
    
    def _add_pipe_id_label(self, msp, start_point: Tuple[float, float], end_point: Tuple[float, float],
                          pipe_data: Dict[str, Any], layer_name: str, scale_factor: float) -> None:
        """
        Add pipe ID label above pipe.
        
        Args:
            msp: Model space
            start_point: (x, y) coordinates of pipe start
            end_point: (x, y) coordinates of pipe end
            pipe_data: Pipe data dictionary
            layer_name: DXF layer name
            scale_factor: Scale factor for text size
        """
        # Calculate label position (midpoint, offset upward)
        midpoint = self.geometry_processor.calculate_midpoint(start_point, end_point)
        offset_distance = 2.0 * scale_factor / 1000.0  # 2mm at scale
        label_point = self.geometry_processor.perpendicular_point(
            start_point, end_point, midpoint, offset_distance
        )
        
        # Calculate text rotation
        rotation = self.geometry_processor.calculate_text_rotation(start_point, end_point)
        
        # Add text
        text_height = 1.5 * scale_factor / 1000.0  # 1.5mm at scale
        msp.add_text(
            text=str(pipe_data.get('pipe_id', '')),
            dxfattribs={
                'layer': layer_name,
                'color': 256,
                'height': text_height,
                'rotation': rotation,
                'style': self.template_manager.default_text_style,
                'halign': TextEntityAlignment.CENTER,
                'valign': TextEntityAlignment.MIDDLE
            }
        ).set_pos(label_point)
    
    def _add_pipe_data_label(self, msp, start_point: Tuple[float, float], end_point: Tuple[float, float],
                           pipe_data: Dict[str, Any], layer_name: str, scale_factor: float, 
                           label_format: str) -> None:
        """
        Add length-diameter-slope label below pipe.
        
        Args:
            msp: Model space
            start_point: (x, y) coordinates of pipe start
            end_point: (x, y) coordinates of pipe end
            pipe_data: Pipe data dictionary
            layer_name: DXF layer name
            scale_factor: Scale factor for text size
            label_format: Format string for label
        """
        # Calculate label position (midpoint, offset downward)
        midpoint = self.geometry_processor.calculate_midpoint(start_point, end_point)
        offset_distance = -2.0 * scale_factor / 1000.0  # 2mm at scale, negative for below
        label_point = self.geometry_processor.perpendicular_point(
            start_point, end_point, midpoint, offset_distance
        )
        
        # Calculate text rotation
        rotation = self.geometry_processor.calculate_text_rotation(start_point, end_point)
        
        # Format label text with graceful fallback for missing data
        try:
            label_text = label_format.format(
                length=pipe_data.get('length', 0),
                diameter=pipe_data.get('diameter', 0),
                slope=pipe_data.get('slope', 0.001)
            )
        except (KeyError, ValueError):
            # Fallback to simple format
            length = pipe_data.get('length', 0)
            diameter = pipe_data.get('diameter', 0)
            slope = pipe_data.get('slope', 0.001)
            label_text = f"{length:.0f}-{diameter:.0f}-{slope:.5f}"
        
        # Add text
        text_height = 1.2 * scale_factor / 1000.0  # 1.2mm at scale
        msp.add_text(
            text=label_text,
            dxfattribs={
                'layer': layer_name,
                'color': 256,
                'height': text_height,
                'rotation': rotation,
                'style': self.template_manager.default_text_style,
                'halign': TextEntityAlignment.CENTER,
                'valign': TextEntityAlignment.MIDDLE
            }
        ).set_pos(label_point)
    
    def _add_flow_arrow(self, msp, start_point: Tuple[float, float], end_point: Tuple[float, float],
                       layer_name: str, scale_factor: float) -> None:
        """
        Add flow direction arrow using SETA block.
        
        Args:
            msp: Model space
            start_point: (x, y) coordinates of pipe start
            end_point: (x, y) coordinates of pipe end
            layer_name: DXF layer name
            scale_factor: Scale factor for arrow size
        """
        # Calculate arrow placement
        arrow_info = self.geometry_processor.calculate_arrow_placement(
            start_point, end_point, scale_factor / 1000.0, 20.0
        )
        
        if arrow_info:
            arrow_x, arrow_y, rotation = arrow_info
            arrow_scale = scale_factor / 1000.0
            
            # Add arrow block insert
            msp.add_blockref(
                name=self.template_manager.ARROW_BLOCK,
                insert=(arrow_x, arrow_y),
                dxfattribs={
                    'layer': layer_name,
                    'color': self.get_aci_color(self.COLOR_ARROW),
                    'xscale': arrow_scale,
                    'yscale': arrow_scale,
                    'rotation': rotation
                }
            )
    
    def _add_pipe_xdata(self, msp, pipe_data: Dict[str, Any]) -> None:
        """
        Add extended entity data (XDATA) to the last added entity.
        
        Args:
            msp: Model space
            pipe_data: Pipe data dictionary
        """
        try:
            # Get the last entity added (should be the pipe line)
            entities = list(msp)
            if entities:
                last_entity = entities[-1]
                
                # Add XDATA with pipe information
                xdata = [
                    (1000, 'PIPE_DATA'),
                    (1000, str(pipe_data.get('pipe_id', ''))),
                    (1040, float(pipe_data.get('diameter', 0))),
                    (1040, float(pipe_data.get('length', 0))),
                    (1040, float(pipe_data.get('slope', 0))),
                    (1000, str(pipe_data.get('material', ''))),
                ]
                
                last_entity.set_xdata('REDBASICA_EXPORT', xdata)
        except Exception:
            # Ignore XDATA errors - not critical for export
            pass
    
    def _add_junction_symbol(self, msp, coordinates: Tuple[float, float], junction_data: Dict[str, Any],
                           layer_name: str, scale_factor: float) -> None:
        """
        Add junction symbol (circle) to DXF.
        
        Args:
            msp: Model space
            coordinates: (x, y) coordinates of junction
            junction_data: Junction data dictionary
            layer_name: DXF layer name
            scale_factor: Scale factor for symbol size
        """
        # Get elevation for 3D coordinate
        z = junction_data.get('invert_elevation', 0.0)
        
        # Calculate circle radius
        radius = 1.0 * scale_factor / 1000.0  # 1mm at scale
        
        # Add circle
        circle = msp.add_circle(
            center=(coordinates[0], coordinates[1], z),
            radius=radius,
            dxfattribs={'layer': layer_name, 'color': 256}
        )
        
        return circle
    
    def _add_junction_id_label(self, msp, coordinates: Tuple[float, float], junction_data: Dict[str, Any],
                             layer_name: str, scale_factor: float) -> None:
        """
        Add junction ID label.
        
        Args:
            msp: Model space
            coordinates: (x, y) coordinates of junction
            junction_data: Junction data dictionary
            layer_name: DXF layer name
            scale_factor: Scale factor for text size
        """
        # Calculate label position (offset to avoid symbol)
        offset_distance = 2.5 * scale_factor / 1000.0  # 2.5mm at scale
        label_point = (coordinates[0] + offset_distance, coordinates[1] + offset_distance)
        
        # Add text
        text_height = 1.5 * scale_factor / 1000.0  # 1.5mm at scale
        msp.add_text(
            text=str(junction_data.get('node_id', '')),
            dxfattribs={
                'layer': layer_name,
                'color': 256,
                'height': text_height,
                'style': self.template_manager.default_text_style,
                'halign': TextEntityAlignment.LEFT,
                'valign': TextEntityAlignment.BOTTOM
            }
        ).set_pos(label_point)
    
    def _add_elevation_block(self, msp, coordinates: Tuple[float, float], junction_data: Dict[str, Any],
                           layer_name: str, scale_factor: float) -> None:
        """
        Add manhole elevation data block.
        
        Args:
            msp: Model space
            coordinates: (x, y) coordinates of junction
            junction_data: Junction data dictionary
            layer_name: DXF layer name
            scale_factor: Scale factor for block size
        """
        # Determine which elevation block to use based on position
        # For simplicity, use pv_dados_NE (northeast) block
        block_name = 'pv_dados_NE'
        
        # Calculate block position (offset from junction)
        offset_distance = 4.0 * scale_factor / 1000.0  # 4mm at scale
        block_point = (coordinates[0] + offset_distance, coordinates[1] + offset_distance)
        
        # Prepare elevation data
        ground_elev = junction_data.get('ground_elevation', 0.0)
        invert_elev = junction_data.get('invert_elevation', 0.0)
        depth = junction_data.get('depth', 0.0)
        
        # Add block insert with attributes
        block_scale = scale_factor / 1000.0
        block_ref = msp.add_blockref(
            name=block_name,
            insert=block_point,
            dxfattribs={
                'layer': layer_name,
                'color': 256,
                'xscale': block_scale,
                'yscale': block_scale
            }
        )
        
        # Add attributes if block supports them
        try:
            if block_ref.has_attrib('CT'):
                block_ref.set_attrib('CT', f"{ground_elev:.2f}")
            if block_ref.has_attrib('CF'):
                block_ref.set_attrib('CF', f"{invert_elev:.2f}")
            if block_ref.has_attrib('PROF'):
                block_ref.set_attrib('PROF', f"{depth:.2f}")
        except Exception:
            # If attributes not available, add simple text
            text_height = 1.0 * scale_factor / 1000.0
            text_lines = [
                f"CT: {ground_elev:.2f}",
                f"CF: {invert_elev:.2f}",
                f"PROF: {depth:.2f}"
            ]
            
            for i, line in enumerate(text_lines):
                text_y = block_point[1] - (i * text_height * 1.2)
                msp.add_text(
                    text=line,
                    dxfattribs={
                        'layer': layer_name,
                        'color': 256,
                        'height': text_height,
                        'style': self.template_manager.default_text_style
                    }
                ).set_pos((block_point[0], text_y))
    
    def _add_junction_xdata(self, msp, junction_data: Dict[str, Any]) -> None:
        """
        Add extended entity data (XDATA) to the last added entity.
        
        Args:
            msp: Model space
            junction_data: Junction data dictionary
        """
        try:
            # Get the last entity added (should be the junction circle)
            entities = list(msp)
            if entities:
                last_entity = entities[-1]
                
                # Add XDATA with junction information
                xdata = [
                    (1000, 'JUNCTION_DATA'),
                    (1000, str(junction_data.get('node_id', ''))),
                    (1040, float(junction_data.get('ground_elevation', 0))),
                    (1040, float(junction_data.get('invert_elevation', 0))),
                    (1040, float(junction_data.get('depth', 0))),
                ]
                
                last_entity.set_xdata('REDBASICA_EXPORT', xdata)
        except Exception:
            # Ignore XDATA errors - not critical for export
            pass
    
    def _get_layer_by_id(self, layer_id: str) -> Optional[QgsVectorLayer]:
        """
        Get QGIS layer by ID.
        
        Args:
            layer_id: QGIS layer ID
            
        Returns:
            QgsVectorLayer or None if not found
        """
        try:
            layer = QgsProject.instance().mapLayer(layer_id)
            if isinstance(layer, QgsVectorLayer):
                return layer
        except Exception:
            pass
        except Exception:
            pass
        return None

    def _add_enhanced_pipe_label(self, msp, p1: Any, p2: Any, 
                               pipe_data: Dict[str, Any], layer_name: str, 
                               scale_factor: float, config: ExportConfiguration):
        """Add MTEXT label for pipe."""
        try:
            from .data_structures import LabelStyle
            from .utils.geometry_utils import (
                get_cad_angle, get_readable_rotation,
                normalize_angle
            )
            from ezdxf.enums import MTextEntityAlignment
            import math
            
            # Prepare content
            name = str(pipe_data.get('pipe_id', '?'))
            
            # Format numbers consistently
            try:    l_val = float(pipe_data.get('length', 0))
            except: l_val = 0
            
            try:    d_val = float(pipe_data.get('diameter', 0))
            except: d_val = 0
            
            try:    s_val = float(pipe_data.get('slope', 0))
            except: s_val = 0
            
            length = f"{l_val:.2f}"
            diameter = f"Ø{d_val:.0f}"
            slope = f"{s_val:.4f} m/m" if config.include_slope_unit else f"{s_val:.4f}"
            
            # Prepare Drop Info
            drop_type = pipe_data.get('drop_type')
            drop_height = pipe_data.get('drop_height')
            drop_str = ""
            if drop_type:
                try:
                    h_val = float(drop_height)
                    height_str = f"{h_val:.2f}"
                except:
                    height_str = ""
                drop_str = f"{drop_type} {height_str}".strip()
            
            # Geometry
            angle = get_cad_angle(p1, p2)
            rotation = get_readable_rotation(angle)
            
            # Calculate Visual Up Vector based on TEXT rotation (not just line geometry)
            # Rotation is in degrees. +90 is "Up" relative to text reading direction
            rad_up = math.radians(rotation + 90)
            up_x = math.cos(rad_up)
            up_y = math.sin(rad_up)
            
            # Midpoint
            mid_x = (p1.x() + p2.x()) / 2.0
            mid_y = (p1.y() + p2.y()) / 2.0
            
            text_height = 2.0 * scale_factor / 1000.0
            
            # Prepare color codes
            c_name = self.format_mtext_color_rgb(self.COLOR_PIPE_NAME)
            c_len = self.format_mtext_color_rgb(self.COLOR_DEPTH_LENGTH)
            c_adaptive = self.format_mtext_color_aci(7)
            
            if config.label_style == LabelStyle.COMPACT:
                # Split Style: 
                # Top: Phone ID (Red) - Length (Gray)
                # Bottom: Diameter Slope (Adaptive)
                
                content_top = f"{c_name}{name} {c_adaptive}- {c_len}{length}"
                content_btm = f"{c_adaptive}{diameter} {slope}"
                
                if drop_str:
                    content_btm += f"\\P{c_adaptive}{drop_str}"
                
                # Offsets
                # Top text: Anchor BottomCenter. Pos = Mid + padding * Up
                # Bottom text: Anchor TopCenter. Pos = Mid - padding * Up
                padding = 1.0 * scale_factor / 1000.0 # 1mm paper gap
                
                # Top Entity
                top_x = mid_x + (up_x * padding)
                top_y = mid_y + (up_y * padding)
                
                mtext_top = msp.add_mtext(
                    content_top,
                    dxfattribs={
                        'layer': layer_name,
                        'style': self.template_manager.default_text_style,
                        'char_height': text_height,
                        'color': 256,
                        'rotation': rotation,
                    }
                )
                mtext_top.set_location(
                    insert=(top_x, top_y),
                    attachment_point=MTextEntityAlignment.BOTTOM_CENTER
                )
                
                # Bottom Entity
                btm_x = mid_x - (up_x * padding)
                btm_y = mid_y - (up_y * padding)
                
                mtext_btm = msp.add_mtext(
                    content_btm,
                    dxfattribs={
                        'layer': layer_name,
                        'style': self.template_manager.default_text_style,
                        'char_height': text_height,
                        'color': 256,
                        'rotation': rotation,
                    }
                )
                mtext_btm.set_location(
                    insert=(btm_x, btm_y),
                    attachment_point=MTextEntityAlignment.TOP_CENTER
                )
                
            else:
                # Stacked (4 lines) -> Now 5 lines with gap in middle
                # We want the middle (empty line) to be ON the pipe line (where arrow is).
                # So we center the MTEXT on the midpoint with NO OFFSET.
                
                # Content: Name(Red) \P Length(Gray) \P (Space) \P Diameter(Adaptive) \P Slope(Adaptive)
                content = f"{c_name}{name}\\P{c_len}{length}\\P \\P{c_adaptive}{diameter}\\P{c_adaptive}{slope}"
                
                if drop_str:
                    content += f"\\P{c_adaptive}{drop_str}"
                
                # Position = Geometric Midpoint (no offset)
                pos_x = mid_x
                pos_y = mid_y
                
                mtext = msp.add_mtext(
                    content,
                    dxfattribs={
                        'layer': layer_name,
                        'style': self.template_manager.default_text_style,
                        'char_height': text_height,
                        'color': 256,
                        'rotation': rotation,
                    }
                )
                mtext.set_location(
                    insert=(pos_x, pos_y),
                    attachment_point=MTextEntityAlignment.MIDDLE_CENTER
                )
                
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Error adding MTEXT label: {e}", "RedBasica Export", Qgis.Warning)


    def _add_multileader_node_label(self, msp, point: Any, 
                                  junction_data: Dict[str, Any], layer_name: str, 
                                  scale_factor: float, export_node_id: bool = False):
        """
        Add Multileader label for node using ezdxf 1.4.3 API.
        
        Layout (matching reference image):
        CT: 148.680
        CF: 147.630   1.050 - col_001-001  (with node ID)
        CF: 147.630   1.050                (without node ID)
        
        Geometry:
        - 2 segments: diagonal from node, then horizontal to text (dogleg)
        - No arrow at target
        - Straight lines (not splines)
        - Text anchored properly to horizontal segment
        
        Args:
            export_node_id: If True, includes node ID after depth in label.
        """
        from qgis.core import QgsMessageLog, Qgis
        
        try:
            from ezdxf.math import Vec2
            from ezdxf.render import mleader
            
            # Extract values with fallbacks
            try:    ct_val = float(junction_data.get('ground_elevation', 0))
            except: ct_val = 0
            
            try:    cf_val = float(junction_data.get('invert_elevation', 0))
            except: cf_val = 0
            
            # Get depth from data, or calculate from CT - CF
            try:    prof_val = float(junction_data.get('depth', 0))
            except: prof_val = 0
            
            # If depth is 0 or not provided, calculate from CT - CF
            if prof_val == 0 and ct_val > 0 and cf_val > 0:
                prof_val = max(0, ct_val - cf_val)
            
            node_id = junction_data.get('node_id', '')
            
            # Build content string matching reference layout:
            # Line 1: CT: xxx.xxx
            # Line 2: CF: xxx.xxx   Prof (optionally with node ID: Prof - Node_ID)
            line1 = f"CT: {ct_val:.3f}"
            if export_node_id and node_id:
                line2 = f"CF: {cf_val:.3f}   {prof_val:.3f} - {node_id}"
            else:
                line2 = f"CF: {cf_val:.3f}   {prof_val:.3f}"
            content = f"{line1}\\P{line2}"  # Using \P for paragraph break (MTEXT style)
            
            # Calculate text height based on scale (2mm at paper scale)
            char_height = 2.0 * scale_factor / 1000.0
            
            # Calculate segment lengths based on scale
            # segment1: diagonal offset from target (relative vector)
            # segment2: horizontal dogleg (relative vector from end of segment1)
            diag_len = 8.0 * scale_factor / 1000.0
            horiz_len = 5.0 * scale_factor / 1000.0
            
            # Target point (where the leader points to - the node)
            target = Vec2(point.x(), point.y())
            
            # Segment 1: diagonal going up-right (relative to target)
            segment1 = Vec2(diag_len, diag_len)
            
            # Segment 2: horizontal going right (relative to end of segment1)
            segment2 = Vec2(horiz_len, 0)
            
            # Create the MULTILEADER builder
            ml_builder = msp.add_multileader_mtext("Standard")
            
            # === CRITICAL SETTINGS ===
            
            # 1. Set leader type to STRAIGHT (not splines)
            ml_builder.set_leader_properties(
                leader_type=mleader.LeaderType.straight_lines
            )
            
            # 2. Disable arrow by setting size to 0
            ml_builder.set_arrow_properties(size=0)
            
            # 3. Set connection properties for proper dogleg
            landing_gap = 0.5 * scale_factor / 1000.0
            ml_builder.set_connection_properties(
                landing_gap=landing_gap,
                dogleg_length=horiz_len
            )
            
            # 4. Set content with explicit char_height
            ml_builder.set_content(
                content,
                char_height=char_height,
                alignment=mleader.TextAlignment.left
            )
            
            # 5. Use quick_leader for proper geometry
            # HorizontalConnection.left means leader connects to LEFT side of text
            # So text extends to the RIGHT of the leader end
            ml_builder.quick_leader(
                content=content,
                target=target,
                segment1=segment1,
                segment2=segment2,
                connection_type=mleader.HorizontalConnection.middle_of_text
            )
            
            # Set layer on the created entity
            if hasattr(ml_builder, 'multileader') and ml_builder.multileader:
                ml_builder.multileader.dxf.layer = layer_name
                
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Error adding MULTILEADER label: {e}", "RedBasica Export", Qgis.Warning)

    
    def _reset_stats(self) -> None:
        """Reset export statistics."""
        self.stats = {
            'pipes_exported': 0,
            'junctions_exported': 0,
            'pipes_skipped': 0,
            'junctions_skipped': 0,
            'errors': []
        }
    
    def _generate_success_message(self, output_path: str) -> str:
        """
        Generate success message with statistics.
        
        Args:
            output_path: Path to exported DXF file
            
        Returns:
            Success message string
        """
        message_parts = [
            f"DXF export completed successfully!",
            f"File saved to: {output_path}",
            f"Pipes exported: {self.stats['pipes_exported']}",
        ]
        
        if self.stats['junctions_exported'] > 0:
            message_parts.append(f"Junctions exported: {self.stats['junctions_exported']}")
        
        if self.stats['pipes_skipped'] > 0 or self.stats['junctions_skipped'] > 0:
            message_parts.append(f"Features skipped: {self.stats['pipes_skipped'] + self.stats['junctions_skipped']}")
        
        if self.stats['errors']:
            message_parts.append(f"Warnings: {len(self.stats['errors'])}")
        
        return "\n".join(message_parts)
    
    def get_export_preview(self, config: ExportConfiguration) -> Dict[str, Any]:
        """
        Generate export preview without actually exporting.
        
        Args:
            config: Export configuration
            
        Returns:
            Dictionary with preview information
        """
        preview = {
            'pipes_count': 0,
            'junctions_count': 0,
            'estimated_entities': 0,
            'layers_to_create': [],
            'validation_errors': []
        }
        
        try:
            # Validate configuration
            if not config.is_valid():
                preview['validation_errors'] = config.get_validation_errors()
                return preview
            
            # Count features in pipes layer
            if config.pipes_mapping:
                pipes_layer = self._get_layer_by_id(config.pipes_mapping.layer_id)
                if pipes_layer:
                    preview['pipes_count'] = pipes_layer.featureCount()
                    # Estimate entities: line + 2 labels + arrow per pipe
                    preview['estimated_entities'] += preview['pipes_count'] * 4
            
            # Count features in junctions layer
            if config.junctions_mapping:
                junctions_layer = self._get_layer_by_id(config.junctions_mapping.layer_id)
                if junctions_layer:
                    preview['junctions_count'] = junctions_layer.featureCount()
                    # Estimate entities: circle + label + elevation block per junction
                    preview['estimated_entities'] += preview['junctions_count'] * 3
            
            # List layers to be created
            for layer_name, _, description in self.template_manager.LAYER_DEFINITIONS:
                full_name = self.template_manager.get_layer_name(layer_name, config.layer_prefix)
                preview['layers_to_create'].append(f"{full_name} - {description}")
            
        except Exception as e:
            preview['validation_errors'].append(f"Preview generation failed: {str(e)}")
        
        return preview  
  
    def export_with_error_handling(self, config: ExportConfiguration) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Export sewerage network to DXF with comprehensive error handling.
        
        Args:
            config: Export configuration with layer mappings and settings
            
        Returns:
            Tuple of (success, message, statistics)
        """
        print(f"DEBUG: export_with_error_handling called")
        print(f"DEBUG: config: {config}")
        print(f"DEBUG: config.pipes_mapping: {config.pipes_mapping}")
        print(f"DEBUG: config.junctions_mapping: {config.junctions_mapping}")
        
        progress = ProgressTracker(7, self.progress_callback)
        progress.start()
        
        try:
            # Step 1: Validate and prepare output path
            progress.update(1, "Validating output path...")
            try:
                validated_path = validate_and_prepare_output_path(config.output_path)
                config.output_path = validated_path
            except (FilePermissionError, ExportError) as e:
                error_msg = self.error_formatter.format_file_error("file_permission_denied", 
                                                                 file_path=config.output_path, 
                                                                 operation="write")
                progress.finish(False, "Path validation failed")
                return False, error_msg, self.error_manager.get_error_summary()
            
            # Step 2: Initialize DXF document
            progress.update(2, "Initializing DXF document...")
            try:
                doc = self._initialize_dxf_document(config)
            except (TemplateError, ExportError) as e:
                error_msg = self.error_formatter.format_export_error("template_not_found",
                                                                   template_path=config.template_path or "default")
                progress.finish(False, "DXF initialization failed")
                return False, error_msg, self.error_manager.get_error_summary()
            
            # Step 3: Set up layers and styles
            progress.update(3, "Setting up DXF layers...")
            try:
                self._setup_dxf_layers(doc, config.layer_prefix)
            except ExportError as e:
                self.error_manager.record_error(
                    ErrorSeverity.ERROR,
                    f"Failed to setup DXF layers: {e}",
                    error_type="layer_setup_failed"
                )
                progress.finish(False, "Layer setup failed")
                return False, str(e), self.error_manager.get_error_summary()
            
            # Step 4: Export pipes
            progress.update(4, "Exporting pipe network...")
            pipes_stats = self._export_pipes_with_recovery(doc, config)
            
            # Step 5: Export junctions
            progress.update(5, "Exporting junctions...")
            junctions_stats = self._export_junctions_with_recovery(doc, config)
            
            # Step 6: Save DXF file
            progress.update(6, "Saving DXF file...")
            try:
                doc.saveas(config.output_path)
            except Exception as e:
                error_msg = self.error_formatter.format_export_error("export_failed",
                                                                   error_details=str(e))
                progress.finish(False, "File save failed")
                return False, error_msg, self.error_manager.get_error_summary()
            
            # Step 7: Generate final report
            progress.update(7, "Generating export report...")
            
            # Combine statistics
            total_processed = pipes_stats.processed_features + junctions_stats.processed_features
            total_features = pipes_stats.total_features + junctions_stats.total_features
            total_errors = self.error_manager.stats.errors
            total_warnings = self.error_manager.stats.warnings
            
            # Generate success message
            if total_errors == 0 and total_warnings == 0:
                success_msg = f"Export completed successfully: {total_processed}/{total_features} features exported to {config.output_path}"
            else:
                success_msg = self.error_formatter.format_progress_summary(
                    total_processed, total_features, total_errors, total_warnings
                )
                success_msg += f"\n\nDXF file saved to: {config.output_path}"
            
            progress.finish(True, "Export completed")
            
            return True, success_msg, self.error_manager.get_error_summary()
            
        except Exception as e:
            # Catch-all for unexpected errors
            self.error_manager.record_error(
                ErrorSeverity.CRITICAL,
                f"Unexpected error during export: {e}",
                error_type="unexpected_error",
                exception=e
            )
            
            error_msg = self.error_formatter.format_export_error("export_failed",
                                                               error_details=str(e))
            progress.finish(False, "Export failed with unexpected error")
            
            return False, error_msg, self.error_manager.get_error_summary()
    
    def _initialize_dxf_document(self, config: ExportConfiguration):
        """Initialize DXF document with error handling."""
        try:
            if config.template_path and os.path.exists(config.template_path):
                # Load from template
                doc = ezdxf.readfile(config.template_path)
                self.error_manager.record_error(
                    ErrorSeverity.INFO,
                    f"Loaded template: {config.template_path}",
                    error_type="template_loaded"
                )
            else:
                # Create new document
                doc = ezdxf.new('R2018')
                self.error_manager.record_error(
                    ErrorSeverity.INFO,
                    "Created new DXF document (no template)",
                    error_type="document_created"
                )
            
            # Set up application ID for extended data
            if 'REDBASICA_EXPORT' not in doc.appids:
                doc.appids.new('REDBASICA_EXPORT')
            
            return doc
            
        except Exception as e:
            raise TemplateError(config.template_path or "default", str(e))
    
    def _setup_dxf_layers(self, doc, layer_prefix: str = "ESG_"):
        """Set up DXF layers with error handling."""
        try:
            # Define layer structure (QEsg compatible)
            layer_definitions = [
                ('REDE', 172, 'Sewage pipes/network'),
                ('NUMERO', 3, 'Pipe ID labels'),
                ('TEXTO', 3, 'Pipe data labels'),
                ('TEXTOPVS', 7, 'Manhole elevation data'),
                ('PV', 3, 'Manholes/junctions'),
                ('NUMPV', 3, 'Manhole ID labels'),
                ('SETA', 172, 'Flow direction arrows'),
                ('NO', 3, 'Dry point symbols'),
                ('AUX', 241, 'Auxiliary elements'),
                ('LIDER', 2, 'Leader lines'),
            ]
            
            for base_name, color, description in layer_definitions:
                layer_name = f"{layer_prefix}{base_name}"
                
                if layer_name not in doc.layers:
                    doc.layers.new(layer_name, dxfattribs={'color': color})
                    
            # Set up text styles
            if 'ROMANS' not in doc.styles:
                doc.styles.new('ROMANS', dxfattribs={'font': 'romans.shx'})
            if self.CAD_FONT not in doc.styles:
                doc.styles.new(self.CAD_FONT, dxfattribs={'font': 'simplex.shx'})
                
        except Exception as e:
            raise ExportError(f"Failed to setup DXF layers: {e}")
    
    def _export_pipes_with_recovery(self, doc, config: ExportConfiguration):
        """Export pipes with error recovery."""
        from .error_recovery import ProcessingStats
        
        print(f"DEBUG: _export_pipes_with_recovery called")
        print(f"DEBUG: config type: {type(config)}")
        print(f"DEBUG: config.pipes_mapping: {config.pipes_mapping}")
        print(f"DEBUG: config.pipes_mapping type: {type(config.pipes_mapping)}")
        
        stats = ProcessingStats()
        
        if not config.pipes_mapping or not config.pipes_mapping.layer_id:
            print(f"DEBUG: No pipes layer configured")
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                "No pipes layer configured - skipping pipe export",
                error_type="no_pipes_layer"
            )
            return stats
        
        # Get pipes layer
        project = QgsProject.instance()
        print(f"DEBUG: Getting pipes layer with ID: {config.pipes_mapping.layer_id}")
        pipes_layer = project.mapLayer(config.pipes_mapping.layer_id)
        print(f"DEBUG: pipes_layer: {pipes_layer}")
        print(f"DEBUG: pipes_layer.isValid(): {pipes_layer.isValid() if pipes_layer else 'N/A'}")
        
        if not pipes_layer or not pipes_layer.isValid():
            self.error_manager.record_error(
                ErrorSeverity.ERROR,
                f"Pipes layer not found or invalid: {config.pipes_mapping.layer_id}",
                error_type="layer_not_found"
            )
            return stats
        
        # Process features with error recovery
        print(f"DEBUG: Getting features from pipes layer")
        features = list(pipes_layer.getFeatures())
        print(f"DEBUG: Got {len(features)} features")
        stats.total_features = len(features)
        
        print(f"DEBUG: Getting modelspace")
        msp = doc.modelspace()
        print(f"DEBUG: Starting feature loop")
        
        for i, feature in enumerate(features):
            print(f"DEBUG: Processing feature {i+1}/{len(features)}")
            if not self.error_manager.should_continue:
                break
                
            try:
                context = create_error_recovery_context(feature, pipes_layer.name(), "pipe_export")
                
                print(f"DEBUG: About to call _extract_feature_data_safe")
                print(f"DEBUG: feature id: {feature.id()}")
                print(f"DEBUG: config.pipes_mapping type: {type(config.pipes_mapping)}")
                print(f"DEBUG: config.pipes_mapping.field_mappings: {config.pipes_mapping.field_mappings}")
                
                # Extract feature data with error handling
                feature_data = self._extract_feature_data_safe(
                    feature, config.pipes_mapping, "pipes"
                )
                print(f"DEBUG: _extract_feature_data_safe returned: {feature_data}")
                
                if feature_data is None:
                    stats.skipped_features += 1
                    continue
                
                # Calculate derived fields (slope, depths, etc.)
                feature_data = self._calculate_pipe_fields(feature_data)
                print(f"DEBUG: After _calculate_pipe_fields: {feature_data}")
                
                # Export pipe geometry and labels
                print(f"DEBUG: About to call _export_pipe_feature")
                print(f"DEBUG: config.include_labels: {config.include_labels}")
                print(f"DEBUG: config.include_arrows: {config.include_arrows}")
                self._export_pipe_feature(msp, feature, feature_data, config)
                stats.processed_features += 1
                
            except Exception as e:
                context = create_error_recovery_context(feature, pipes_layer.name(), "pipe_export")
                continue_processing = handle_feature_processing_error(
                    self.error_manager, e, context
                )
                
                if continue_processing:
                    stats.failed_features += 1
                else:
                    break
        
        return stats
    
    def _export_junctions_with_recovery(self, doc, config: ExportConfiguration):
        """Export junctions with error recovery."""
        from .error_recovery import ProcessingStats
        
        stats = ProcessingStats()
        
        if not config.junctions_mapping or not config.junctions_mapping.layer_id:
            self.error_manager.record_error(
                ErrorSeverity.INFO,
                "No junctions layer configured - skipping junction export",
                error_type="no_junctions_layer"
            )
            return stats
        
        # Get junctions layer
        project = QgsProject.instance()
        junctions_layer = project.mapLayer(config.junctions_mapping.layer_id)
        
        if not junctions_layer or not junctions_layer.isValid():
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                f"Junctions layer not found or invalid: {config.junctions_mapping.layer_id}",
                error_type="layer_not_found"
            )
            return stats
        
        # Process features with error recovery
        features = list(junctions_layer.getFeatures())
        stats.total_features = len(features)
        
        msp = doc.modelspace()
        
        for feature in features:
            if not self.error_manager.should_continue:
                break
                
            try:
                context = create_error_recovery_context(feature, junctions_layer.name(), "junction_export")
                
                # Extract feature data with error handling
                feature_data = self._extract_feature_data_safe(
                    feature, config.junctions_mapping, "junctions"
                )
                
                if feature_data is None:
                    stats.skipped_features += 1
                    continue
                
                # Export junction geometry and labels
                self._export_junction_feature(msp, feature, feature_data, config)
                stats.processed_features += 1
                
            except Exception as e:
                context = create_error_recovery_context(feature, junctions_layer.name(), "junction_export")
                continue_processing = handle_feature_processing_error(
                    self.error_manager, e, context
                )
                
                if continue_processing:
                    stats.failed_features += 1
                else:
                    break
        
        return stats
    
    def _extract_feature_data_safe(self, feature: QgsFeature, mapping: LayerMapping, 
                                 feature_type: str) -> Optional[Dict[str, Any]]:
        """Extract feature data with error handling and type conversion."""
        try:
            print(f"DEBUG: _extract_feature_data_safe ENTRY - feature_type: {feature_type}")
            print(f"DEBUG: mapping type: {type(mapping)}")
            print(f"DEBUG: mapping.field_mappings type: {type(mapping.field_mappings)}")
            print(f"DEBUG: mapping.field_mappings: {mapping.field_mappings}")
            
            feature_data = {}
            
            # Get all fields based on feature type
            if feature_type == "pipes":
                all_fields = SewageNetworkFields.get_all_pipe_fields()
            else:
                all_fields = SewageNetworkFields.get_all_junction_fields()
            
            # Extract and convert field values
            for field_def in all_fields:
                field_name = field_def.name
                
                print(f"DEBUG: Processing field: {field_name}")
                print(f"DEBUG: mapping.field_mappings type: {type(mapping.field_mappings)}")
                print(f"DEBUG: mapping.field_mappings: {mapping.field_mappings}")
                
                # Get mapped field name or use default
                try:
                    # Ensure field_mappings is actually a dictionary
                    if not isinstance(mapping.field_mappings, dict):
                        print(f"ERROR: field_mappings is not a dict: {type(mapping.field_mappings)}")
                        # Try to convert if it's a proper dictionary-like sequence
                        if hasattr(mapping.field_mappings, 'items'):
                            mapping.field_mappings = dict(mapping.field_mappings)
                            print(f"DEBUG: Converted field_mappings to dict: {mapping.field_mappings}")
                        else:
                            # Fallback: create empty dict if completely invalid
                            mapping.field_mappings = {}
                            print(f"DEBUG: Fallback: created empty field_mappings dict")
                    
                    field_in_mappings = field_name in mapping.field_mappings
                    print(f"DEBUG: '{field_name}' in mapping.field_mappings: {field_in_mappings}")
                except Exception as e:
                    print(f"DEBUG: Error checking if '{field_name}' in mapping.field_mappings: {e}")
                    print(f"DEBUG: Exception type: {type(e)}")
                    raise
                
                if field_name in mapping.field_mappings:
                    source_field = mapping.field_mappings[field_name]
                    raw_value = feature[source_field] if source_field in feature.fields().names() else None
                elif hasattr(mapping, 'default_values') and isinstance(mapping.default_values, dict) and field_name in mapping.default_values:
                    raw_value = mapping.default_values[field_name]
                else:
                    raw_value = field_def.default_value
                
                # Convert value to appropriate type
                try:
                    if field_def.field_type == FieldType.STRING:
                        converted_value = self.data_converter.to_string(raw_value)
                    elif field_def.field_type == FieldType.DOUBLE:
                        converted_value = self.data_converter.to_double(raw_value)
                    elif field_def.field_type == FieldType.INTEGER:
                        converted_value = self.data_converter.to_integer(raw_value)
                    else:
                        converted_value = raw_value
                    
                    feature_data[field_name] = converted_value
                    
                except Exception as e:
                    # Use recovery strategy for conversion errors
                    recovery_context = {
                        'field_name': field_name,
                        'raw_value': raw_value,
                        'target_type': field_def.field_type.value,
                        'default_value': field_def.default_value,
                        'feature_id': str(feature.id())
                    }
                    
                    success, default_value = self.error_manager.apply_recovery_strategy(
                        'data_conversion_error', recovery_context
                    )
                    
                    if success:
                        feature_data[field_name] = default_value or field_def.default_value
                    else:
                        # Critical conversion failure
                        raise ExportError(f"Failed to convert field {field_name}: {e}")
            
            return feature_data
            
        except Exception as e:
            self.error_manager.record_error(
                ErrorSeverity.ERROR,
                f"Failed to extract feature data: {e}",
                feature_id=str(feature.id()),
                error_type="data_extraction_failed",
                exception=e
            )
            return None
    
    def _export_pipe_feature(self, msp, feature: QgsFeature, feature_data: Dict[str, Any], 
                           config: ExportConfiguration):
        """Export a single pipe feature with error handling."""
        try:
            geometry = feature.geometry()
            if geometry.isNull() or not geometry.isGeosValid():
                raise GeometryError(str(feature.id()), "Invalid or null geometry")
            
            # Get line coordinates
            if geometry.isMultipart():
                # Handle multipart geometry - use first part
                parts = geometry.asMultiPolyline()
                if not parts:
                    raise GeometryError(str(feature.id()), "Empty multipart geometry")
                line_coords = parts[0]
            else:
                line_coords = geometry.asPolyline()
            
            if len(line_coords) < 2:
                raise GeometryError(str(feature.id()), "Line has less than 2 points")
            
            # Convert to DXF coordinates
            start_point = (line_coords[0].x(), line_coords[0].y(), 0)
            end_point = (line_coords[-1].x(), line_coords[-1].y(), 0)
            
            # Add pipe line to DXF
            line = msp.add_line(
                start_point, end_point,
                dxfattribs={'layer': f"{config.layer_prefix}REDE", 'color': 256}
            )
            
            # Add extended data
            pipe_id = feature_data.get('pipe_id', str(feature.id()))
            diameter = feature_data.get('diameter', 0)
            length = feature_data.get('length', 0)
            
            line.set_xdata('REDBASICA_EXPORT', [
                (1000, 'PIPE_DATA'),
                (1000, pipe_id),
                (1040, diameter),
                (1040, length)
            ])
            
            # Add labels if enabled
            print(f"DEBUG: _export_pipe_feature - config.include_labels: {config.include_labels}")
            if config.include_labels:
                print(f"DEBUG: Calling _add_pipe_labels")
                self._add_pipe_labels(msp, line_coords, feature_data, config)
            else:
                print(f"DEBUG: Skipping labels - include_labels is False")
            
            # Add flow arrows if enabled
            print(f"DEBUG: _export_pipe_feature - config.include_arrows: {config.include_arrows}")
            if config.include_arrows:
                print(f"DEBUG: Calling _add_flow_arrows")
                self._add_flow_arrows(msp, line_coords, config)
            else:
                print(f"DEBUG: Skipping arrows - include_arrows is False")
                
            # Add Drop / Drop Pipe markers (even if arrows are disabled, though usually they go together)
            # Uses the same layer prefix logic as arrows or specific layer
            self._add_drop_marker(msp, line_coords[0], line_coords[-1], feature_data, f"{config.layer_prefix}SETA", config.scale_factor)
            print(f"DEBUG: Called _add_drop_marker in recovery mode")

            # Add Collector Depth Label (h_col_p2) if enabled
            if config.include_collector_depth:
                self._add_collector_depth_label(msp, line_coords[0], line_coords[-1], feature_data, f"{config.layer_prefix}TEXTO", config.scale_factor)
                
        except GeometryError:
            raise  # Re-raise geometry errors
        except Exception as e:
            raise ExportError(f"Failed to export pipe feature: {e}")
    
    def _export_junction_feature(self, msp, feature: QgsFeature, feature_data: Dict[str, Any],
                               config: ExportConfiguration):
        """Export a single junction feature with error handling."""
        try:
            geometry = feature.geometry()
            if geometry.isNull() or not geometry.isGeosValid():
                raise GeometryError(str(feature.id()), "Invalid or null geometry")
            
            # Get point coordinates
            if geometry.isMultipart():
                # Handle multipart geometry - use first part
                parts = geometry.asMultiPoint()
                if not parts:
                    raise GeometryError(str(feature.id()), "Empty multipart geometry")
                point = parts[0]
            else:
                point = geometry.asPoint()
            
            # Convert to DXF coordinates
            dxf_point = (point.x(), point.y(), 0)
            
            # Add junction circle to DXF
            circle = msp.add_circle(
                dxf_point, radius=1.0,  # Default radius, could be configurable
                dxfattribs={'layer': f"{config.layer_prefix}PV", 'color': 1}
            )
            
            # Add extended data
            node_id = feature_data.get('node_id', str(feature.id()))
            ground_elevation = feature_data.get('ground_elevation', 0)
            
            circle.set_xdata('REDBASICA_EXPORT', [
                (1000, 'JUNCTION_DATA'),
                (1000, node_id),
                (1040, ground_elevation)
            ])
            
            # Add labels if enabled
            print(f"DEBUG: _export_junction_feature - config.include_labels: {config.include_labels}")
            if config.include_labels:
                print(f"DEBUG: Calling _add_junction_labels")
                self._add_junction_labels(msp, dxf_point, feature_data, config)
            else:
                print(f"DEBUG: Skipping junction labels - include_labels is False")
                
        except GeometryError:
            raise  # Re-raise geometry errors
        except Exception as e:
            raise ExportError(f"Failed to export junction feature: {e}")
    
    def _add_pipe_labels(self, msp, line_coords, feature_data: Dict[str, Any], config: ExportConfiguration):
        """Add pipe labels with error handling."""
        try:
            # Use enhanced pipe labels for proper label style (2/4 lines) support
            # This applies to both STANDARD and ENHANCED modes
            from qgis.core import QgsPointXY
            start = QgsPointXY(line_coords[0].x(), line_coords[0].y())
            end = QgsPointXY(line_coords[-1].x(), line_coords[-1].y())
            text_layer = f"{config.layer_prefix}TEXTO"
            self._add_enhanced_pipe_label(msp, start, end, feature_data, text_layer, config.scale_factor, config)
            
            print(f"DEBUG: _add_pipe_labels called _add_enhanced_pipe_label")
            return  # Done - enhanced method handles everything
            
            # QEsg-style scale calculation and text sizing
            sc = config.scale_factor / 2000.0
            text_height = 3 * sc
            text_offset = 1.25 * sc
            
            start = line_coords[0]
            end = line_coords[-1]
            
            print(f"DEBUG: QEsg-style scale (sc): {sc}, text_height: {text_height}, offset: {text_offset}")
            
            # Add pipe ID label above line (QEsg style)
            pipe_id = feature_data.get('pipe_id', 'Unknown')
            print(f"DEBUG: pipe_id: {pipe_id}")
            print(f"DEBUG: Adding pipe ID text: '{pipe_id}' to layer: {config.layer_prefix}NUMERO")
            
            # Calculate text position and rotation using QEsg method
            azim = self._calculate_azimuth(start, end)
            if azim < 0:
                azim += 360
            rot = 90.0 - azim
            
            # Keep text readable by ensuring rotation is between -90 and +90 degrees
            while rot > 90:
                rot -= 180
            while rot < -90:
                rot += 180
            
            text_pos = self._calculate_text_position(start, end, -text_offset, azim)
            print(f"DEBUG: Text position: {text_pos}, rotation: {rot}")
            
            from ezdxf.enums import TextEntityAlignment
            text_entity = msp.add_text(
                pipe_id,
                height=text_height,
                dxfattribs={
                    'rotation': rot,
                    'style': self.CAD_FONT,
                    'color': self.get_aci_color(self.COLOR_PIPE_NAME),
                    'layer': f"{config.layer_prefix}NUMERO"
                }
            ).set_placement(text_pos, align=TextEntityAlignment.BOTTOM_CENTER)
            print(f"DEBUG: Pipe ID text added successfully")
            
            # Add pipe data label below line
            length = feature_data.get('length', 0)
            diameter = feature_data.get('diameter', 0)
            slope = feature_data.get('slope', feature_data.get('calculated_slope', 0))
            
            print(f"DEBUG: Pipe data - length: {length}, diameter: {diameter}, slope: {slope}")
            print(f"DEBUG: Available feature_data keys: {list(feature_data.keys())}")
            
            data_label = config.label_format.format(
                length=length, diameter=diameter, slope=slope
            )
            
            # Append Drop info if present
            drop_type = feature_data.get('drop_type')
            drop_height = feature_data.get('drop_height')
            if drop_type:
                # Format: "Type Height" e.g "D 0.05" or "TC 0.80"
                height_str = f"{float(drop_height):.2f}" if drop_height is not None else ""
                data_label += f" {drop_type} {height_str}".strip()
            
            print(f"DEBUG: Formatted data label: '{data_label}'")
            
            print(f"DEBUG: Adding pipe data text: '{data_label}' to layer: {config.layer_prefix}TEXTO")
            
            # Add data label below line (QEsg style)
            data_pos = self._calculate_text_position(start, end, text_offset, azim)
            
            data_text_entity = msp.add_text(
                data_label,
                height=text_height,
                dxfattribs={
                    'rotation': rot,
                    'style': self.CAD_FONT, 
                    'color': self.get_aci_color(self.COLOR_DEPTH_LENGTH),
                    'layer': f"{config.layer_prefix}TEXTO"
                }
            ).set_placement(data_pos, align=TextEntityAlignment.TOP_CENTER)
            print(f"DEBUG: Pipe data text added successfully")
            
        except Exception as e:
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                f"Failed to add pipe labels: {e}",
                error_type="label_creation_failed"
            )
    
    def _add_junction_labels(self, msp, point, feature_data: Dict[str, Any], config: ExportConfiguration):
        """Add junction labels with error handling."""
        try:
            # Enhanced Mode Check
            if config.export_mode.name == 'ENHANCED':
                from qgis.core import QgsPointXY
                # point is tuple (x, y, 0)
                point_xy = QgsPointXY(point[0], point[1])
                text_layer = f"{config.layer_prefix}TEXTOPVS" # Using elevation layer for multileader
                self._add_multileader_node_label(msp, point_xy, feature_data, text_layer, config.scale_factor, export_node_id=config.export_node_id)
                return

            print(f"DEBUG: _add_junction_labels ENTRY")
            print(f"DEBUG: point: {point}")
            print(f"DEBUG: feature_data: {feature_data}")
            
            # Skip individual manhole ID label since it's now included in the h-ID block
            print(f"DEBUG: Skipping individual manhole ID label - now included in detailed labels")
            
            # Add detailed manhole data labels (QEsg style)
            self._add_manhole_data_labels(msp, point, feature_data, config)
            
        except Exception as e:
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                f"Failed to add junction labels: {e}",
                error_type="label_creation_failed"
            )
    
    def _add_flow_arrows(self, msp, line_coords, config: ExportConfiguration):
        """Add flow direction arrows with error handling."""
        try:
            print(f"DEBUG: _add_flow_arrows ENTRY")
            print(f"DEBUG: line_coords length: {len(line_coords)}")
            print(f"DEBUG: config.scale_factor: {config.scale_factor}")
            
            # Calculate line length
            total_length = 0
            for i in range(len(line_coords) - 1):
                p1 = line_coords[i]
                p2 = line_coords[i + 1]
                segment_length = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
                total_length += segment_length
            
            print(f"DEBUG: Total line length: {total_length}")
            
            # QEsg-style arrow condition: only for lines longer than 20*sc
            sc = config.scale_factor / 2000.0
            min_length = 20 * sc
            print(f"DEBUG: Minimum length for arrows: {min_length}")
            
            if total_length > min_length:
                print(f"DEBUG: Line is long enough for arrows, proceeding...")
                
                # QEsg-style arrow positioning: middle of line
                start = line_coords[0]
                end = line_coords[-1]
                arrow_x = (start.x() + end.x()) / 2
                arrow_y = (start.y() + end.y()) / 2
                arrow_z = 0  # QEsg calculates from elevations but we'll use 0
                
                # QEsg-style arrow rotation
                azim = self._calculate_azimuth(start, end)
                if azim < 0:
                    azim += 360
                rot = 90.0 - azim
                
                arrow_point = (arrow_x, arrow_y, arrow_z)
                print(f"DEBUG: Adding arrow block at {arrow_point} with rotation {rot}")
                print(f"DEBUG: Arrow layer: {config.layer_prefix}SETA")
                
                # Create arrow block if it doesn't exist (QEsg solid triangle)
                arrow_block_name = f"{config.layer_prefix}SETA"
                if arrow_block_name not in msp.doc.blocks:
                    arrow_block = msp.doc.blocks.new(name=arrow_block_name)
                    arrow_block.add_solid(
                        [(4*sc, 0), (-4*sc, -1.33*sc), (-4*sc, 1.33*sc)],
                        dxfattribs={'color': 0, 'layer': '0'}
                    )
                    print(f"DEBUG: Created arrow block: {arrow_block_name}")
                
                # Add arrow block reference
                msp.add_blockref(
                    arrow_block_name,
                    arrow_point,
                    dxfattribs={
                        'xscale': 1,
                        'yscale': 1,
                        'rotation': rot,
                        'layer': f"{config.layer_prefix}SETA",
                        'color': self.get_aci_color(self.COLOR_ARROW)
                    }
                )
                print(f"DEBUG: Arrow block added successfully")
            else:
                print(f"DEBUG: Line too short for arrows ({total_length} <= {min_length})")
                    
        except Exception as e:
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                f"Failed to add flow arrows: {e}",
                error_type="arrow_creation_failed"
            )
            
    def _ensure_drop_marker_block(self, doc, block_name="RB_DROP_MARKER", n=16):
        """
        Create a filled circle marker block using only R12-safe primitives:
        - Circle outline (CIRCLE)
        - Filled area using a fan of SOLID triangles
        All entities on layer '0' and color BYBLOCK (0).
        """
        if block_name in doc.blocks:
            return

        import math
        # Create block
        blk = doc.blocks.new(name=block_name)

        r = 1.0

        # Outline (always visible even if fill fails)
        blk.add_circle((0, 0), radius=r, dxfattribs={"layer": "0", "color": 0})

        # Fill: triangle fan from center
        cx, cy = 0.0, 0.0
        for i in range(n):
            a1 = 2.0 * math.pi * i / n
            a2 = 2.0 * math.pi * (i + 1) / n
            p1 = (r * math.cos(a1), r * math.sin(a1))
            p2 = (r * math.cos(a2), r * math.sin(a2))

            # SOLID entity (3 or 4 points)
            # For triangle: p1, p2, p3, p3 (repeat last point)
            blk.add_solid(
                [(cx, cy), p1, p2, p2],
                dxfattribs={"layer": "0", "color": 0}
            )
        
        print(f"DEBUG: Created robust drop marker block: {block_name}")

    def _add_drop_marker(self, msp, start_point, end_point, feature_data: Dict[str, Any], layer_name: str, scale_factor: float):
        """Add drop marker using robust block."""
        try:
            drop_type = feature_data.get('drop_type')
            if not drop_type:
                return

            # Determine color
            if drop_type.upper() in ['TC', 'TUBO DE QUEDA']:
                color_rgb = self.COLOR_RED
            else:
                color_rgb = self.COLOR_BLUE
            
            aci_color = self.get_aci_color(color_rgb)
            
            # Access coordinates
            from qgis.core import QgsPointXY
            if hasattr(start_point, 'x'):
                p1 = QgsPointXY(start_point.x(), start_point.y())
            else:
                p1 = QgsPointXY(start_point[0], start_point[1])
                
            if hasattr(end_point, 'x'):
                p2 = QgsPointXY(end_point.x(), end_point.y())
            else:
                p2 = QgsPointXY(end_point[0], end_point[1])
            
            # Calculate position
            import math
            length = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            
            # 1/3 rule for short pipes, otherwise 6m from end
            if length <= 4.0:
                dist_from_end = length / 3.0
            else:
                dist_from_end = 4.0
                
            # Calculate marker position (using vector from end to start)
            marker_pos = self._point_along(p2, p1, dist_from_end)
            
            # --- BLOCK BASED IMPLEMENTATION ---
            block_name = "RB_DROP_MARKER"
            
            # 1. Ensure Block Exists (Robust)
            self._ensure_drop_marker_block(msp.doc, block_name=block_name)

            # 2. Insert Block Reference
            # Scale radius: DROP_CIRCLE_RADIUS * scale_factor / 2000
            sc = scale_factor / 2000.0
            scale = self.DROP_CIRCLE_RADIUS * sc
            
            msp.add_blockref(
                block_name,
                (marker_pos.x(), marker_pos.y(), 0),
                dxfattribs={
                    'xscale': scale,
                    'yscale': scale,
                    'rotation': 0,
                    'layer': layer_name,
                    'color': aci_color
                }
            )
            
            print(f"DEBUG: Added drop marker block ref ({drop_type}) at {marker_pos}")
            
        except Exception as e:
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                f"Failed to add drop marker: {e}",
                error_type="drop_marker_failed"
            )
            
    def _add_collector_depth_label(self, msp, start_point, end_point, feature_data: Dict[str, Any], layer_name: str, scale_factor: float):
        """
        Add collector depth label (h_col_p2) near downstream node.
        
        Specs:
        - Parallel to pipe
        - Below the line
        - 5m from downstream node
        - Color: Gray (same as depth/length)
        - Height: 0.6 * Node Text Height (Node Height is 2.0 * scale/1000) -> 1.2 * scale/1000
        """
        try:
            depth_val = feature_data.get('downstream_depth')
            if depth_val is None:
                return
                
            # Format value
            try:
                text = f"{float(depth_val):.2f}"
            except:
                return

            from qgis.core import QgsPointXY
            import math
            
            # Access coordinates
            if hasattr(start_point, 'x'):
                p1 = QgsPointXY(start_point.x(), start_point.y())
            else:
                p1 = QgsPointXY(start_point[0], start_point[1])
                
            if hasattr(end_point, 'x'):
                p2 = QgsPointXY(end_point.x(), end_point.y())
            else:
                p2 = QgsPointXY(end_point[0], end_point[1])
            
            # Calculate position: 5.0m from p2 towards p1
            dist_from_end = 5.0
            length = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            
            if length < dist_from_end:
                 # If pipe is too short, place at midpoint
                 marker_pos = self._point_along(p2, p1, length / 2.0)
            else:
                 marker_pos = self._point_along(p2, p1, dist_from_end)
            
            # Calculate rotation
            angle_rad = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            angle_deg = math.degrees(angle_rad)
            
            # Normalize for readability (same logic as pipe labels)
            rotation = angle_deg
            if 90 < rotation <= 270:
                rotation -= 180
            elif -270 < rotation <= -90:
                rotation += 180
                
            # Offset "Below" the line
            # "Below" depends on the reading direction.
            # We want to move perpendicular to the text direction.
            # Normal vector to text direction:
            # If text is rotated R, Up is R+90. Below is R-90.
            
            rad_text = math.radians(rotation)
            rad_below = rad_text - math.pi/2
            
            # Text Height: User requested 1.2 drawing units (approx 0.6mm at 1:2000)
            # This is very small, but explicitly valid per user conversation.
            text_height = 1.2
            
            # Offset distance: roughly 1.5 * text_height
            offset_dist = 1.5 * text_height
            
            off_x = math.cos(rad_below) * offset_dist
            off_y = math.sin(rad_below) * offset_dist
            
            final_x = marker_pos.x() + off_x
            final_y = marker_pos.y() + off_y
            
            # Color: Gray
            color_rgb = self.COLOR_DEPTH_LENGTH
            aci_color = self.get_aci_color(color_rgb)
            
            # Add TEXT entity using explicit attributes for alignment
            # For MIDDLE_CENTER: halign=1 (CENTER), valign=2 (MIDDLE)
            # 'align_point' is used for aligned text, 'insert' is ignored for aligned text usually
            msp.add_text(
                text,
                dxfattribs={
                    'layer': layer_name,
                    'height': text_height,
                    'color': aci_color,
                    'rotation': rotation,
                    'style': self.template_manager.default_text_style,
                    'halign': 1,  # CENTER
                    'valign': 2,  # MIDDLE
                    'align_point': (final_x, final_y)
                }
            )
            
            print(f"DEBUG: Added collector depth label '{text}' at {final_x}, {final_y} with height {text_height}")
            
        except Exception as e:
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                f"Failed to add collector depth label: {e}",
                error_type="label_creation_failed"
            )
    
    def _calculate_azimuth(self, pt1, pt2):
        """Calculate azimuth between two points (QEsg style)."""
        from qgis.core import QgsPointXY
        if hasattr(pt1, 'x'):
            p1 = QgsPointXY(pt1.x(), pt1.y())
        else:
            p1 = QgsPointXY(pt1[0], pt1[1])
        if hasattr(pt2, 'x'):
            p2 = QgsPointXY(pt2.x(), pt2.y())
        else:
            p2 = QgsPointXY(pt2[0], pt2[1])
        return p1.azimuth(p2)
    
    def _calculate_azimuth_from_coords(self, x1, y1, x2, y2):
        """Calculate azimuth from coordinates."""
        from qgis.core import QgsPointXY
        p1 = QgsPointXY(x1, y1)
        p2 = QgsPointXY(x2, y2)
        return p1.azimuth(p2)
    
    def _calculate_text_position(self, pt1, pt2, offset, azim):
        """Calculate text position with perpendicular offset (QEsg style)."""
        import math
        from qgis.core import QgsPointXY
        
        if hasattr(pt1, 'x'):
            x1, y1 = pt1.x(), pt1.y()
        else:
            x1, y1 = pt1[0], pt1[1]
        if hasattr(pt2, 'x'):
            x2, y2 = pt2.x(), pt2.y()
        else:
            x2, y2 = pt2[0], pt2[1]
        
        # Calculate midpoint
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        
        # Calculate perpendicular offset
        if 180 <= azim < 360:
            sign = -1 * math.copysign(1, offset)
        else:
            sign = 1 * math.copysign(1, offset)
        
        length = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        x = mx + sign * abs(offset) * (y2 - y1) / length
        y = my + sign * abs(offset) * (x1 - x2) / length
        
        return QgsPointXY(x, y)
    
    def _point_along(self, pt1, pt2, distance):
        """Calculate point along line at specified distance from pt1 (QEsg PtoAlong)."""
        import math
        from qgis.core import QgsPointXY
        
        if hasattr(pt1, 'x'):
            x1, y1 = pt1.x(), pt1.y()
        else:
            x1, y1 = pt1[0], pt1[1]
        if hasattr(pt2, 'x'):
            x2, y2 = pt2.x(), pt2.y()
        else:
            x2, y2 = pt2[0], pt2[1]
        
        length = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        x = x1 + distance/length * (x2 - x1)
        y = y1 + distance/length * (y2 - y1)
        return QgsPointXY(x, y)
    
    def _point_perpendicular(self, pt1, pt2, offset):
        """Calculate point perpendicular to line at pt1 with offset (QEsg PtoPerp)."""
        import math
        from qgis.core import QgsPointXY
        
        if hasattr(pt1, 'x'):
            x1, y1 = pt1.x(), pt1.y()
        else:
            x1, y1 = pt1[0], pt1[1]
        if hasattr(pt2, 'x'):
            x2, y2 = pt2.x(), pt2.y()
        else:
            x2, y2 = pt2[0], pt2[1]
        
        length = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        x = x1 + offset/length * (y2 - y1)
        y = y1 + offset/length * (x1 - x2)
        return QgsPointXY(x, y)
    
    def _add_manhole_data_labels(self, msp, point, feature_data: Dict[str, Any], config: ExportConfiguration):
        """Add manhole data labels with two-segment leader and left/right layout."""
        try:
            print(f"DEBUG: _add_manhole_data_labels ENTRY")
            
            sc = config.scale_factor / 2000.0
            text_height = 2.75 * sc           # Increased by another 5% (total 10% from base)
            line_spacing = 1.4 * text_height  # Increased accordingly
            gap = 0.4 * text_height           # Gap
            
            # Get manhole data
            ground_elev = feature_data.get('ground_elevation', 0)
            invert_elev = feature_data.get('invert_elevation', 0)  
            calculated_depth = ground_elev - invert_elev if ground_elev and invert_elev else 0
            node_id = feature_data.get('node_id', 'Unknown')
            
            if not (ground_elev or invert_elev):
                return
                
            # Compose strings exactly as specified
            ct_str = f"CT: {ground_elev:.3f}" if ground_elev else ""
            cf_str = f"CF: {invert_elev:.3f}" if invert_elev else ""
            # Right block: depth only, or depth + node_id if export_node_id is enabled
            if config.export_node_id and node_id != 'Unknown':
                right_str = f"{calculated_depth:.3f} - {node_id}" if calculated_depth else ""
            else:
                right_str = f"{calculated_depth:.3f}" if calculated_depth else ""
            
            print(f"DEBUG: Labels - CT: '{ct_str}', CF: '{cf_str}', Right: '{right_str}'")
            
            # Calculate text widths using 0.93 factor for accurate measurement
            char_width = text_height * 0.93  # Use 0.93 factor for precise width
            w_ct = len(ct_str) * char_width if ct_str else 0
            w_cf = len(cf_str) * char_width if cf_str else 0
            left_block_w = max(w_ct, w_cf)  # Width of widest line in left block
            
            print(f"DEBUG: Text widths - CT: {w_ct}, CF: {w_cf}, left_block_w: {left_block_w}")
            
            # Position labels (adjusted for proper alignment)
            # Increased offsets again to match new text size
            label_offset_x = 16.5 * sc - 7.82  # (was 15.75)
            label_offset_y = 4.4 * sc + 1.35   # (was 4.2)
            x_label = point[0] + label_offset_x
            y_label = point[1] + label_offset_y  # Top line baseline (CT position)
            
            from ezdxf.enums import TextEntityAlignment
            
            # Draw left block (CT and CF stacked with proper spacing)
            y_CT = y_label  # CT baseline
            y_CF = y_label - line_spacing  # CF baseline (1.2 * text_height below CT)
            
            if ct_str:
                msp.add_text(
                    ct_str,
                    height=text_height,
                    dxfattribs={
                        'rotation': 0,
                        'style': self.CAD_FONT,
                        'color': 7,
                        'layer': f"{config.layer_prefix}TEXTOPVS"
                    }
                ).set_placement((x_label, y_CT), align=TextEntityAlignment.MIDDLE_LEFT)
                print(f"DEBUG: Added CT label: {ct_str} at ({x_label}, {y_CT})")
            
            if cf_str:
                msp.add_text(
                    cf_str,
                    height=text_height,
                    dxfattribs={
                        'rotation': 0,
                        'style': self.CAD_FONT,
                        'color': 7,
                        'layer': f"{config.layer_prefix}TEXTOPVS"
                    }
                ).set_placement((x_label, y_CF), align=TextEntityAlignment.MIDDLE_LEFT)
                print(f"DEBUG: Added CF label: {cf_str} at ({x_label}, {y_CF})")
            
            # Draw right block (h - id inline) center-aligned between CT and CF
            if right_str:
                # Position at end of horizontal leader line (center between CT and CF)
                x_right = x_label + left_block_w  # Start exactly where horizontal line ends
                y_right = (y_CT + y_CF) / 2  # Center between CT and CF baselines
                
                msp.add_text(
                    right_str,
                    height=text_height,
                    dxfattribs={
                        'rotation': 0,
                        'style': self.CAD_FONT,
                        'color': self.get_aci_color(self.COLOR_DEPTH_LENGTH),
                        'layer': f"{config.layer_prefix}TEXTOPVS"
                    }
                ).set_placement((x_right, y_right), align=TextEntityAlignment.MIDDLE_LEFT)
                print(f"DEBUG: Added right block: {right_str} at ({x_right}, {y_right})")
            
            # Create two-segment leader with correct elbow positioning
            # Target point T (manhole center)
            T = (point[0], point[1], 0)
            
            # Elbow point E - inclined 30° toward label
            import math
            leader_length = 8.8 * sc # Increased by another 5%
            angle_rad = math.radians(30)  # 30° inclined segment
            E_x = point[0] + leader_length * math.cos(angle_rad)
            
            # Elbow Y = midpoint between CT and CF baselines
            elbow_y = (y_CT + y_CF) / 2
            E = (E_x, elbow_y, 0)
            
            # Landing point L - horizontal segment ends at right edge of left block
            L_x = x_label + left_block_w
            L = (L_x, elbow_y, 0)
            
            # Draw leader as polyline (3 vertices) - easier to edit in CAD
            msp.add_lwpolyline(
                [T[:2], E[:2], L[:2]],  # 2D points (x, y)
                dxfattribs={
                    'layer': f"{config.layer_prefix}LIDER",
                        'color': 7,
                }
            )
            
            print(f"DEBUG: Added polyline leader from {T} to {E} to {L}")
                
        except Exception as e:
            print(f"DEBUG: Error in _add_manhole_data_labels: {e}")
            self.error_manager.record_error(
                ErrorSeverity.WARNING,
                f"Failed to add manhole data labels: {e}",
                error_type="manhole_label_creation_failed"
            )