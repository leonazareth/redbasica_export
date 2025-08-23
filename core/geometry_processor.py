"""
Geometry processing utilities for DXF export operations.

This module provides geometric calculations and transformations needed for
sewerage network DXF export, including azimuth calculations, point generation,
and coordinate transformations.
"""

import math
from typing import Tuple, Optional, List
from qgis.core import QgsPointXY, QgsGeometry, QgsWkbTypes


class GeometryProcessor:
    """
    Utility class for geometric calculations and transformations.
    
    Provides methods for azimuth calculations, point-along-line operations,
    perpendicular point generation, and coordinate transformations needed
    for DXF export operations.
    """
    
    @staticmethod
    def calculate_azimuth(start_point: Tuple[float, float], end_point: Tuple[float, float]) -> float:
        """
        Calculate azimuth (bearing) from start point to end point in degrees.
        
        Args:
            start_point: (x, y) coordinates of start point
            end_point: (x, y) coordinates of end point
            
        Returns:
            Azimuth in degrees (0-360), where 0 is North, 90 is East
        """
        x1, y1 = start_point
        x2, y2 = end_point
        
        # Calculate differences
        dx = x2 - x1
        dy = y2 - y1
        
        # Handle zero-length line
        if dx == 0 and dy == 0:
            return 0.0
        
        # Calculate azimuth using atan2
        azimuth_rad = math.atan2(dx, dy)
        
        # Convert to degrees and normalize to 0-360
        azimuth_deg = math.degrees(azimuth_rad)
        if azimuth_deg < 0:
            azimuth_deg += 360
            
        return azimuth_deg
    
    @staticmethod
    def calculate_midpoint(start_point: Tuple[float, float], end_point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calculate midpoint between two points.
        
        Args:
            start_point: (x, y) coordinates of start point
            end_point: (x, y) coordinates of end point
            
        Returns:
            (x, y) coordinates of midpoint
        """
        x1, y1 = start_point
        x2, y2 = end_point
        
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0
        
        return (mid_x, mid_y)
    
    @staticmethod
    def point_along_line(start_point: Tuple[float, float], end_point: Tuple[float, float], 
                        distance: float) -> Tuple[float, float]:
        """
        Calculate point at specified distance along line from start point.
        
        Args:
            start_point: (x, y) coordinates of start point
            end_point: (x, y) coordinates of end point
            distance: Distance from start point (can be negative for opposite direction)
            
        Returns:
            (x, y) coordinates of point at specified distance
        """
        x1, y1 = start_point
        x2, y2 = end_point
        
        # Calculate line length
        line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Handle zero-length line
        if line_length == 0:
            return start_point
        
        # Calculate unit vector
        unit_x = (x2 - x1) / line_length
        unit_y = (y2 - y1) / line_length
        
        # Calculate point at distance
        point_x = x1 + (unit_x * distance)
        point_y = y1 + (unit_y * distance)
        
        return (point_x, point_y)
    
    @staticmethod
    def point_along_line_ratio(start_point: Tuple[float, float], end_point: Tuple[float, float], 
                              ratio: float) -> Tuple[float, float]:
        """
        Calculate point at specified ratio along line (0.0 = start, 1.0 = end).
        
        Args:
            start_point: (x, y) coordinates of start point
            end_point: (x, y) coordinates of end point
            ratio: Ratio along line (0.0 to 1.0)
            
        Returns:
            (x, y) coordinates of point at specified ratio
        """
        x1, y1 = start_point
        x2, y2 = end_point
        
        point_x = x1 + ratio * (x2 - x1)
        point_y = y1 + ratio * (y2 - y1)
        
        return (point_x, point_y)
    
    @staticmethod
    def perpendicular_point(line_start: Tuple[float, float], line_end: Tuple[float, float],
                           reference_point: Tuple[float, float], distance: float) -> Tuple[float, float]:
        """
        Generate point perpendicular to line at specified distance from reference point.
        
        Args:
            line_start: (x, y) coordinates of line start
            line_end: (x, y) coordinates of line end
            reference_point: (x, y) coordinates of reference point on or near line
            distance: Distance from reference point (positive = right side, negative = left side)
            
        Returns:
            (x, y) coordinates of perpendicular point
        """
        x1, y1 = line_start
        x2, y2 = line_end
        ref_x, ref_y = reference_point
        
        # Calculate line direction vector
        dx = x2 - x1
        dy = y2 - y1
        
        # Calculate line length
        line_length = math.sqrt(dx**2 + dy**2)
        
        # Handle zero-length line
        if line_length == 0:
            return reference_point
        
        # Calculate unit perpendicular vector (rotated 90 degrees)
        perp_x = -dy / line_length
        perp_y = dx / line_length
        
        # Calculate perpendicular point
        point_x = ref_x + (perp_x * distance)
        point_y = ref_y + (perp_y * distance)
        
        return (point_x, point_y)
    
    @staticmethod
    def calculate_text_rotation(start_point: Tuple[float, float], end_point: Tuple[float, float]) -> float:
        """
        Calculate text rotation angle for alignment with line direction.
        
        Args:
            start_point: (x, y) coordinates of line start
            end_point: (x, y) coordinates of line end
            
        Returns:
            Rotation angle in degrees for text alignment
        """
        x1, y1 = start_point
        x2, y2 = end_point
        
        # Calculate angle
        dx = x2 - x1
        dy = y2 - y1
        
        # Handle zero-length line
        if dx == 0 and dy == 0:
            return 0.0
        
        # Calculate angle in radians
        angle_rad = math.atan2(dy, dx)
        
        # Convert to degrees
        angle_deg = math.degrees(angle_rad)
        
        # Normalize to keep text readable (avoid upside-down text)
        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180
            
        return angle_deg
    
    @staticmethod
    def calculate_arrow_placement(start_point: Tuple[float, float], end_point: Tuple[float, float],
                                 scale_factor: float = 1.0, min_segment_length: float = 20.0) -> Optional[Tuple[float, float, float]]:
        """
        Calculate arrow placement for flow direction indication.
        
        Args:
            start_point: (x, y) coordinates of pipe start
            end_point: (x, y) coordinates of pipe end
            scale_factor: Scale factor for minimum segment length
            min_segment_length: Minimum segment length for arrow placement (in scale units)
            
        Returns:
            (x, y, rotation) for arrow placement, or None if segment too short
        """
        x1, y1 = start_point
        x2, y2 = end_point
        
        # Calculate segment length
        segment_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Check if segment is long enough for arrow
        min_length = min_segment_length * scale_factor
        if segment_length < min_length:
            return None
        
        # Place arrow at 75% along the segment (closer to end)
        arrow_point = GeometryProcessor.point_along_line_ratio(start_point, end_point, 0.75)
        
        # Calculate rotation for arrow direction
        rotation = GeometryProcessor.calculate_azimuth(start_point, end_point)
        
        return (arrow_point[0], arrow_point[1], rotation)
    
    @staticmethod
    def transform_coordinates(point: Tuple[float, float], translation: Tuple[float, float] = (0, 0),
                            rotation: float = 0.0, scale: float = 1.0) -> Tuple[float, float]:
        """
        Apply coordinate transformation (translation, rotation, scaling).
        
        Args:
            point: (x, y) coordinates to transform
            translation: (dx, dy) translation offset
            rotation: Rotation angle in degrees
            scale: Scale factor
            
        Returns:
            (x, y) transformed coordinates
        """
        x, y = point
        dx, dy = translation
        
        # Apply scaling
        x *= scale
        y *= scale
        
        # Apply rotation if specified
        if rotation != 0.0:
            rotation_rad = math.radians(rotation)
            cos_r = math.cos(rotation_rad)
            sin_r = math.sin(rotation_rad)
            
            x_rot = x * cos_r - y * sin_r
            y_rot = x * sin_r + y * cos_r
            
            x, y = x_rot, y_rot
        
        # Apply translation
        x += dx
        y += dy
        
        return (x, y)
    
    @staticmethod
    def calculate_line_length(start_point: Tuple[float, float], end_point: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two points.
        
        Args:
            start_point: (x, y) coordinates of start point
            end_point: (x, y) coordinates of end point
            
        Returns:
            Distance between points
        """
        x1, y1 = start_point
        x2, y2 = end_point
        
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    @staticmethod
    def extract_line_coordinates(geometry: QgsGeometry) -> List[Tuple[float, float]]:
        """
        Extract coordinate pairs from QGIS line geometry.
        
        Args:
            geometry: QGIS geometry object (LineString or MultiLineString)
            
        Returns:
            List of (x, y) coordinate tuples
        """
        coordinates = []
        
        if geometry.isNull() or geometry.isEmpty():
            return coordinates
        
        geom_type = geometry.wkbType()
        
        if geom_type == QgsWkbTypes.LineString:
            # Single LineString
            line = geometry.asPolyline()
            coordinates = [(point.x(), point.y()) for point in line]
        elif geom_type == QgsWkbTypes.MultiLineString:
            # MultiLineString - take first line
            multiline = geometry.asMultiPolyline()
            if multiline:
                line = multiline[0]
                coordinates = [(point.x(), point.y()) for point in line]
        
        return coordinates
    
    @staticmethod
    def extract_point_coordinates(geometry: QgsGeometry) -> Optional[Tuple[float, float]]:
        """
        Extract coordinates from QGIS point geometry.
        
        Args:
            geometry: QGIS geometry object (Point or MultiPoint)
            
        Returns:
            (x, y) coordinates or None if invalid
        """
        if geometry.isNull() or geometry.isEmpty():
            return None
        
        geom_type = geometry.wkbType()
        
        if geom_type == QgsWkbTypes.Point:
            # Single Point
            point = geometry.asPoint()
            return (point.x(), point.y())
        elif geom_type == QgsWkbTypes.MultiPoint:
            # MultiPoint - take first point
            multipoint = geometry.asMultiPoint()
            if multipoint:
                point = multipoint[0]
                return (point.x(), point.y())
        
        return None