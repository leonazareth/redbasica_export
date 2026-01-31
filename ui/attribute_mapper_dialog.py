"""
Attribute Mapper Dialog for Flexible Sewerage Network DXF Export Plugin

This dialog provides flexible attribute mapping with auto-mapping suggestions,
manual mapping capabilities, and real-time validation.
"""

import os
from typing import Dict, List, Optional, Any

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QComboBox, 
    QLineEdit, QLabel, QPushButton, QTextEdit, QTabWidget,
    QHeaderView, QAbstractItemView, QMessageBox
)
from qgis.core import QgsVectorLayer, QgsWkbTypes

from ..core.layer_manager import LayerManager
from ..core.data_structures import GeometryType
from ..core.attribute_mapper import AttributeMapper
from ..core.data_structures import RequiredField, LayerMapping
from ..core.data_structures import FieldType
from ..core.i18n_manager import tr

# Load UI file
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'attribute_mapper_dialog.ui'))


class AttributeMapperDialog(QDialog, FORM_CLASS):
    """
    Dialog for flexible attribute field mapping with auto-suggestions.
    
    Features:
    - Auto-mapping based on common naming patterns
    - Manual field mapping capability
    - Default value configuration
    - Real-time validation feedback
    - Required/Optional field separation
    """
    
    # Signals
    mapping_changed = pyqtSignal()  # Emitted when mapping changes
    
    def __init__(self, layer_manager: LayerManager, parent=None):
        """
        Initialize the attribute mapper dialog.
        
        Args:
            layer_manager: LayerManager instance for layer operations
            parent: Parent widget
        """
        super(AttributeMapperDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.layer_manager = layer_manager
        self.attribute_mapper = AttributeMapper()
        
        # Current configuration
        self.current_layer = None
        self.geometry_type = None
        self.required_fields = []
        self.optional_fields = []
        self.layer_fields = []
        
        # Current mapping
        self.field_mappings = {}  # required_field_name -> layer_field_name
        self.default_values = {}  # required_field_name -> default_value
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up UI components."""
        # Configure tables
        self._setup_required_fields_table()
        self._setup_optional_fields_table()
        
        # Set initial states
        self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
        
        # Initialize validation display
        self.validationTextEdit.setStyleSheet(
            "QTextEdit { background-color: #f0f0f0; }"
        )
    
    def _setup_required_fields_table(self):
        """Configure the required fields table."""
        table = self.requiredFieldsTable
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            'Required Field', 'Description', 'Layer Field', 'Default Value', 'Status'
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
    
    def _setup_optional_fields_table(self):
        """Configure the optional fields table."""
        table = self.optionalFieldsTable
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            'Optional Field', 'Description', 'Layer Field', 'Default Value', 'Status'
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Mapping action buttons
        self.autoMapButton.clicked.connect(self._auto_map_fields)
        self.clearMappingButton.clicked.connect(self._clear_all_mappings)
        
        # Table cell changes will be connected when tables are populated
    
    def configure_for_layer(self, layer: QgsVectorLayer, geometry_type: GeometryType,
                          required_fields: List[RequiredField], 
                          optional_fields: List[RequiredField]):
        """
        Configure the dialog for a specific layer and field requirements.
        
        Args:
            layer: The layer to configure mapping for
            geometry_type: Required geometry type
            required_fields: List of required field definitions
            optional_fields: List of optional field definitions
        """
        self.current_layer = layer
        self.geometry_type = geometry_type
        self.required_fields = required_fields
        self.optional_fields = optional_fields
        
        # Get layer fields
        self.layer_fields = self.layer_manager.get_layer_fields(layer)
        
        # Update layer info display
        self._update_layer_info()
        
        # Populate field tables
        self._populate_required_fields_table()
        self._populate_optional_fields_table()
        
        # Clear existing mappings
        self.field_mappings.clear()
        self.default_values.clear()
        
        # Update validation
        self._update_validation()
    
    def _update_mapping_display(self):
        """
        Update the UI tables to reflect the current field_mappings and default_values.
        This is called after set_mapping() to sync the internal state with the UI.
        """
        # Update required fields table
        table = self.requiredFieldsTable
        for row in range(table.rowCount()):
            name_item = table.item(row, 0)
            if not name_item:
                continue
            
            field_name = name_item.text()
            
            # Update combo box selection
            combo = table.cellWidget(row, 2)
            if combo and isinstance(combo, QComboBox):
                mapped_field = self.field_mappings.get(field_name)
                if mapped_field:
                    # Find the index for this field
                    idx = combo.findData(mapped_field)
                    if idx >= 0:
                        combo.blockSignals(True)  # Prevent triggering handlers
                        combo.setCurrentIndex(idx)
                        combo.blockSignals(False)
            
            # Update default value line edit
            default_edit = table.cellWidget(row, 3)
            if default_edit and isinstance(default_edit, QLineEdit):
                default_val = self.default_values.get(field_name)
                if default_val is not None:
                    default_edit.blockSignals(True)
                    default_edit.setText(str(default_val))
                    default_edit.blockSignals(False)
            
            # Update status column
            status_item = table.item(row, 4)
            if status_item:
                is_mapped = field_name in self.field_mappings
                has_default = field_name in self.default_values
                if is_mapped:
                    status_item.setText("Mapped")
                elif has_default:
                    status_item.setText("Default")
                else:
                    status_item.setText("Not Configured")
        
        # Update optional fields table similarly
        table = self.optionalFieldsTable
        for row in range(table.rowCount()):
            name_item = table.item(row, 0)
            if not name_item:
                continue
            
            field_name = name_item.text()
            
            # Update combo box selection
            combo = table.cellWidget(row, 2)
            if combo and isinstance(combo, QComboBox):
                mapped_field = self.field_mappings.get(field_name)
                if mapped_field:
                    idx = combo.findData(mapped_field)
                    if idx >= 0:
                        combo.blockSignals(True)
                        combo.setCurrentIndex(idx)
                        combo.blockSignals(False)
            
            # Update default value line edit
            default_edit = table.cellWidget(row, 3)
            if default_edit and isinstance(default_edit, QLineEdit):
                default_val = self.default_values.get(field_name)
                if default_val is not None:
                    default_edit.blockSignals(True)
                    default_edit.setText(str(default_val))
                    default_edit.blockSignals(False)
            
            # Update status column
            status_item = table.item(row, 4)
            if status_item:
                is_mapped = field_name in self.field_mappings
                has_default = field_name in self.default_values
                if is_mapped:
                    status_item.setText("Mapped")
                elif has_default:
                    status_item.setText("Default")
                else:
                    status_item.setText("Not Configured")
    
    def _update_layer_info(self):
        """Update the layer information display."""
        if not self.current_layer:
            return
        
        self.layerNameValueLabel.setText(self.current_layer.name())
        
        # Geometry type
        geom_type_map = {
            QgsWkbTypes.PointGeometry: "Point",
            QgsWkbTypes.LineGeometry: "Line",
            QgsWkbTypes.PolygonGeometry: "Polygon"
        }
        geom_type_text = geom_type_map.get(self.current_layer.geometryType(), "Unknown")
        self.geometryTypeValueLabel.setText(geom_type_text)
        
        # Field count
        self.fieldCountValueLabel.setText(str(len(self.layer_fields)))
    
    def _populate_required_fields_table(self):
        """Populate the required fields table."""
        table = self.requiredFieldsTable
        table.setRowCount(len(self.required_fields))
        
        for row, field in enumerate(self.required_fields):
            # Field name (read-only)
            name_item = QTableWidgetItem(field.name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            table.setItem(row, 0, name_item)
            
            # Description (read-only)
            desc_item = QTableWidgetItem(field.description)
            desc_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            desc_item.setToolTip(field.description)
            table.setItem(row, 1, desc_item)
            
            # Layer field combo box
            field_combo = QComboBox()
            field_combo.addItem("-- Not Mapped --", None)
            
            # Add layer fields
            for layer_field_name, field_type in self.layer_fields.items():
                field_combo.addItem(layer_field_name, layer_field_name)
            
            # Connect change signal with proper closure
            def make_required_field_handler(row_idx, field_obj):
                return lambda text: self._on_required_field_mapping_changed(row_idx, field_obj, text)
            
            field_combo.currentTextChanged.connect(make_required_field_handler(row, field))
            
            table.setCellWidget(row, 2, field_combo)
            
            # Default value line edit
            default_edit = QLineEdit()
            if field.default_value is not None:
                default_edit.setText(str(field.default_value))
            default_edit.setPlaceholderText("Enter default value...")
            
            # Connect change signal with proper closure
            def make_default_handler(field_obj):
                return lambda text: self._on_default_value_changed(field_obj, text)
            
            default_edit.textChanged.connect(make_default_handler(field))
            
            table.setCellWidget(row, 3, default_edit)
            
            # Status (read-only)
            status_item = QTableWidgetItem("Not Configured")
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            table.setItem(row, 4, status_item)
    
    def _populate_optional_fields_table(self):
        """Populate the optional fields table."""
        table = self.optionalFieldsTable
        table.setRowCount(len(self.optional_fields))
        
        for row, field in enumerate(self.optional_fields):
            # Field name (read-only)
            name_item = QTableWidgetItem(field.name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            table.setItem(row, 0, name_item)
            
            # Description (read-only)
            desc_item = QTableWidgetItem(field.description)
            desc_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            desc_item.setToolTip(field.description)
            table.setItem(row, 1, desc_item)
            
            # Layer field combo box
            field_combo = QComboBox()
            field_combo.addItem("-- Not Mapped --", None)
            
            # Add layer fields
            for layer_field_name, field_type in self.layer_fields.items():
                field_combo.addItem(layer_field_name, layer_field_name)
            
            # Connect change signal with proper closure
            def make_optional_field_handler(row_idx, field_obj):
                return lambda text: self._on_optional_field_mapping_changed(row_idx, field_obj, text)
            
            field_combo.currentTextChanged.connect(make_optional_field_handler(row, field))
            
            table.setCellWidget(row, 2, field_combo)
            
            # Default value line edit
            default_edit = QLineEdit()
            if field.default_value is not None:
                default_edit.setText(str(field.default_value))
            default_edit.setPlaceholderText("Enter default value...")
            
            # Connect change signal with proper closure
            def make_default_handler_opt(field_obj):
                return lambda text: self._on_default_value_changed(field_obj, text)
            
            default_edit.textChanged.connect(make_default_handler_opt(field))
            
            table.setCellWidget(row, 3, default_edit)
            
            # Status (read-only)
            status_item = QTableWidgetItem("Not Configured")
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            table.setItem(row, 4, status_item)
    
    def _on_required_field_mapping_changed(self, row: int, field: RequiredField, selected_text: str):
        """Handle required field mapping change."""
        if selected_text == "-- Not Mapped --":
            self.field_mappings.pop(field.name, None)
        else:
            self.field_mappings[field.name] = selected_text
        
        self._update_field_status(self.requiredFieldsTable, row, field)
        self._update_validation()
        self.mapping_changed.emit()
    
    def _on_optional_field_mapping_changed(self, row: int, field: RequiredField, selected_text: str):
        """Handle optional field mapping change."""
        if selected_text == "-- Not Mapped --":
            self.field_mappings.pop(field.name, None)
        else:
            self.field_mappings[field.name] = selected_text
        
        self._update_field_status(self.optionalFieldsTable, row, field)
        self._update_validation()
        self.mapping_changed.emit()
    
    def _on_default_value_changed(self, field: RequiredField, value: str):
        """Handle default value change."""
        if value.strip():
            self.default_values[field.name] = value.strip()
        else:
            self.default_values.pop(field.name, None)
        
        self._update_validation()
        self.mapping_changed.emit()
    
    def _update_field_status(self, table: QTableWidget, row: int, field: RequiredField):
        """Update the status column for a field."""
        is_mapped = field.name in self.field_mappings
        has_default = field.name in self.default_values
        
        if is_mapped:
            status_text = "✓ Mapped"
            status_color = "#2d5a2d"
        elif has_default:
            status_text = "✓ Default Value"
            status_color = "#5a5a2d"
        else:
            status_text = "Not Configured"
            status_color = "#5a2d2d"
        
        status_item = table.item(row, 4)
        if status_item:
            status_item.setText(status_text)
            status_item.setForeground(QColor(status_color))
    
    def _auto_map_fields(self):
        """Automatically map fields based on naming patterns."""
        try:
            if not self.current_layer:
                QMessageBox.warning(
                    self, "Auto-Mapping Error",
                    "No layer selected for auto-mapping."
                )
                return
            
            # Create auto-mapping using AttributeMapper
            auto_mapping = self.attribute_mapper.create_auto_mapping(
                self.current_layer, self.geometry_type
            )
            
            if not auto_mapping.field_mappings and not auto_mapping.default_values:
                QMessageBox.information(
                    self, "Auto-Mapping",
                    "No automatic field mappings could be suggested based on common naming patterns."
                )
                return
            
            # Apply auto-mapping suggestions
            applied_count = 0
            
            # Apply field mappings
            for field_name, layer_field in auto_mapping.field_mappings.items():
                if layer_field in self.layer_fields:
                    self.field_mappings[field_name] = layer_field
                    applied_count += 1
            
            # Apply default values
            for field_name, default_value in auto_mapping.default_values.items():
                if field_name not in self.field_mappings:  # Don't override mapped fields
                    self.default_values[field_name] = default_value
                    applied_count += 1
            
            # Update UI
            self._update_mapping_display()
            self._update_validation()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Auto-Mapping Error",
                f"Failed to perform automatic field mapping:\\n{str(e)}"
            )
    
    def _clear_all_mappings(self):
        """Clear all field mappings and default values."""
        self.field_mappings.clear()
        self.default_values.clear()
        
        # Update UI
        self._update_mapping_display()
        self._update_validation()
        
        self.mapping_changed.emit()
    
    def _update_validation(self):
        """Update validation status display."""
        validation_errors = self._get_validation_errors()
        
        if not validation_errors:
            self.validationTextEdit.setPlainText("✓ Field mapping is complete and ready for export")
            self.validationTextEdit.setStyleSheet(
                "QTextEdit { background-color: #e8f5e8; color: #2d5a2d; }"
            )
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(True)
        else:
            error_text = "Mapping Issues:\n" + "\n".join(f"• {error}" for error in validation_errors)
            self.validationTextEdit.setPlainText(error_text)
            self.validationTextEdit.setStyleSheet(
                "QTextEdit { background-color: #ffeaea; color: #5a2d2d; }"
            )
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)

    def _get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            is_mapped = field.name in self.field_mappings
            has_default = field.name in self.default_values
            
            if not is_mapped and not has_default:
                display_name = getattr(field, 'display_name', field.name)
                errors.append(f"Required field '{display_name}' must be mapped or have a default value")
        
        # Check for duplicate mappings
        mapped_layer_fields = [field for field in self.field_mappings.values()]
        duplicates = set([field for field in mapped_layer_fields if mapped_layer_fields.count(field) > 1])
        
        for duplicate in duplicates:
            errors.append(f"Layer field '{duplicate}' is mapped to multiple required fields")
        
        return errors
    
    def get_mapping(self) -> Optional[LayerMapping]:
        """
        Get the current layer mapping configuration.
        
        Returns:
            LayerMapping object or None if invalid
        """
        if not self.current_layer:
            return None
        
        validation_errors = self._get_validation_errors()
        
        return LayerMapping(
            layer_id=self.current_layer.id(),
            layer_name=self.current_layer.name(),
            geometry_type=self.geometry_type,
            field_mappings=self.field_mappings.copy(),
            default_values=self.default_values.copy(),
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors if validation_errors else None
        )

    def set_mapping(self, mapping: LayerMapping):
        """
        Set the current mapping from a LayerMapping object.
        
        Args:
            mapping: LayerMapping to apply
        """
        # We don't check layer_id strictly here because usually we WANT to apply
        # the saved mapping to the current layer even if IDs somehow differ
        # (e.g. if the user wants to apply a template or previous config)
        
        self.field_mappings = mapping.field_mappings.copy()
        self.default_values = mapping.default_values.copy()
        
        # Update UI
        self._update_mapping_display()
        self._update_validation()
    
    def accept(self):
        """Handle dialog acceptance."""
        mapping = self.get_mapping()
        if mapping and mapping.is_valid:
            super().accept()
        else:
            QMessageBox.warning(
                self, "Invalid Mapping",
                "Please resolve all validation issues before proceeding."
            )