# -*- coding: utf-8 -*-
"""
Data conversion utilities for RedBasica Export plugin.

This module provides robust data type conversion to handle various data formats
commonly found in QGIS projects, including string representations of numbers,
NULL values, and different decimal notations.
"""

import logging
from typing import Any, Union, Optional

# Handle QGIS import gracefully for testing
try:
    from qgis.core import NULL
except ImportError:
    # Mock NULL for testing outside QGIS environment
    class MockNull:
        def __eq__(self, other):
            return isinstance(other, MockNull)
    NULL = MockNull()

logger = logging.getLogger(__name__)


class DataConverter:
    """Utility class for robust data type conversion."""
    
    @staticmethod
    def to_string(value: Any) -> str:
        """
        Convert any value to string, handling NULL/None gracefully.
        
        Args:
            value: Input value of any type
            
        Returns:
            String representation of the value, empty string for NULL/None
        """
        if value is None:
            return ""
        
        # Handle QGIS NULL values and MockNull for testing
        try:
            if value == NULL:
                return ""
        except:
            pass
        
        # Check type name for mock NULL or QGIS NULL
        if hasattr(value, '__class__') and ('Null' in value.__class__.__name__ or 'NULL' in value.__class__.__name__):
            return ""
        
        if isinstance(value, str):
            return value.strip()
        
        return str(value).strip()
    
    @staticmethod
    def to_double(value: Any) -> float:
        """
        Convert string or numeric to float, handling various formats.
        
        Handles:
        - NULL/None values (returns 0.0)
        - String representations like "1.05", "2,50" (Portuguese decimal)
        - Numeric types (int, float)
        - Invalid values (returns 0.0 with warning)
        
        Args:
            value: Input value to convert
            
        Returns:
            Float representation of the value, 0.0 for invalid/NULL values
        """
        if value is None:
            return 0.0
        
        # Handle QGIS NULL values and MockNull for testing
        try:
            if value == NULL:
                return 0.0
        except:
            pass
        
        # Check type name for mock NULL or QGIS NULL
        if hasattr(value, '__class__') and ('Null' in value.__class__.__name__ or 'NULL' in value.__class__.__name__):
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            try:
                # Handle empty strings
                cleaned = value.strip()
                if not cleaned:
                    return 0.0
                
                # Handle Portuguese decimal notation (comma to dot)
                # First check if it's a number with thousands separator
                import re
                
                # Remove currency symbols and other non-numeric prefixes
                # This handles cases like "R$ 1.234,56", "$25.50", "12.5m"
                cleaned = re.sub(r'^[^\d\-]*', '', cleaned)  # Remove non-numeric prefix
                cleaned = re.sub(r'[^\d\-\.,]*$', '', cleaned)  # Remove non-numeric suffix
                
                # Pattern for numbers like "1.234,56" (Portuguese format with thousands separator)
                portuguese_pattern = r'^(\d{1,3}(?:\.\d{3})*),(\d+)$'
                match = re.match(portuguese_pattern, cleaned)
                if match:
                    # Convert "1.234,56" to "1234.56"
                    integer_part = match.group(1).replace('.', '')
                    decimal_part = match.group(2)
                    cleaned = f"{integer_part}.{decimal_part}"
                else:
                    # Simple comma to dot replacement for cases like "12,34"
                    cleaned = cleaned.replace(',', '.')
                
                # Extract the numeric value
                numeric_match = re.search(r'-?\d*\.?\d+', cleaned)
                if numeric_match:
                    return float(numeric_match.group())
                else:
                    logger.warning(f"Could not extract numeric value from '{value}', using 0.0")
                    return 0.0
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert '{value}' to float: {e}, using 0.0")
                return 0.0
        
        # For any other type, try direct conversion
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {type(value).__name__} '{value}' to float: {e}, using 0.0")
            return 0.0
    
    @staticmethod
    def to_integer(value: Any) -> int:
        """
        Convert string or numeric to integer, handling various formats.
        
        Args:
            value: Input value to convert
            
        Returns:
            Integer representation of the value, 0 for invalid/NULL values
        """
        if value is None:
            return 0
        
        # Handle QGIS NULL values and MockNull for testing
        try:
            if value == NULL:
                return 0
        except:
            pass
        
        # Check type name for mock NULL or QGIS NULL
        if hasattr(value, '__class__') and ('Null' in value.__class__.__name__ or 'NULL' in value.__class__.__name__):
            return 0
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, float):
            return int(value)
        
        if isinstance(value, str):
            try:
                # First convert to float to handle decimal strings, then to int
                return int(DataConverter.to_double(value))
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert '{value}' to integer: {e}, using 0")
                return 0
        
        # For any other type, try conversion via float
        try:
            return int(DataConverter.to_double(value))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {type(value).__name__} '{value}' to integer: {e}, using 0")
            return 0
    
    @staticmethod
    def to_boolean(value: Any) -> bool:
        """
        Convert various representations to boolean.
        
        Args:
            value: Input value to convert
            
        Returns:
            Boolean representation of the value
        """
        if value is None:
            return False
        
        # Handle QGIS NULL values and MockNull for testing
        try:
            if value == NULL:
                return False
        except:
            pass
        
        # Check type name for mock NULL or QGIS NULL
        if hasattr(value, '__class__') and ('Null' in value.__class__.__name__ or 'NULL' in value.__class__.__name__):
            return False
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return value != 0
        
        if isinstance(value, str):
            value_lower = value.strip().lower()
            return value_lower in ('true', 'yes', 'sim', 's', '1', 'on', 'verdadeiro')
        
        # For any other type, use Python's truthiness
        return bool(value)
    
    @staticmethod
    def convert_by_type(value: Any, target_type: str) -> Any:
        """
        Convert value to specified type using appropriate converter.
        
        Args:
            value: Input value to convert
            target_type: Target type ('String', 'Double', 'Integer', 'Boolean')
            
        Returns:
            Converted value
        """
        converters = {
            'String': DataConverter.to_string,
            'Double': DataConverter.to_double,
            'Integer': DataConverter.to_integer,
            'Boolean': DataConverter.to_boolean,
        }
        
        converter = converters.get(target_type)
        if converter:
            return converter(value)
        else:
            logger.warning(f"Unknown target type '{target_type}', returning string representation")
            return DataConverter.to_string(value)
    
    @staticmethod
    def safe_divide(numerator: Any, denominator: Any, default: float = 0.0) -> float:
        """
        Safely divide two values, handling division by zero.
        
        Args:
            numerator: Numerator value
            denominator: Denominator value
            default: Default value to return if division by zero
            
        Returns:
            Result of division or default value
        """
        try:
            num = DataConverter.to_double(numerator)
            den = DataConverter.to_double(denominator)
            
            if den == 0.0:
                logger.warning(f"Division by zero: {numerator} / {denominator}, using default {default}")
                return default
            
            return num / den
            
        except Exception as e:
            logger.warning(f"Error in division {numerator} / {denominator}: {e}, using default {default}")
            return default


class CalculatedFields:
    """Utility class for calculating derived fields from mapped data."""
    
    @staticmethod
    def calculate_slope(upstream_invert: Any, downstream_invert: Any, length: Any) -> float:
        """
        Calculate pipe slope from invert elevations and length.
        
        Args:
            upstream_invert: Upstream invert elevation
            downstream_invert: Downstream invert elevation
            length: Pipe length
            
        Returns:
            Calculated slope in m/m
        """
        try:
            up_inv = DataConverter.to_double(upstream_invert)
            down_inv = DataConverter.to_double(downstream_invert)
            pipe_length = DataConverter.to_double(length)
            
            if pipe_length <= 0:
                logger.warning("Invalid pipe length for slope calculation, using default 0.001")
                return 0.001
            
            slope = (up_inv - down_inv) / pipe_length
            
            # Ensure positive slope (sewers flow downhill)
            if slope <= 0:
                logger.warning(f"Calculated negative or zero slope ({slope:.6f}), using minimum 0.0001")
                return 0.0001
            
            return slope
            
        except Exception as e:
            logger.warning(f"Error calculating slope: {e}, using default 0.001")
            return 0.001
    
    @staticmethod
    def calculate_depth(ground_elevation: Any, invert_elevation: Any) -> float:
        """
        Calculate depth from ground and invert elevations.
        
        Args:
            ground_elevation: Ground surface elevation
            invert_elevation: Invert elevation
            
        Returns:
            Calculated depth in meters
        """
        try:
            ground = DataConverter.to_double(ground_elevation)
            invert = DataConverter.to_double(invert_elevation)
            
            depth = ground - invert
            
            # Ensure positive depth
            if depth < 0:
                logger.warning(f"Calculated negative depth ({depth:.3f}), using 0.0")
                return 0.0
            
            return depth
            
        except Exception as e:
            logger.warning(f"Error calculating depth: {e}, using 0.0")
            return 0.0