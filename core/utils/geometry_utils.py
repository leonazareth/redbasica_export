# -*- coding: utf-8 -*-
"""
Geometry utilities for CAD calculations.
"""

import math
from typing import Tuple, List, Optional
from qgis.core import QgsPointXY, QgsGeometry

def normalize_angle(angle_deg: float) -> float:
    """Normalize angle to 0-360 range."""
    return angle_deg % 360

def get_cad_angle(p1: QgsPointXY, p2: QgsPointXY) -> float:
    """
    Calculate angle from p1 to p2 in degrees (CAD standard: East = 0, CCW).
    """
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    angle_rad = math.atan2(dy, dx)
    return math.degrees(angle_rad)

def get_readable_rotation(angle_deg: float) -> float:
    """
    Adjust rotation to ensure text is readable (not upside down).
    Rules: Keep text between 90 (exclusive) and 270 (inclusive) degrees inverted.
    Actually, standard drafting usually wants text readable from bottom or right.
    Standard rule:
    -90 < angle <= 90: Keep as is
    90 < angle <= 270: Rotate 180
    """
    angle = normalize_angle(angle_deg)
    if 90 < angle <= 270:
        return normalize_angle(angle + 180)
    return angle

def get_perpendicular_offset_point(
    p1: QgsPointXY, 
    p2: QgsPointXY, 
    distance: float, 
    position_t: float = 0.5,
    side: str = 'left'
) -> QgsPointXY:
    """
    Calculate a point offset perpendicularly from the line segment p1-p2.
    
    Args:
        p1: Start point
        p2: End point
        distance: Offset distance (positive)
        position_t: Position along the line (0.0 to 1.0)
        side: 'left' or 'right' relative to p1->p2 direction
        
    Returns:
        QgsPointXY: The calculated offset point
    """
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    
    # Calculate base point along the line
    base_x = p1.x() + dx * position_t
    base_y = p1.y() + dy * position_t
    
    # Normalize direction vector
    length = math.sqrt(dx*dx + dy*dy)
    if length == 0:
        return QgsPointXY(base_x, base_y)
        
    u_x = dx / length
    u_y = dy / length
    
    # Calculate perpendicular vector (-y, x) for left, (y, -x) for right
    if side == 'left':
        perp_x = -u_y
        perp_y = u_x
    else:
        perp_x = u_y
        perp_y = -u_x
        
    return QgsPointXY(
        base_x + perp_x * distance,
        base_y + perp_y * distance
    )

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))
