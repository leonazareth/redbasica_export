"""
Collapsible GroupBox Widget for PyQt5

A QGroupBox-like widget that can be collapsed/expanded by clicking on its title.
"""

from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QToolButton, QFrame, QSizePolicy
from qgis.PyQt.QtCore import Qt, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation


class CollapsibleGroupBox(QWidget):
    """
    A collapsible group box widget with an arrow toggle button.
    
    When collapsed, only the title bar is visible.
    When expanded, the content is shown below the title.
    """
    
    def __init__(self, title: str = "", parent=None, collapsed: bool = True):
        """
        Initialize the collapsible group box.
        
        Args:
            title: The title to display
            parent: Parent widget
            collapsed: Whether to start collapsed (default: True)
        """
        super().__init__(parent)
        
        self._is_collapsed = collapsed
        self._animation_duration = 150
        
        # Create the toggle button (acts as title bar)
        self.toggle_button = QToolButton()
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                font-weight: bold;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(not collapsed)
        self._update_arrow()
        self.toggle_button.clicked.connect(self._on_toggle)
        
        # Create a horizontal line separator
        self.header_line = QFrame()
        self.header_line.setFrameShape(QFrame.HLine)
        self.header_line.setFrameShadow(QFrame.Sunken)
        
        # Create the content area
        self.content_area = QWidget()
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 5, 0, 5)
        self.content_layout.setSpacing(5)
        
        # Set initial visibility
        self.content_area.setVisible(not collapsed)
        self.content_area.setMaximumHeight(0 if collapsed else 16777215)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.header_line)
        main_layout.addWidget(self.content_area)
    
    def _update_arrow(self):
        """Update the arrow icon based on collapsed state."""
        if self._is_collapsed:
            self.toggle_button.setArrowType(Qt.RightArrow)
        else:
            self.toggle_button.setArrowType(Qt.DownArrow)
    
    def _on_toggle(self):
        """Handle toggle button click."""
        self._is_collapsed = not self._is_collapsed
        self._update_arrow()
        self.toggle_button.setChecked(not self._is_collapsed)
        
        if self._is_collapsed:
            self.content_area.setMaximumHeight(0)
            self.content_area.setVisible(False)
        else:
            self.content_area.setVisible(True)
            self.content_area.setMaximumHeight(16777215)
    
    def addWidget(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)
    
    def addLayout(self, layout):
        """Add a layout to the content area."""
        self.content_layout.addLayout(layout)
    
    def setTitle(self, title: str):
        """Set the title text."""
        self.toggle_button.setText(title)
    
    def isCollapsed(self) -> bool:
        """Return whether the group box is collapsed."""
        return self._is_collapsed
    
    def setCollapsed(self, collapsed: bool):
        """Set the collapsed state."""
        if collapsed != self._is_collapsed:
            self._on_toggle()
    
    def expand(self):
        """Expand the group box."""
        self.setCollapsed(False)
    
    def collapse(self):
        """Collapse the group box."""
        self.setCollapsed(True)
