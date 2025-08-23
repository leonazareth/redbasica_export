# -*- coding: utf-8 -*-
"""
Core package for RedBasica Export plugin.

This package contains the core business logic including layer management,
attribute mapping, DXF export engine, and data processing utilities.
"""

# Import core classes for easy access
from .data_structures import (
    GeometryType, FieldType, RequiredField, LayerMapping, ExportConfiguration
)
from .field_definitions import SewageNetworkFields
from .data_converter import DataConverter, CalculatedFields
from .configuration import Configuration
from .layer_manager import LayerManager
from .attribute_mapper import AttributeMapper

__all__ = [
    'GeometryType', 'FieldType', 'RequiredField', 'LayerMapping', 'ExportConfiguration',
    'SewageNetworkFields', 'DataConverter', 'CalculatedFields', 'Configuration',
    'LayerManager', 'AttributeMapper'
]