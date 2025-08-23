"""
Layer Selector Dialog for Flexible Sewerage Network DXF Export Plugin

This dialog provides layer selection with filtering, preview capabilities,
and validation feedback for any project layers.
"""

import os
from typing import Dict, List, Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QListWidget, QListWidgetItem, QTableWidget, 
    QTableWidgetItem, QLabel, QComboBox, QPushButton,
    QHeaderView, QAbstractItemView
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsWkbTypes, QgsField, QgsFeature
)

from ..core.layer_manager import LayerManager
from ..core.data_structures import GeometryType
from ..core.i18n_manager import tr

# Load UI file
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'layer_selector_dialog.ui'))


class LayerSelectorDialog(QDialog, FORM_CLASS):
    """
    Dialog for selecting layers with filtering and preview capabilities.
    
    Features:
    - Geometry type filtering
    - Layer information display
    - Field list with types
    - Sample data preview
    - Layer validation status
    """
    
    # Signals
    layer_selected = pyqtSignal(QgsVectorLayer)  # Emitted when layer is selected
    
    def __init__(self, layer_manager: LayerManager, parent=None):
        """
        Initialize the layer selector dialog.
        
        Args:
            layer_manager: LayerManager instance for layer operations
            parent: Parent widget
        """
        super(LayerSelectorDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.layer_manager = layer_manager
        self.selected_layer = None
        self.geometry_filter = None
        
        self._setup_ui()
        self._connect_signals()
        self._refresh_layers()
    
    def _setup_ui(self):
        """Set up UI components."""
        # Configure tables
        self._setup_fields_table()
        self._setup_sample_data_table()
        
        # Set initial states
        self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
        
        # Set splitter proportions
        self.splitter.setSizes([250, 450])
    
    def _setup_fields_table(self):
        """Configure the fields table widget."""
        self.fieldsTableWidget.setColumnCount(3)
        self.fieldsTableWidget.setHorizontalHeaderLabels(['Field Name', 'Type', 'Length'])
        
        # Set column widths
        header = self.fieldsTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Set selection behavior
        self.fieldsTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
    
    def _setup_sample_data_table(self):
        """Configure the sample data table widget."""
        # Will be configured dynamically based on selected layer
        self.sampleDataTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Geometry type filter
        self.geometryTypeCombo.currentTextChanged.connect(self._on_geometry_filter_changed)
        
        # Refresh button
        self.refreshButton.clicked.connect(self._refresh_layers)
        
        # Layer selection
        self.layerListWidget.itemSelectionChanged.connect(self._on_layer_selection_changed)
        self.layerListWidget.itemDoubleClicked.connect(self._on_layer_double_clicked)
    
    def _on_geometry_filter_changed(self, filter_text: str):
        """Handle geometry type filter change."""
        filter_map = {
            'All Layers': None,
            'Point Layers (Junctions/Manholes)': GeometryType.POINT,
            'Line Layers (Pipes/Conduits)': GeometryType.LINE,
            'Polygon Layers': GeometryType.POLYGON
        }
        
        self.geometry_filter = filter_map.get(filter_text)
        self._refresh_layers()
    
    def _refresh_layers(self):
        """Refresh the layer list based on current filter."""
        self.layerListWidget.clear()
        
        # Get available layers
        layers = self.layer_manager.get_available_layers(self.geometry_filter)
        
        for layer in layers:
            item = QListWidgetItem(layer.name())
            item.setData(Qt.UserRole, layer)
            
            # Add geometry type info to display
            geom_type = self._get_geometry_type_name(layer.geometryType())
            item.setText(f"{layer.name()} ({geom_type})")
            
            # Add tooltip with layer info
            tooltip = f"Layer: {layer.name()}\\nGeometry: {geom_type}\\nFeatures: {layer.featureCount()}"
            item.setToolTip(tooltip)
            
            self.layerListWidget.addItem(item)
        
        # Clear layer info if no layers
        if not layers:
            self._clear_layer_info()
            self.layerNameLabel.setText("No layers match the current filter")
    
    def _get_geometry_type_name(self, geometry_type) -> str:
        """Get human-readable geometry type name."""
        type_map = {
            QgsWkbTypes.PointGeometry: "Point",
            QgsWkbTypes.LineGeometry: "Line", 
            QgsWkbTypes.PolygonGeometry: "Polygon",
            QgsWkbTypes.UnknownGeometry: "Unknown",
            QgsWkbTypes.NullGeometry: "None"
        }
        return type_map.get(geometry_type, "Unknown")
    
    def _on_layer_selection_changed(self):
        """Handle layer selection change."""
        selected_items = self.layerListWidget.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            layer = item.data(Qt.UserRole)
            self._display_layer_info(layer)
            self.selected_layer = layer
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(True)
        else:
            self._clear_layer_info()
            self.selected_layer = None
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
    
    def _on_layer_double_clicked(self, item: QListWidgetItem):
        """Handle layer double-click (accept selection)."""
        layer = item.data(Qt.UserRole)
        if layer:
            self.selected_layer = layer
            self.accept()
    
    def _display_layer_info(self, layer: QgsVectorLayer):
        """Display detailed information for the selected layer."""
        if not layer:
            self._clear_layer_info()
            return
        
        # Update layer name
        self.layerNameLabel.setText(f"<b>{layer.name()}</b>")
        
        # Update layer details
        self.geometryTypeValueLabel.setText(self._get_geometry_type_name(layer.geometryType()))
        self.featureCountValueLabel.setText(str(layer.featureCount()))
        
        # CRS info
        crs = layer.crs()
        crs_text = f"{crs.authid()} - {crs.description()}" if crs.isValid() else "Unknown"
        self.crsValueLabel.setText(crs_text)
        
        # Display fields
        self._display_layer_fields(layer)
        
        # Display sample data
        self._display_sample_data(layer)
        
        # Display validation status
        self._display_validation_status(layer)
    
    def _display_layer_fields(self, layer: QgsVectorLayer):
        """Display the layer's field information."""
        fields = layer.fields()
        
        self.fieldsTableWidget.setRowCount(len(fields))
        
        for i, field in enumerate(fields):
            # Field name
            name_item = QTableWidgetItem(field.name())
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.fieldsTableWidget.setItem(i, 0, name_item)
            
            # Field type
            type_item = QTableWidgetItem(field.typeName())
            type_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.fieldsTableWidget.setItem(i, 1, type_item)
            
            # Field length
            length_text = str(field.length()) if field.length() > 0 else "-"
            length_item = QTableWidgetItem(length_text)
            length_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.fieldsTableWidget.setItem(i, 2, length_item)
        
        # Resize columns to content
        self.fieldsTableWidget.resizeColumnsToContents()
    
    def _display_sample_data(self, layer: QgsVectorLayer):
        """Display sample data from the layer."""
        try:
            # Get sample data using layer manager
            sample_data = self.layer_manager.get_sample_data(layer, max_features=5)
            
            if not sample_data:
                self.sampleDataTableWidget.setRowCount(0)
                self.sampleDataTableWidget.setColumnCount(0)
                return
            
            # Set up table structure
            fields = layer.fields()
            field_names = [field.name() for field in fields]
            
            self.sampleDataTableWidget.setColumnCount(len(field_names))
            self.sampleDataTableWidget.setHorizontalHeaderLabels(field_names)
            self.sampleDataTableWidget.setRowCount(len(sample_data))
            
            # Populate data
            for row, feature_data in enumerate(sample_data):
                for col, field_name in enumerate(field_names):
                    value = feature_data.get(field_name, '')
                    
                    # Convert value to string for display
                    if value is None:
                        display_value = 'NULL'
                    else:
                        display_value = str(value)
                    
                    item = QTableWidgetItem(display_value)
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    self.sampleDataTableWidget.setItem(row, col, item)
            
            # Resize columns to content
            self.sampleDataTableWidget.resizeColumnsToContents()
            
        except Exception as e:
            # If sample data fails, show error
            self.sampleDataTableWidget.setRowCount(1)
            self.sampleDataTableWidget.setColumnCount(1)
            self.sampleDataTableWidget.setHorizontalHeaderLabels(['Error'])
            
            error_item = QTableWidgetItem(f"Error loading sample data: {str(e)}")
            error_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.sampleDataTableWidget.setItem(0, 0, error_item)
    
    def _display_validation_status(self, layer: QgsVectorLayer):
        """Display validation status for the layer."""
        try:
            # Determine required geometry type based on current filter
            required_geometry = self.geometry_filter
            
            if required_geometry:
                # Validate layer compatibility
                validation_errors = self.layer_manager.validate_layer_compatibility(
                    layer, required_geometry
                )
                
                if not validation_errors:
                    self.validationStatusLabel.setText(
                        "✓ Layer is compatible with the selected geometry type"
                    )
                    self.validationStatusLabel.setStyleSheet(
                        "QLabel { color: #2d5a2d; background-color: #e8f5e8; padding: 5px; }"
                    )
                else:
                    error_text = "⚠ Validation Issues:\\n" + "\\n".join(f"• {error}" for error in validation_errors)
                    self.validationStatusLabel.setText(error_text)
                    self.validationStatusLabel.setStyleSheet(
                        "QLabel { color: #5a2d2d; background-color: #ffeaea; padding: 5px; }"
                    )
            else:
                # No specific geometry requirement
                feature_count = layer.featureCount()
                if feature_count > 0:
                    self.validationStatusLabel.setText(
                        f"✓ Layer contains {feature_count} features and is ready for use"
                    )
                    self.validationStatusLabel.setStyleSheet(
                        "QLabel { color: #2d5a2d; background-color: #e8f5e8; padding: 5px; }"
                    )
                else:
                    self.validationStatusLabel.setText(
                        "⚠ Layer contains no features"
                    )
                    self.validationStatusLabel.setStyleSheet(
                        "QLabel { color: #5a5a2d; background-color: #fff5e8; padding: 5px; }"
                    )
                    
        except Exception as e:
            self.validationStatusLabel.setText(
                f"Error validating layer: {str(e)}"
            )
            self.validationStatusLabel.setStyleSheet(
                "QLabel { color: #5a2d2d; background-color: #ffeaea; padding: 5px; }"
            )
    
    def _clear_layer_info(self):
        """Clear all layer information displays."""
        self.layerNameLabel.setText("Select a layer to view information")
        
        # Clear details
        self.geometryTypeValueLabel.setText("-")
        self.featureCountValueLabel.setText("-")
        self.crsValueLabel.setText("-")
        
        # Clear tables
        self.fieldsTableWidget.setRowCount(0)
        self.sampleDataTableWidget.setRowCount(0)
        self.sampleDataTableWidget.setColumnCount(0)
        
        # Clear validation
        self.validationStatusLabel.setText("Select a layer to see validation status")
        self.validationStatusLabel.setStyleSheet("")
    
    def set_geometry_filter(self, geometry_type: GeometryType):
        """
        Set the geometry type filter.
        
        Args:
            geometry_type: Required geometry type
        """
        filter_map = {
            GeometryType.POINT: 'Point Layers (Junctions/Manholes)',
            GeometryType.LINE: 'Line Layers (Pipes/Conduits)',
            GeometryType.POLYGON: 'Polygon Layers'
        }
        
        filter_text = filter_map.get(geometry_type, 'All Layers')
        
        # Find and set the combo box index
        index = self.geometryTypeCombo.findText(filter_text)
        if index >= 0:
            self.geometryTypeCombo.setCurrentIndex(index)
    
    def get_selected_layer(self) -> Optional[QgsVectorLayer]:
        """
        Get the currently selected layer.
        
        Returns:
            Selected QgsVectorLayer or None
        """
        return self.selected_layer
    
    def accept(self):
        """Handle dialog acceptance."""
        if self.selected_layer:
            self.layer_selected.emit(self.selected_layer)
        super().accept()