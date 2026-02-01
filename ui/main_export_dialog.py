"""
Main Export Dialog for Flexible Sewerage Network DXF Export Plugin

This dialog provides the primary interface for configuring and executing DXF exports
with flexible layer selection and attribute mapping capabilities.
"""

import os
from typing import Dict, List, Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QPushButton, 
    QLineEdit, QSpinBox, QCheckBox, QTextEdit, QLabel
)
from qgis.PyQt import QtWidgets
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsWkbTypes, QgsMapLayerProxyModel
)
from qgis.gui import QgsMapLayerComboBox

from ..core.layer_manager import LayerManager
from ..core.data_structures import GeometryType
from ..core.configuration import Configuration, ExportConfiguration
from ..core.field_definitions import SewageNetworkFields
from ..core.validation import ComprehensiveValidator, ValidationResult
from ..core.exceptions import ValidationError, ExportError
from ..core.error_messages import create_error_formatter
from ..core.dxf_exporter import DXFExporter
from ..core.i18n_manager import tr
from ..core.i18n_manager import tr
from ..core.attribute_mapper import AttributeMapper
from .attribute_mapper_dialog import AttributeMapperDialog
from .collapsible_group_box import CollapsibleGroupBox

# Load UI file
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'main_export_dialog.ui'))


class MainExportDialog(QDialog, FORM_CLASS):
    """
    Main dialog for configuring and executing flexible DXF exports.
    
    Features:
    - Layer selection with geometry type filtering
    - Real-time validation feedback
    - Configuration persistence
    - Attribute mapping integration
    """
    
    # Signals
    export_requested = pyqtSignal(dict)  # Emitted when export is requested
    
    def __init__(self, layer_manager: LayerManager, parent=None):
        """
        Initialize the main export dialog.
        
        Args:
            layer_manager: LayerManager instance for layer operations
            parent: Parent widget
        """
        super(MainExportDialog, self).__init__(parent)
        super(MainExportDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("RedBasica Export Helper")
        
        self.layer_manager = layer_manager
        self.configuration = Configuration()
        self.attribute_mapper = AttributeMapper()
        self.error_formatter = create_error_formatter()
        
        # Attribute mapping dialogs
        self.pipes_mapper_dialog = None
        self.junctions_mapper_dialog = None
        
        # Current mappings
        self.pipes_mapping = None
        self.junctions_mapping = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_configuration()
        self._update_validation()
    
    def _setup_ui(self):
        """Set up UI components and layer filtering."""
        # Configure layer combo boxes with geometry filtering
        self._setup_layer_combos()
        
        # Set initial button states
        self.configurePipesButton.setEnabled(False)
        self.configureJunctionsButton.setEnabled(False)
        
        # Set OK button text
        self.buttonBox.button(self.buttonBox.Ok).setText("Export DXF")
        
        # Initialize validation display
        self.validationTextEdit.setStyleSheet(
            "QTextEdit { background-color: #f0f0f0; }"
        )
        
        # Setup collapsible Advanced Options section
        self._setup_collapsible_advanced_options()
    
    def _setup_layer_combos(self):
        """Configure layer combo boxes with appropriate filtering."""
        # Pipes layer combo - show only line layers
        self.pipesLayerCombo.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.pipesLayerCombo.setAllowEmptyLayer(True)
        self.pipesLayerCombo.setShowCrs(True)
        
        # Junctions layer combo - show only point layers  
        self.junctionsLayerCombo.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.junctionsLayerCombo.setAllowEmptyLayer(True)
        self.junctionsLayerCombo.setShowCrs(True)

        # Add Auto-Map Button Programmatically
        from qgis.PyQt.QtWidgets import QPushButton, QFormLayout
        self.autoMapButton = QPushButton("Auto-Map Fields")
        self.autoMapButton.setToolTip("Attempt to automatically map fields for selected layers")
        
        # Find the layer layout
        layer_group = self.findChild(QtWidgets.QGroupBox, "layerSelectionGroup")
        if layer_group and layer_group.layout():
             # Add to row 2
             layer_group.layout().setWidget(2, QFormLayout.SpanningRole, self.autoMapButton)
    
    def _setup_collapsible_advanced_options(self):
        """Replace the static Advanced Options group with a collapsible one."""
        # Get the main layout
        main_layout = self.layout()
        
        # Find and remove the current advancedOptionsGroup
        old_group = self.advancedOptionsGroup
        old_group_index = main_layout.indexOf(old_group)
        
        # Create the collapsible group box (collapsed by default)
        self.collapsible_advanced = CollapsibleGroupBox(
            title="Advanced Options", 
            collapsed=True
        )
        
        # Move widgets from old group to new collapsible group
        # We need to re-parent the widgets
        
        # Move widgets from old group to new collapsible group
        # We need to re-parent the widgets
        
        # 1. Export Mode Selection
        from qgis.PyQt.QtWidgets import QHBoxLayout, QWidget, QLabel, QComboBox
        from ..core.data_structures import ExportMode, LabelStyle
        
        mode_container = QWidget()
        mode_layout = QHBoxLayout(mode_container)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        self.exportModeLabel = QLabel("Export Mode:")
        self.exportModeCombo = QComboBox()
        for mode in ExportMode:
            # Skip ENHANCED mode for now
            if mode.name != "ENHANCED":
                self.exportModeCombo.addItem(mode.value, mode)
            
        mode_layout.addWidget(self.exportModeLabel)
        mode_layout.addWidget(self.exportModeCombo)
        self.collapsible_advanced.addWidget(mode_container)
        
        # 2. Hidden Checkboxes (always TRUE - user always wants arrows/labels)
        # Create NEW checkbox instances since originals get deleted with old_group
        from qgis.PyQt.QtWidgets import QCheckBox
        self.includeArrowsCheckBox = QCheckBox("Include flow direction arrows")
        self.includeArrowsCheckBox.setChecked(True)  # Always TRUE
        self.includeLabelsCheckBox = QCheckBox("Include pipe labels")
        self.includeLabelsCheckBox.setChecked(True)  # Always TRUE
        # Don't add to UI - they're hidden but accessible for config
        
        # 3. Label Style (Sub-option for Labels)
        style_container = QWidget()
        style_layout = QHBoxLayout(style_container)
        style_layout.setContentsMargins(20, 0, 0, 0) # Indent to show hierarchy
        
        self.labelStyleLabel = QLabel("Label Style:")
        self.labelStyleCombo = QComboBox()
        for style in LabelStyle:
            self.labelStyleCombo.addItem(style.value, style)
            
        style_layout.addWidget(self.labelStyleLabel)
        style_layout.addWidget(self.labelStyleCombo)
        self.collapsible_advanced.addWidget(style_container)
        
        # Connect logic to enable/disable style combo based on includeLabels
        def update_style_combo_state(checked):
            self.labelStyleCombo.setEnabled(checked)
            self.labelStyleLabel.setEnabled(checked)
        self.includeLabelsCheckBox.toggled.connect(update_style_combo_state)
        # Initialize state
        update_style_combo_state(self.includeLabelsCheckBox.isChecked())

        self.collapsible_advanced.addWidget(self.includeElevationsCheckBox)
        
        # 4. Export Node ID in Labels (unchecked by default)
        from qgis.PyQt.QtWidgets import QCheckBox
        self.exportNodeIdCheckBox = QCheckBox("Export Node ID in Labels")
        self.exportNodeIdCheckBox.setChecked(False)  # Default: unchecked
        self.exportNodeIdCheckBox.setToolTip("When checked, includes the node identifier after the depth value in labels")
        self.collapsible_advanced.addWidget(self.exportNodeIdCheckBox)
        
        # 5. Include Slope Unit (unchecked by default)
        self.includeSlopeUnitCheckBox = QCheckBox("Include Slope Unit (m/m)")
        self.includeSlopeUnitCheckBox.setChecked(False)  # Default: unchecked
        self.includeSlopeUnitCheckBox.setToolTip("When checked, appends 'm/m' after slope values")
        self.collapsible_advanced.addWidget(self.includeSlopeUnitCheckBox)
        
        # 6. Include Collector Depth (checked by default)
        self.includeCollectorDepthCheckBox = QCheckBox("Include Collector Depth")
        self.includeCollectorDepthCheckBox.setChecked(True)
        self.includeCollectorDepthCheckBox.setToolTip("Show collector depth (h_col_p2) 5m from downstream node")
        self.collapsible_advanced.addWidget(self.includeCollectorDepthCheckBox)
        
        # Create a container for the label format row
        label_format_container = QWidget()
        label_format_layout = QHBoxLayout(label_format_container)
        label_format_layout.setContentsMargins(0, 0, 0, 0)
        label_format_layout.addWidget(self.labelFormatLabel)
        label_format_layout.addWidget(self.labelFormatEdit)
        self.collapsible_advanced.addWidget(label_format_container)
        
        # Hide and remove old group
        old_group.hide()
        main_layout.removeWidget(old_group)
        old_group.deleteLater()
        
        # Insert collapsible group at same position
        main_layout.insertWidget(old_group_index, self.collapsible_advanced)
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Layer selection changes
        self.pipesLayerCombo.layerChanged.connect(self._on_pipes_layer_changed)
        self.junctionsLayerCombo.layerChanged.connect(self._on_junctions_layer_changed)
        
        # Configuration buttons
        self.configurePipesButton.clicked.connect(self._configure_pipes_mapping)
        self.configureJunctionsButton.clicked.connect(self._configure_junctions_mapping)
        
        # File browser buttons
        self.browseOutputButton.clicked.connect(self._browse_output_file)
        
        # Validation triggers
        self.outputPathEdit.textChanged.connect(self._update_validation)
        self.scaleFactorSpinBox.valueChanged.connect(self._update_validation)
        self.layerPrefixEdit.textChanged.connect(self._update_validation)
        
        # Advanced options
        self.includeArrowsCheckBox.toggled.connect(self._update_validation)
        self.includeLabelsCheckBox.toggled.connect(self._update_validation)
        self.includeElevationsCheckBox.toggled.connect(self._update_validation)
        self.includeElevationsCheckBox.toggled.connect(self._update_validation)
        self.labelFormatEdit.textChanged.connect(self._update_validation)
        
        # Connect new Auto-Map button if created
        if hasattr(self, 'autoMapButton'):
            self.autoMapButton.clicked.connect(self._manual_auto_map_all)

    def _manual_auto_map_all(self):
        """Manually trigger auto-mapping for all layers."""
        pipes_layer = self.pipesLayerCombo.currentLayer()
        if pipes_layer:
            self._try_auto_configure_pipes(pipes_layer)
            
        junctions_layer = self.junctionsLayerCombo.currentLayer()
        if junctions_layer:
            self._try_auto_configure_junctions(junctions_layer)
            
        # Show feedback using Message Bar
        
        # Update validation status visually
        self._update_validation()

        # Validation checks logic
        pipes_mapped = self.pipes_mapping and self.pipes_mapping.is_valid
        junctions_mapped = self.junctions_mapping and self.junctions_mapping.is_valid
        
        from qgis.utils import iface
        from qgis.core import Qgis
        
        if pipes_mapped and junctions_mapped:
            iface.messageBar().pushMessage("RedBasica", "All fields auto-mapped successfully!", Qgis.Success)
        elif pipes_mapped:
            iface.messageBar().pushMessage("RedBasica", "Pipes auto-mapped. Junctions missing required mappings.", Qgis.Warning)
        elif junctions_mapped:
            iface.messageBar().pushMessage("RedBasica", "Junctions auto-mapped. Pipes missing required mappings.", Qgis.Warning)
        else:
             iface.messageBar().pushMessage("RedBasica", "Auto-mapping failed. Check field names.", Qgis.Warning)
    
    def _on_pipes_layer_changed(self, layer: QgsVectorLayer):
        """Handle pipes layer selection change."""
        if layer:
            # Validate geometry type
            if layer.geometryType() != QgsWkbTypes.LineGeometry:
                QMessageBox.warning(
                    self, "Invalid Layer Type",
                    f"Selected layer '{layer.name()}' is not a line layer. "
                    "Please select a layer containing pipe/conduit geometries."
                )
                self.pipesLayerCombo.setLayer(None)
                return
            
            self.configurePipesButton.setEnabled(True)
            
            # Reset mapping initially
            self.pipes_mapping = None
            
            # Check for saved configuration FIRST
            saved_config = self.configuration.load_export_configuration()
            if saved_config and saved_config.pipes_mapping and saved_config.pipes_mapping.layer_id == layer.id():
                self.pipes_mapping = saved_config.pipes_mapping
                print(f"DEBUG: Loaded saved pipes mapping for {layer.name()}")
            else:
                # AUTO-MAP: Only try if no saved config exists
                self._try_auto_configure_pipes(layer)
            
            self._update_validation()
        else:
            self.configurePipesButton.setEnabled(False)
            self.pipes_mapping = None
        
        self._update_validation()
    
    def _on_junctions_layer_changed(self, layer: QgsVectorLayer):
        """Handle junctions layer selection change."""
        if layer:
            # Validate geometry type
            if layer.geometryType() != QgsWkbTypes.PointGeometry:
                QMessageBox.warning(
                    self, "Invalid Layer Type", 
                    f"Selected layer '{layer.name()}' is not a point layer. "
                    "Please select a layer containing junction/manhole geometries."
                )
                self.junctionsLayerCombo.setLayer(None)
                return
            
            self.configureJunctionsButton.setEnabled(True)
             
            # Reset mapping initially
            self.junctions_mapping = None
            
            # Check for saved configuration FIRST
            saved_config = self.configuration.load_export_configuration()
            if saved_config and saved_config.junctions_mapping and saved_config.junctions_mapping.layer_id == layer.id():
                self.junctions_mapping = saved_config.junctions_mapping
                print(f"DEBUG: Loaded saved junctions mapping for {layer.name()}")
            else:
                # AUTO-MAP: Only try if no saved config exists
                self._try_auto_configure_junctions(layer)
            
            self._update_validation()
        else:
            self.configureJunctionsButton.setEnabled(False)
            self.junctions_mapping = None
        
        self._update_validation()
    
    def _configure_pipes_mapping(self):
        """Open attribute mapping dialog for pipes layer."""
        layer = self.pipesLayerCombo.currentLayer()
        if not layer:
            return
        
        # Create or reuse mapper dialog
        if not self.pipes_mapper_dialog:
            self.pipes_mapper_dialog = AttributeMapperDialog(
                layer_manager=self.layer_manager,
                parent=self
            )
        
        # Configure for pipes
        self.pipes_mapper_dialog.configure_for_layer(
            layer=layer,
            geometry_type=GeometryType.LINE,
            required_fields=SewageNetworkFields.get_pipes_required_fields(),
            optional_fields=SewageNetworkFields.get_pipes_optional_fields()
        )
        
        # Set existing mapping if available
        if self.pipes_mapping:
            self.pipes_mapper_dialog.set_mapping(self.pipes_mapping)
        
        # Show dialog
        if self.pipes_mapper_dialog.exec_() == QDialog.Accepted:
            self.pipes_mapping = self.pipes_mapper_dialog.get_mapping()
            # Save configuration immediately to persist mappings
            config = self.get_export_configuration()
            self.configuration.current_config = config
            self._update_validation()
    
    def _configure_junctions_mapping(self):
        """Open attribute mapping dialog for junctions layer."""
        layer = self.junctionsLayerCombo.currentLayer()
        if not layer:
            return
        
        # Create or reuse mapper dialog
        if not self.junctions_mapper_dialog:
            self.junctions_mapper_dialog = AttributeMapperDialog(
                layer_manager=self.layer_manager,
                parent=self
            )
        
        # Configure for junctions
        self.junctions_mapper_dialog.configure_for_layer(
            layer=layer,
            geometry_type=GeometryType.POINT,
            required_fields=SewageNetworkFields.get_junctions_required_fields(),
            optional_fields=SewageNetworkFields.get_junctions_optional_fields()
        )
        
        # Set existing mapping if available
        if self.junctions_mapping:
            self.junctions_mapper_dialog.set_mapping(self.junctions_mapping)
        
        # Show dialog
        if self.junctions_mapper_dialog.exec_() == QDialog.Accepted:
            self.junctions_mapping = self.junctions_mapper_dialog.get_mapping()
            # Save configuration immediately to persist mappings
            config = self.get_export_configuration()
            self.configuration.current_config = config
            self._update_validation()
    
    def _browse_output_file(self):
        """Browse for output DXF file location."""
        current_path = self.outputPathEdit.text()
        if not current_path:
            # Default to project directory if available
            project = QgsProject.instance()
            if project.fileName():
                current_path = os.path.dirname(project.fileName())
            else:
                current_path = os.path.expanduser("~")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save DXF File",
            current_path,
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.outputPathEdit.setText(file_path)
    
    def _update_validation(self):
        """Update validation status display."""
        validation_errors = self.validate_configuration()
        
        if not validation_errors:
            self.validationTextEdit.setPlainText("✓ Configuration is valid and ready for export")
            self.validationTextEdit.setStyleSheet(
                "QTextEdit { background-color: #e8f5e8; color: #2d5a2d; }"
            )
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(True)
        else:
            error_text = "Configuration Issues:\n" + "\n".join(f"• {error}" for error in validation_errors)
            self.validationTextEdit.setPlainText(error_text)
            self.validationTextEdit.setStyleSheet(
                "QTextEdit { background-color: #ffeaea; color: #5a2d2d; }"
            )
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
    
    def validate_configuration(self) -> List[str]:
        """
        Validate current configuration and return list of errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check layer selection
        pipes_layer = self.pipesLayerCombo.currentLayer()
        junctions_layer = self.junctionsLayerCombo.currentLayer()
        
        if not pipes_layer and not junctions_layer:
            errors.append("At least one layer (pipes or junctions) must be selected")
        
        # Check pipes layer and mapping
        if pipes_layer:
            if not self.pipes_mapping:
                errors.append("Pipes layer selected but field mapping not configured")
            elif not self.pipes_mapping.is_valid:
                errors.extend([f"Pipes mapping: {error}" for error in self.pipes_mapping.validation_errors or []])
        
        # Check junctions layer and mapping
        if junctions_layer:
            if not self.junctions_mapping:
                errors.append("Junctions layer selected but field mapping not configured")
            elif not self.junctions_mapping.is_valid:
                errors.extend([f"Junctions mapping: {error}" for error in self.junctions_mapping.validation_errors or []])
        
        # Check output path
        output_path = self.outputPathEdit.text().strip()
        if not output_path:
            errors.append("Output file path is required")
        else:
            # Check if directory exists and is writable
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                errors.append(f"Output directory does not exist: {output_dir}")
            elif output_dir and not os.access(output_dir, os.W_OK):
                errors.append(f"Output directory is not writable: {output_dir}")
        
        # Check scale factor
        if self.scaleFactorSpinBox.value() <= 0:
            errors.append("Scale factor must be greater than 0")
        
        # Check label format if labels are enabled
        if self.includeLabelsCheckBox.isChecked():
            label_format = self.labelFormatEdit.text().strip()
            if not label_format:
                errors.append("Label format is required when labels are enabled")
        
        return errors
    
    def get_export_configuration(self) -> Optional[ExportConfiguration]:
        """
        Get current export configuration.
        
        Returns:
            ExportConfiguration object or None if invalid
        """
        validation_errors = self.validate_configuration()
        if validation_errors:
            print(f"DEBUG: Validation errors: {validation_errors}")
            return None
        
        print(f"DEBUG: Creating ExportConfiguration in main_export_dialog")
        print(f"DEBUG: self.pipes_mapping type: {type(self.pipes_mapping)}")
        print(f"DEBUG: self.pipes_mapping: {self.pipes_mapping}")
        print(f"DEBUG: self.junctions_mapping type: {type(self.junctions_mapping)}")
        print(f"DEBUG: self.junctions_mapping: {self.junctions_mapping}")
        
        if self.pipes_mapping:
            print(f"DEBUG: pipes_mapping.field_mappings type: {type(self.pipes_mapping.field_mappings)}")
            print(f"DEBUG: pipes_mapping.field_mappings: {self.pipes_mapping.field_mappings}")
        
        return ExportConfiguration(
            pipes_mapping=self.pipes_mapping,
            junctions_mapping=self.junctions_mapping,
            output_path=self.outputPathEdit.text().strip(),
            scale_factor=self.scaleFactorSpinBox.value(),
            layer_prefix=self.layerPrefixEdit.text().strip(),
            template_path=None,
            include_arrows=self.includeArrowsCheckBox.isChecked(),
            include_labels=self.includeLabelsCheckBox.isChecked(),
            include_elevations=self.includeElevationsCheckBox.isChecked(),
            export_node_id=self.exportNodeIdCheckBox.isChecked(),
            include_slope_unit=self.includeSlopeUnitCheckBox.isChecked(),
            include_collector_depth=self.includeCollectorDepthCheckBox.isChecked(),
            label_format=self.labelFormatEdit.text().strip(),
            export_mode=self.exportModeCombo.currentData(),
            label_style=self.labelStyleCombo.currentData()
        )
    
    def _load_configuration(self):
        """Load saved configuration settings."""
        try:
            from ..core.data_structures import ExportMode, LabelStyle

            # Load basic settings
            self.scaleFactorSpinBox.setValue(
                self.configuration.get_setting('scale_factor', 1000)
            )
            self.layerPrefixEdit.setText(
                self.configuration.get_setting('layer_prefix', 'RB_')
            )
            
            # Load advanced options
            
            # Label Style
            # Label Style - force default to STACKED if not set or invalid
            # Also handle migration from "COMPACT" if it was saved previously
            saved_style_name = self.configuration.get_setting('label_style', LabelStyle.STACKED.name)
            
            if saved_style_name in ["COMPACT", "2 lines"]: # Force migration to STACKED
                 saved_style_name = LabelStyle.STACKED.name
            
            # Find index
            style_idx = -1
            try:
                target_data = LabelStyle[saved_style_name]
                style_idx = self.labelStyleCombo.findData(target_data)
            except KeyError:
                pass
            
            if style_idx >= 0:
                self.labelStyleCombo.setCurrentIndex(style_idx)
            else:
                # Absolute fallback
                fallback_idx = self.labelStyleCombo.findData(LabelStyle.STACKED)
                if fallback_idx >= 0:
                    self.labelStyleCombo.setCurrentIndex(fallback_idx)
            
            # Find and set the mode in combobox
            mode_index = self.exportModeCombo.findData(ExportMode[saved_mode_name])
            if mode_index >= 0:
                self.exportModeCombo.setCurrentIndex(mode_index)

            self.includeArrowsCheckBox.setChecked(
                self.configuration.get_setting('include_arrows', True)
            )
            self.includeLabelsCheckBox.setChecked(
                self.configuration.get_setting('include_labels', True)
            )
            self.includeElevationsCheckBox.setChecked(
                self.configuration.get_setting('include_elevations', True)
            )
            
            # Label Style
            # Label Style - force default to STACKED if not set or invalid
            # Also handle migration from "COMPACT" if it was saved previously
            saved_style_name = self.configuration.get_setting('label_style', LabelStyle.STACKED.name)
            
            if saved_style_name == "COMPACT": # Force migration to STACKED
                 saved_style_name = LabelStyle.STACKED.name
            
            # Find index
            style_idx = -1
            target_data = None
            try:
                target_data = LabelStyle[saved_style_name]
                style_idx = self.labelStyleCombo.findData(target_data)
            except KeyError:
                pass
            
            if style_idx >= 0:
                self.labelStyleCombo.setCurrentIndex(style_idx)
            else:
                # Absolute fallback
                fallback_idx = self.labelStyleCombo.findData(LabelStyle.STACKED)
                if fallback_idx >= 0:
                    self.labelStyleCombo.setCurrentIndex(fallback_idx)

            self.labelFormatEdit.setText(
                self.configuration.get_setting('label_format', '{length:.0f}-{diameter:.0f}-{slope:.5f}')
            )
            
            # Load output path - prioritize current project path
            project = QgsProject.instance()
            project_path = project.fileName()
            
            if project_path:
                # Default to [Project Directory]/[Project Name].dxf
                base_name = os.path.splitext(os.path.basename(project_path))[0]
                default_path = os.path.join(os.path.dirname(project_path), f"{base_name}.dxf")
                self.outputPathEdit.setText(default_path)
            else:
                # Fallback to last output path if project is not saved
                last_output = self.configuration.get_setting('last_output_path', '')
                if last_output:
                    self.outputPathEdit.setText(last_output)
            
        except Exception as e:
            # If loading fails, use defaults
            pass
    
    def _save_configuration(self):
        """Save current configuration settings."""
        try:
            self.configuration.set_setting('scale_factor', self.scaleFactorSpinBox.value())
            self.configuration.set_setting('layer_prefix', self.layerPrefixEdit.text())
            self.configuration.set_setting('include_arrows', self.includeArrowsCheckBox.isChecked())
            self.configuration.set_setting('include_labels', self.includeLabelsCheckBox.isChecked())
            self.configuration.set_setting('include_elevations', self.includeElevationsCheckBox.isChecked())
            self.configuration.set_setting('label_format', self.labelFormatEdit.text())
            self.configuration.set_setting('last_output_path', self.outputPathEdit.text())
            
            # Save Enums by name
            self.configuration.set_setting('export_mode', self.exportModeCombo.currentData().name)
            self.configuration.set_setting('label_style', self.labelStyleCombo.currentData().name)
            
        except Exception as e:
            # If saving fails, continue silently
            pass
    
    def accept(self):
        """Handle dialog acceptance (Export button clicked)."""
        config = self.get_export_configuration()
        if config:
            self._save_configuration()
            # Signal that export was requested
            config_dict = self.configuration._export_config_to_dict(config)
        self.export_requested.emit(config_dict)
        super().accept()

    def _try_auto_configure_pipes(self, layer):
        """Try to auto-configure pipes mapping using AttributeMapper."""
        if not layer:
            return

        from ..core.data_structures import GeometryType

        try:
            # Use shared AttributeMapper logic
            mapping = self.attribute_mapper.create_auto_mapping(layer, GeometryType.LINE)
            
            # Check if we have at least ANY valid mapping or default
            if mapping.field_mappings or mapping.default_values:
                self.pipes_mapping = mapping
                print(f"DEBUG: Auto-configured pipes mapping for {layer.name()}")
                
        except Exception as e:
            print(f"Auto-config error (pipes): {e}")

    def _try_auto_configure_junctions(self, layer):
        """Try to auto-configure junctions mapping using AttributeMapper."""
        if not layer:
            return

        from ..core.data_structures import GeometryType

        try:
            # Use shared AttributeMapper logic
            mapping = self.attribute_mapper.create_auto_mapping(layer, GeometryType.POINT)
            
            # Check if we have at least ANY valid mapping or default
            if mapping.field_mappings or mapping.default_values:
                self.junctions_mapping = mapping
                print(f"DEBUG: Auto-configured junctions mapping for {layer.name()}")

        except Exception as e:
            print(f"Auto-config error (junctions): {e}")
    
    def reject(self):
        """Handle dialog rejection (Cancel button clicked)."""
        self._save_configuration()
        super().reject()
        """Set up UI components with proper configuration."""
        # Configure layer combo boxes with geometry filtering
        self.pipesLayerCombo.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.junctionsLayerCombo.setFilters(QgsMapLayerProxyModel.PointLayer)
        
        # Set up validation display
        self.validationTextEdit.setReadOnly(True)
        self.validationTextEdit.setMaximumHeight(100)
        
        # Configure export button
        self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
       
    
    def _validate_configuration(self):
        """Validate the complete export configuration."""
        try:
            self.validationTextEdit.clear()
            
            # Get current configuration
            config = self._get_export_configuration()
            
            # Perform comprehensive validation
            validation_result = self.validator.validate_complete_configuration(config)
            
            # Display validation results
            self._display_validation_results(validation_result)
            
            # Enable/disable export button based on validation
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(validation_result.is_valid)
            
            if validation_result.is_valid:
                self._show_validation_message("Configuration is valid - ready to export", "success")
            else:
                error_count = len(validation_result.errors)
                warning_count = len(validation_result.warnings)
                self._show_validation_message(
                    f"Validation failed: {error_count} errors, {warning_count} warnings", 
                    "error"
                )
                
        except Exception as e:
            error_msg = self.error_formatter.format_export_error("validation_failed", error=str(e))
            self._show_error_message(error_msg)
            self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
    
    def _execute_export(self):
        """Execute the DXF export with comprehensive error handling."""
        try:
            # Get and validate configuration
            config = self.get_export_configuration()
            
            # Create progress dialog
            from qgis.PyQt.QtWidgets import QProgressDialog
            progress_dialog = QProgressDialog("Exporting DXF...", "Cancel", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.show()
            
            def progress_callback(progress: int, message: str):
                progress_dialog.setValue(progress)
                progress_dialog.setLabelText(message)
                if progress_dialog.wasCanceled():
                    raise ExportError("Export cancelled by user")
            
            # Create exporter and execute
            exporter = DXFExporter(progress_callback=progress_callback)
            success, message, statistics = exporter.export_with_error_handling(config)
            
            progress_dialog.close()
            
            if success:
                self._show_success_message(message, statistics)
            else:
                self._show_export_error(message, statistics)
                
        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.close()
            
            error_msg = self.error_formatter.format_export_error("export_failed", error_details=str(e))
            self._show_error_message(error_msg)
    
    def _get_export_configuration(self) -> ExportConfiguration:
        """Get current export configuration from UI."""
        # Get layer mappings
        pipes_mapping = self.configuration.get_pipes_mapping()
        junctions_mapping = self.configuration.get_junctions_mapping()
        
        # Update layer IDs from current selection
        pipes_layer = self.pipesLayerCombo.currentLayer()
        if pipes_layer and pipes_mapping:
            pipes_mapping.layer_id = pipes_layer.id()
            pipes_mapping.layer_name = pipes_layer.name()
        
        junctions_layer = self.junctionsLayerCombo.currentLayer()
        if junctions_layer and junctions_mapping:
            junctions_mapping.layer_id = junctions_layer.id()
            junctions_mapping.layer_name = junctions_layer.name()
        
        # Create configuration
        config = ExportConfiguration(
            pipes_mapping=pipes_mapping,
            junctions_mapping=junctions_mapping,
            output_path=self.outputPathEdit.text(),
            scale_factor=self.scaleFactorSpinBox.value(),
            layer_prefix=self.layerPrefixEdit.text(),
            template_path=None,
            include_arrows=self.includeArrowsCheckBox.isChecked(),
            include_labels=self.includeLabelsCheckBox.isChecked(),
            include_elevations=self.includeElevationsCheckBox.isChecked(),
            export_node_id=self.exportNodeIdCheckBox.isChecked(),
            include_slope_unit=self.includeSlopeUnitCheckBox.isChecked(),
            label_format=self.labelFormatEdit.text()
        )
        
        return config
    
    def _display_validation_results(self, result: ValidationResult):
        """Display validation results in the UI."""
        self.validationTextEdit.clear()
        
        if result.errors:
            self.validationTextEdit.append("ERRORS:")
            for error in result.errors:
                self.validationTextEdit.append(f"  • {error}")
            self.validationTextEdit.append("")
        
        if result.warnings:
            self.validationTextEdit.append("WARNINGS:")
            for warning in result.warnings:
                self.validationTextEdit.append(f"  • {warning}")
            self.validationTextEdit.append("")
        
        if result.info:
            self.validationTextEdit.append("INFORMATION:")
            for info in result.info:
                self.validationTextEdit.append(f"  • {info}")
    
    def _show_validation_message(self, message: str, level: str = "info"):
        """Show validation message in status area."""
        # Color coding based on level
        colors = {
            "info": "blue",
            "success": "green", 
            "warning": "orange",
            "error": "red"
        }
        
        color = colors.get(level, "black")
        self.validationTextEdit.setText(f'<span style="color: {color};">{message}</span>')
    
    def _show_error_message(self, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, "Export Error", message)
    
    def _show_success_message(self, message: str, statistics: Dict):
        """Show success message with export statistics."""
        detailed_message = message
        
        if statistics:
            stats = statistics.get('statistics')
            if stats:
                detailed_message += f"\n\nStatistics:\n{stats.get_summary()}"
        
        QMessageBox.information(self, "Export Successful", detailed_message)
    
    def _show_export_error(self, message: str, statistics: Dict):
        """Show export error with detailed statistics."""
        detailed_message = message
        
        if statistics:
            recent_errors = statistics.get('recent_errors', [])
            if recent_errors:
                detailed_message += "\n\nRecent errors:\n"
                for error in recent_errors[:5]:  # Show first 5 errors
                    detailed_message += f"• {error}\n"
        
        QMessageBox.warning(self, "Export Completed with Issues", detailed_message)
    
    def _on_configuration_changed(self):
        """Handle configuration changes for real-time validation."""
        # Disable export button until validation is run
        self.buttonBox.button(self.buttonBox.Ok).setEnabled(False)
        
        # Show that validation is needed
        self._show_validation_message("Configuration changed - click Validate to check", "warning")
    
    def _load_configuration(self):
        """Load saved configuration."""
        try:
            config = self.configuration.load_export_configuration()
            if config:
                # Restore UI state from configuration
                self.outputPathEdit.setText(config.output_path or "")
                self.scaleFactorSpinBox.setValue(config.scale_factor)
                self.layerPrefixEdit.setText(config.layer_prefix)
                self.includeArrowsCheckBox.setChecked(config.include_arrows)
                self.includeLabelsCheckBox.setChecked(config.include_labels)
                self.includeElevationsCheckBox.setChecked(config.include_elevations)
                self.labelFormatEdit.setText(config.label_format)
                
        except Exception as e:
            # Non-critical error - just log it
            self._show_validation_message(f"Could not load saved configuration: {e}", "warning")
    
    def _save_full_configuration(self):
        """Save current full export configuration."""
        try:
            config = self.get_export_configuration()
            if config:
                self.configuration.save_export_configuration(config)
        except Exception as e:
            # Non-critical error - just log it
            print(f"Could not save full configuration: {e}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Save basic configuration before closing
        self._save_configuration()
        super().closeEvent(event)