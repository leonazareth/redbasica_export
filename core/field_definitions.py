# -*- coding: utf-8 -*-
"""
Field definitions for sewerage network export.

This module defines the required and optional fields for pipes and junctions
in a sewerage network, providing flexibility while maintaining compatibility
with standard sewerage design practices.
"""

from typing import List, Optional, Dict
from .data_structures import RequiredField, FieldType
from .i18n_manager import tr


class SewageNetworkFields:
    """Standard field definitions for sewerage network components."""
    
    @classmethod
    def get_pipes_required_fields(cls) -> List[RequiredField]:
        """Get localized required fields for pipe segments."""
        return [
            RequiredField(
                name="pipe_id",
                display_name=tr("Pipe Identifier"),
                field_type=FieldType.STRING,
                description=tr("Unique identifier for each pipe segment"),
                default_value="",
                is_required=True,
                validation_rules={"max_length": 50}
            ),
            RequiredField(
                name="upstream_node",
                display_name=tr("Upstream Node"),
                field_type=FieldType.STRING,
                description=tr("Identifier of upstream manhole or junction"),
                default_value="",
                is_required=True,
                validation_rules={"max_length": 50}
            ),
            RequiredField(
                name="downstream_node",
                display_name=tr("Downstream Node"),
                field_type=FieldType.STRING,
                description=tr("Identifier of downstream manhole or junction"),
                default_value="",
                is_required=True,
                validation_rules={"max_length": 50}
            ),
            RequiredField(
                name="length",
                display_name=tr("Length"),
                field_type=FieldType.DOUBLE,
                description=tr("Pipe length in meters"),
                default_value=0.0,
                is_required=True,
                validation_rules={"min_value": 0.01, "max_value": 10000.0}
            ),
            RequiredField(
                name="diameter",
                display_name=tr("Diameter"),
                field_type=FieldType.DOUBLE,
                description=tr("Pipe diameter in millimeters"),
                default_value=150.0,
                is_required=True,
                validation_rules={"min_value": 50.0, "max_value": 3000.0}
            ),
            # Note: upstream_invert_elev and downstream_invert_elev moved to optional
            # They come from the nodes layer, not directly from pipes
        ]
    
    @classmethod
    def get_pipes_optional_fields(cls) -> List[RequiredField]:
        """Get localized optional fields for pipe segments."""
        return [
            RequiredField(
                name="upstream_invert_elev",
                display_name=tr("Upstream Invert Elevation"),
                field_type=FieldType.DOUBLE,
                description=tr("Upstream invert elevation (cota de fundo) in meters - from nodes layer"),
                default_value=0.0,
                is_required=False,
                validation_rules={"min_value": -100.0, "max_value": 5000.0}
            ),
            RequiredField(
                name="downstream_invert_elev",
                display_name=tr("Downstream Invert Elevation"),
                field_type=FieldType.DOUBLE,
                description=tr("Downstream invert elevation (cota de fundo) in meters - from nodes layer"),
                default_value=0.0,
                is_required=False,
                validation_rules={"min_value": -100.0, "max_value": 5000.0}
            ),
            RequiredField(
                name="upstream_ground_elev",
                display_name=tr("Upstream Ground Elevation"),
                field_type=FieldType.DOUBLE,
                description=tr("Upstream ground surface elevation in meters - from nodes layer"),
                default_value=0.0,
                is_required=False,
                validation_rules={"min_value": -100.0, "max_value": 5000.0}
            ),
            RequiredField(
                name="downstream_ground_elev",
                display_name=tr("Downstream Ground Elevation"),
                field_type=FieldType.DOUBLE,
                description=tr("Downstream ground surface elevation in meters - from nodes layer"),
                default_value=0.0,
                is_required=False,
                validation_rules={"min_value": -100.0, "max_value": 5000.0}
            ),
            RequiredField(
                name="slope",
                display_name=tr("Slope"),
                field_type=FieldType.DOUBLE,
                description=tr("Pipe slope in meters per meter (m/m)"),
                default_value=0.001,
                is_required=False,
                validation_rules={"min_value": 0.0001, "max_value": 1.0}
            ),
            RequiredField(
                name="material",
                display_name=tr("Material"),
                field_type=FieldType.STRING,
                description=tr("Pipe material (e.g., PVC, concrete, etc.)"),
                default_value="PVC",
                is_required=False,
                validation_rules={"max_length": 30}
            ),
            RequiredField(
                name="notes",
                display_name=tr("Notes"),
                field_type=FieldType.STRING,
                description=tr("Additional notes or observations"),
                default_value="",
                is_required=False,
                validation_rules={"max_length": 255}
            ),
            RequiredField(
                name="downstream_depth",
                display_name=tr("Collector Depth"),
                field_type=FieldType.DOUBLE,
                description=tr("Depth of the collector pipe at the downstream node (h_col_p2)"),
                default_value=None,
                is_required=False
            ),
            RequiredField(
                name="drop_type",
                display_name=tr("Drop Type"),
                field_type=FieldType.STRING,
                description=tr("Drop type: 'D' (Degrau) or 'TC' (Tubo de Queda)"),
                default_value="",
                is_required=False,
                validation_rules={"max_length": 10}
            ),
            RequiredField(
                name="drop_height",
                display_name=tr("Drop Height"),
                field_type=FieldType.DOUBLE,
                description=tr("Height of the drop or drop pipe"),
                default_value=0.0,
                is_required=False,
                validation_rules={"min_value": 0.0, "max_value": 100.0}
            ),
        ]
    
    @classmethod
    def get_junctions_required_fields(cls) -> List[RequiredField]:
        """Get localized required fields for junctions/manholes."""
        return [
            RequiredField(
                name="node_id",
                display_name=tr("Node Identifier"),
                field_type=FieldType.STRING,
                description=tr("Unique identifier for each junction or manhole"),
                default_value="",
                is_required=True,
                validation_rules={"max_length": 50}
            ),
            RequiredField(
                name="ground_elevation",
                display_name=tr("Ground Elevation (CT)"),
                field_type=FieldType.DOUBLE,
                description=tr("Ground surface elevation at junction in meters (Cota do Terreno)"),
                default_value=0.0,
                is_required=True,
                validation_rules={"min_value": -100.0, "max_value": 5000.0}
            ),
            RequiredField(
                name="invert_elevation",
                display_name=tr("Invert Elevation (CF)"),
                field_type=FieldType.DOUBLE,
                description=tr("Junction invert elevation in meters (Cota de Fundo)"),
                default_value=0.0,
                is_required=True,
                validation_rules={"min_value": -100.0, "max_value": 5000.0}
            ),
        ]
    
    @classmethod
    def get_junctions_optional_fields(cls) -> List[RequiredField]:
        """Get localized optional fields for junctions/manholes."""
        return [
            # Note: depth is now calculated automatically from ground_elevation - invert_elevation
            RequiredField(
                name="notes",
                display_name=tr("Notes"),
                field_type=FieldType.STRING,
                description=tr("Additional notes or observations"),
                default_value="",
                is_required=False,
                validation_rules={"max_length": 255}
            ),
        ]
    
    @classmethod
    def get_calculated_fields(cls) -> List[RequiredField]:
        """Get localized calculated fields."""
        return [
            RequiredField(
                name="upstream_depth",
                display_name=tr("Upstream Depth"),
                field_type=FieldType.DOUBLE,
                description=tr("Calculated depth at upstream end (ground - invert)"),
                default_value=0.0,
                is_calculated=True,
                is_required=False,
                calculation_dependencies=["upstream_ground", "upstream_invert"],
                validation_rules={"min_value": 0.0, "max_value": 50.0}
            ),
            RequiredField(
                name="downstream_depth",
                display_name=tr("Downstream Depth"),
                field_type=FieldType.DOUBLE,
                description=tr("Calculated depth at downstream end (ground - invert)"),
                default_value=0.0,
                is_calculated=True,
                is_required=False,
                calculation_dependencies=["downstream_ground", "downstream_invert"],
                validation_rules={"min_value": 0.0, "max_value": 50.0}
            ),
            RequiredField(
                name="calculated_slope",
                display_name=tr("Calculated Slope"),
                field_type=FieldType.DOUBLE,
                description=tr("Calculated slope from elevation difference and length"),
                default_value=0.001,
                is_calculated=True,
                is_required=False,
                calculation_dependencies=["upstream_invert", "downstream_invert", "length"],
                validation_rules={"min_value": 0.0001, "max_value": 1.0}
            ),
            RequiredField(
                name="junction_depth",
                display_name=tr("Junction Depth"),
                field_type=FieldType.DOUBLE,
                description=tr("Junction depth calculated from ground and invert elevations"),
                default_value=0.0,
                is_calculated=True,
                is_required=False,
                calculation_dependencies=["ground_elevation", "invert_elevation"],
                validation_rules={"min_value": 0.0, "max_value": 50.0}
            ),
        ]
    
    # Legacy properties for backward compatibility
    @property
    def PIPES_REQUIRED(self) -> List[RequiredField]:
        return self.get_pipes_required_fields()
    
    @property
    def PIPES_OPTIONAL(self) -> List[RequiredField]:
        return self.get_pipes_optional_fields()
    
    @property
    def JUNCTIONS_REQUIRED(self) -> List[RequiredField]:
        return self.get_junctions_required_fields()
    
    @property
    def JUNCTIONS_OPTIONAL(self) -> List[RequiredField]:
        return self.get_junctions_optional_fields()
    
    @property
    def CALCULATED_FIELDS(self) -> List[RequiredField]:
        return self.get_calculated_fields()
    
    @classmethod
    def get_all_pipe_fields(cls) -> List[RequiredField]:
        """Get all pipe fields (required + optional + calculated)."""
        return cls.get_pipes_required_fields() + cls.get_pipes_optional_fields() + cls.get_calculated_fields()
    
    @classmethod
    def get_all_junction_fields(cls) -> List[RequiredField]:
        """Get all junction fields (required + optional)."""
        return cls.get_junctions_required_fields() + cls.get_junctions_optional_fields()
    
    @classmethod
    def get_field_by_name(cls, field_name: str) -> Optional[RequiredField]:
        """Get a field definition by its name."""
        all_fields = cls.get_all_pipe_fields() + cls.get_all_junction_fields()
        for field_def in all_fields:
            if field_def.name == field_name:
                return field_def
        return None
    
    @classmethod
    def get_required_pipe_fields(cls) -> List[str]:
        """Get list of required pipe field names."""
        return [field.name for field in cls.get_pipes_required_fields()]
    
    @classmethod
    def get_required_junction_fields(cls) -> List[str]:
        """Get list of required junction field names."""
        return [field.name for field in cls.get_junctions_required_fields()]
    
    @classmethod
    def get_calculated_field_dependencies(cls, field_name: str) -> List[str]:
        """Get the dependencies for a calculated field."""
        field_def = cls.get_field_by_name(field_name)
        if field_def and field_def.is_calculated:
            return field_def.calculation_dependencies
        return []
    
    @classmethod
    def can_calculate_field(cls, field_name: str, available_fields: List[str]) -> bool:
        """Check if a calculated field can be computed with available fields."""
        dependencies = cls.get_calculated_field_dependencies(field_name)
        return all(dep in available_fields for dep in dependencies)
    
    @classmethod
    def get_field_suggestions(cls) -> Dict[str, List[str]]:
        """Get common field name patterns for auto-mapping suggestions."""
        return {
            # Pipe fields - including QEsg patterns as suggestions (not requirements)
            "pipe_id": ["ID_TRM_(N)", "pipe_id", "trecho_id", "Rede"],
            "upstream_node": ["node_up_id", "PVM", "node_upstream", "nos_montante"],
            "downstream_node": ["node_down_id", "PVJ", "node_downstream", "nos_jusante"],
            "length": ["L", "length", "comprimento", "len", "distance", "extensao", "dist", "comp"],
            "diameter": ["DN", "diameter", "diam", "dn", "size", "diametro", "bitola", "calibre"],
            
            # Additional optional fields
            "downstream_depth": ["h_col_p2", "prof_montante_p2", "h_chegada"],
            
            # Fields that come from node assignment
            "upstream_invert_elev": ["node_up_invert_elev", "CF_nodo_p1", "cf_montante", "invert_up"],
            "downstream_invert_elev": ["node_down_invert_elev", "CF_nodo_p2", "cf_jusante", "invert_down"],
            "upstream_ground_elev": ["node_up_ground_elev", "CT_(N)_p1", "ct_montante", "ground_up"],
            "downstream_ground_elev": ["node_down_ground_elev", "CT_(N)_p2", "ct_jusante", "ground_down"],
            
            # Drop / Drop Pipe fields
            "drop_type": ["Caida_p2", "tipo_queda", "degrau", "drop_type"],
            "drop_height": ["Caida_p2_h", "altura_queda", "degrau_h", "drop_height"],
            
            "slope": ["S", "slope", "declividade", "inclinacao", "Declivity"],
            "material": ["Mat_col", "material", "mat"],
            "notes": [],
            
            # Junction fields
            "node_id": ["Id_NODO_(n", "node_id", "id_no", "pv_id", "manhole_id"],
            "ground_elevation": ["CT_(N)", "elev_ground", "cota_terreno", "ct", "ground_elev"],
            "invert_elevation": ["CF_nodo", "elev_invert", "cota_fundo", "cf", "invert_elev"],
        }
    
    @classmethod
    def suggest_field_mapping(cls, layer_fields: List[str], geometry_type: str) -> Dict[str, List[str]]:
        """
        Suggest field mappings based on layer field names.
        
        Args:
            layer_fields: List of available field names in the layer
            geometry_type: 'pipes' or 'junctions'
            
        Returns:
            Dictionary mapping required_field -> [suggested_layer_fields]
        """
        suggestions = cls.get_field_suggestions()
        suggested_mappings = {}
        
        # Normalize layer field names for comparison
        normalized_layer_fields = {field.lower(): field for field in layer_fields}
        
        # Get relevant field suggestions based on geometry type
        if geometry_type == 'pipes':
            relevant_fields = [field.name for field in cls.get_all_pipe_fields()]
        else:
            relevant_fields = [field.name for field in cls.get_all_junction_fields()]
        
        for required_field in relevant_fields:
            if required_field in suggestions:
                matches = []
                for pattern in suggestions[required_field]:
                    pattern_lower = pattern.lower()
                    # Exact match
                    if pattern_lower in normalized_layer_fields:
                        matches.append(normalized_layer_fields[pattern_lower])
                    # Partial match (contains pattern)
                    else:
                        for norm_field, orig_field in normalized_layer_fields.items():
                            if pattern_lower in norm_field or norm_field in pattern_lower:
                                if orig_field not in matches:
                                    matches.append(orig_field)
                
                if matches:
                    suggested_mappings[required_field] = matches[:3]  # Limit to top 3 suggestions
        
        return suggested_mappings