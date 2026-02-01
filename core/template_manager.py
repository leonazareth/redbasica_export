"""
Template management system for DXF export operations.

This module handles DXF template discovery, validation, loading, and default
template creation. It manages block libraries and standard layer definitions
for QEsg-compatible DXF output.
"""

import os
import sys
from typing import Optional, Dict, List, Tuple
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


class TemplateManager:
    """
    Manages DXF templates and standard block definitions.
    
    Handles template discovery, validation, loading, and creation of default
    templates when needed. Provides block library management for arrows and
    manhole data blocks.
    """
    
    # Standard QEsg-compatible layer definitions
    LAYER_DEFINITIONS = [
        ('REDE', 5, 'Sewage pipes/network'),             # Main pipe network - BLUE
        ('NUMERO', 7, 'Pipe ID labels'),                 # Pipe identification numbers - WHITE
        ('TEXTO', 7, 'Pipe data labels'),                # Length-diameter-slope labels - WHITE
        ('TEXTOPVS', 1, 'Manhole elevation data'),       # Manhole elevation blocks - RED
        ('PV', 1, 'Manholes/junctions'),                 # Manhole symbols (circles) - RED
        ('NUMPV', 1, 'Manhole ID labels'),               # Manhole identification - RED
        ('SETA', 7, 'Flow direction arrows'),            # Flow direction indicators - WHITE
        ('NO', 3, 'Dry point symbols'),                  # Perpendicular lines for dry points
        ('AUX', 241, 'Auxiliary elements'),              # Helper geometry
        ('LIDER', 2, 'Leader lines'),                    # Connection lines
        ('ESG_TQ', 256, 'Drop tube symbols'),            # Special TQ (Tubo de Queda) symbols
    ]
    
    # Standard block definitions for manhole data
    MANHOLE_BLOCKS = [
        'pv_dados_NE',  # Northeast manhole data block
        'pv_dados_NO',  # Northwest manhole data block
        'pv_dados_SE',  # Southeast manhole data block
        'pv_dados_SO',  # Southwest manhole data block
        'tr_curto',     # Short transition block
        'notq',         # Special notation block
    ]
    
    # Arrow block definition
    ARROW_BLOCK = 'SETA'
    
    def __init__(self):
        """Initialize template manager."""
        self.bundled_template_path = self._get_bundled_template_path()
        self.default_text_style = 'ROMANS'
        
    def _get_bundled_template_path(self) -> Optional[str]:
        """
        Get path to bundled QEsg template.
        
        Returns:
            Path to bundled template or None if not found
        """
        # Get plugin directory
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(plugin_dir, 'resources', 'templates', 'QEsg_template.dxf')
        
        if os.path.exists(template_path):
            return template_path
        return None
    
    def discover_templates(self, search_paths: List[str] = None) -> List[str]:
        """
        Discover available DXF templates in specified paths.
        
        Args:
            search_paths: List of directories to search for templates
            
        Returns:
            List of discovered template file paths
        """
        templates = []
        
        # Default search paths
        if search_paths is None:
            search_paths = []
            
        # Always include bundled template if available
        if self.bundled_template_path:
            templates.append(self.bundled_template_path)
        
        # Search additional paths
        for search_path in search_paths:
            if os.path.exists(search_path):
                for file_name in os.listdir(search_path):
                    if file_name.lower().endswith('.dxf'):
                        full_path = os.path.join(search_path, file_name)
                        if full_path not in templates:
                            templates.append(full_path)
        
        return templates
    
    def validate_template(self, template_path: str) -> Tuple[bool, List[str]]:
        """
        Validate DXF template file.
        
        Args:
            template_path: Path to template file
            
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        
        # Check file existence
        if not os.path.exists(template_path):
            errors.append(f"Template file not found: {template_path}")
            return False, errors
        
        # Check file readability
        if not os.access(template_path, os.R_OK):
            errors.append(f"Template file not readable: {template_path}")
            return False, errors
        
        # Try to load with ezdxf
        try:
            doc = ezdxf.readfile(template_path)
            
            # Check for required blocks (optional - template can work without them)
            missing_blocks = []
            for block_name in self.MANHOLE_BLOCKS + [self.ARROW_BLOCK]:
                if block_name not in doc.blocks:
                    missing_blocks.append(block_name)
            
            if missing_blocks:
                errors.append(f"Template missing recommended blocks: {', '.join(missing_blocks)}")
            
            # Check DXF version compatibility
            dxf_version = doc.dxfversion
            if dxf_version < 'AC1015':  # AutoCAD 2000 or later
                errors.append(f"Template DXF version {dxf_version} may not be compatible")
            
        except Exception as e:
            errors.append(f"Failed to load template: {str(e)}")
            return False, errors
        
        # Template is valid (warnings don't make it invalid)
        return True, errors
    
    def load_template(self, template_path: Optional[str] = None) -> ezdxf.document.Drawing:
        """
        Load DXF template or create default if not available.
        
        Args:
            template_path: Path to template file (uses bundled if None)
            
        Returns:
            ezdxf Drawing document
        """
        # Use bundled template if no path specified
        if template_path is None:
            template_path = self.bundled_template_path
        
        # Try to load specified template
        if template_path and os.path.exists(template_path):
            try:
                doc = ezdxf.readfile(template_path)
                # Ensure required layers exist
                self._ensure_standard_layers(doc)
                return doc
            except Exception as e:
                # Fall back to default template
                pass
        
        # Create default template
        return self._create_default_template()
    
    def _create_default_template(self) -> ezdxf.document.Drawing:
        """
        Create default DXF template with standard layers and blocks.
        
        Returns:
            ezdxf Drawing document with default setup
        """
        # Create new DXF document - setup=True creates MLEADERSTYLE for MULTILEADER support
        doc = ezdxf.new('R2018', setup=True)
        
        # Set up units (meters)
        doc.units = units.M
        
        # Create standard layers
        self._ensure_standard_layers(doc)
        
        # Create standard text style
        self._create_text_styles(doc)
        
        # Create standard blocks
        self._create_standard_blocks(doc)
        
        return doc
    
    def _ensure_standard_layers(self, doc: ezdxf.document.Drawing, layer_prefix: str = "") -> None:
        """
        Ensure standard layers exist in document.
        
        Args:
            doc: ezdxf Drawing document
            layer_prefix: Optional prefix for layer names
        """
        for layer_name, color, description in self.LAYER_DEFINITIONS:
            full_layer_name = f"{layer_prefix}{layer_name}" if layer_prefix else layer_name
            
            if full_layer_name not in doc.layers:
                doc.layers.new(
                    name=full_layer_name,
                    dxfattribs={
                        'color': color,
                        'description': description
                    }
                )
    
    def _create_text_styles(self, doc: ezdxf.document.Drawing) -> None:
        """
        Create standard text styles.
        
        Args:
            doc: ezdxf Drawing document
        """
        # Create ROMANS text style if it doesn't exist
        if self.default_text_style not in doc.styles:
            doc.styles.new(
                name=self.default_text_style,
                dxfattribs={
                    'font': 'romans.shx',
                    'width': 1.0,
                    'height': 0.0,  # Variable height
                }
            )
    
    def _create_standard_blocks(self, doc: ezdxf.document.Drawing) -> None:
        """
        Create standard block definitions.
        
        Args:
            doc: ezdxf Drawing document
        """
        # Create arrow block (SETA)
        if self.ARROW_BLOCK not in doc.blocks:
            self._create_arrow_block(doc)
        
        # Create manhole data blocks
        for block_name in self.MANHOLE_BLOCKS:
            if block_name not in doc.blocks:
                self._create_manhole_block(doc, block_name)
    
    def _create_arrow_block(self, doc: ezdxf.document.Drawing) -> None:
        """
        Create arrow block for flow direction indication.
        
        Args:
            doc: ezdxf Drawing document
        """
        block = doc.blocks.new(name=self.ARROW_BLOCK)
        
        # Create simple arrow shape (triangle)
        # Arrow points in positive X direction
        arrow_points = [
            (0.0, 0.0),      # Arrow tip
            (-1.0, 0.3),     # Upper back
            (-0.7, 0.0),     # Back center
            (-1.0, -0.3),    # Lower back
            (0.0, 0.0)       # Close to tip
        ]
        
        # Add arrow as polyline
        block.add_lwpolyline(
            points=arrow_points,
            close=True,
            dxfattribs={'color': 256}  # ByLayer color
        )
    
    def _create_manhole_block(self, doc: ezdxf.document.Drawing, block_name: str) -> None:
        """
        Create manhole data block.
        
        Args:
            doc: ezdxf Drawing document
            block_name: Name of block to create
        """
        block = doc.blocks.new(name=block_name)
        
        # Create simple text placeholder for manhole data
        # Real implementation would have more complex geometry
        block.add_text(
            text="CT: {CT}\nCF: {CF}\nPROF: {PROF}",
            dxfattribs={
                'style': self.default_text_style,
                'height': 1.0,
                'color': 256,  # ByLayer color
                'halign': TextEntityAlignment.CENTER,
                'valign': TextEntityAlignment.MIDDLE
            }
        )
        
        # Add frame rectangle
        block.add_lwpolyline(
            points=[(-1.5, -1.0), (1.5, -1.0), (1.5, 1.0), (-1.5, 1.0)],
            close=True,
            dxfattribs={'color': 256}
        )
    
    def get_block_names(self, doc: ezdxf.document.Drawing) -> List[str]:
        """
        Get list of available block names in document.
        
        Args:
            doc: ezdxf Drawing document
            
        Returns:
            List of block names
        """
        return list(doc.blocks.keys())
    
    def has_required_blocks(self, doc: ezdxf.document.Drawing) -> Tuple[bool, List[str]]:
        """
        Check if document has required blocks.
        
        Args:
            doc: ezdxf Drawing document
            
        Returns:
            (has_all_blocks, missing_blocks) tuple
        """
        missing_blocks = []
        
        # Check for arrow block
        if self.ARROW_BLOCK not in doc.blocks:
            missing_blocks.append(self.ARROW_BLOCK)
        
        # Check for manhole blocks
        for block_name in self.MANHOLE_BLOCKS:
            if block_name not in doc.blocks:
                missing_blocks.append(block_name)
        
        return len(missing_blocks) == 0, missing_blocks
    
    def create_layers_with_prefix(self, doc: ezdxf.document.Drawing, prefix: str) -> None:
        """
        Create standard layers with specified prefix.
        
        Args:
            doc: ezdxf Drawing document
            prefix: Prefix to add to layer names
        """
        self._ensure_standard_layers(doc, prefix)
    
    def get_layer_name(self, base_name: str, prefix: str = "") -> str:
        """
        Get full layer name with prefix.
        
        Args:
            base_name: Base layer name
            prefix: Optional prefix
            
        Returns:
            Full layer name
        """
        return f"{prefix}{base_name}" if prefix else base_name
    
    def setup_document_properties(self, doc: ezdxf.document.Drawing) -> None:
        """
        Set up document properties and variables.
        
        Args:
            doc: ezdxf Drawing document
        """
        # Set drawing units to meters
        doc.units = units.M
        
        # Set up header variables
        doc.header['$INSUNITS'] = 6  # Meters
        doc.header['$MEASUREMENT'] = 1  # Metric
        
        # Set up application ID for extended data
        if 'REDBASICA_EXPORT' not in doc.appids:
            doc.appids.new('REDBASICA_EXPORT')