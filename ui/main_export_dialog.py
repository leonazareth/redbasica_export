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
from .attribute_mapper_dialog import AttributeMapperDialog

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
        self.setupUi(self)
        
        self.layer_manager = layer_manager
        self.configuration = Configuration()
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
        self.browseTemplateButton.clicked.connect(self._browse_template_file)
        
        # Preview button
        self.previewButton.clicked.connect(self._preview_export)
        
        # Validation triggers
        self.outputPathEdit.textChanged.connect(self._update_validation)
        self.scaleFactorSpinBox.valueChanged.connect(self._update_validation)
        self.layerPrefixEdit.textChanged.connect(self._update_validation)
        self.templatePathEdit.textChanged.connect(self._update_validation)
        
        # Advanced options
        self.includeArrowsCheckBox.toggled.connect(self._update_validation)
        self.includeLabelsCheckBox.toggled.connect(self._update_validation)
        self.includeElevationsCheckBox.toggled.connect(self._update_validation)
        self.labelFormatEdit.textChanged.connect(self._update_validation)
    
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
            # Reset mapping when layer changes
            self.pipes_mapping = None
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
            # Reset mapping when layer changes
            self.junctions_mapping = None
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
            required_fields=SewageNetworkFields.PIPES_REQUIRED,
            optional_fields=SewageNetworkFields.PIPES_OPTIONAL
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
            required_fields=SewageNetworkFields.JUNCTIONS_REQUIRED,
            optional_fields=SewageNetworkFields.JUNCTIONS_OPTIONAL
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
    
    def _browse_template_file(self):
        """Browse for DXF template file."""
        current_path = self.templatePathEdit.text()
        if not current_path:
            current_path = os.path.expanduser("~")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DXF Template",
            current_path,
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.templatePathEdit.setText(file_path)
    
    def _preview_export(self):
        """Generate and display export preview."""
        try:
            config = self.get_export_configuration()
            if not config:
                return
            
            # Generate preview information
            preview_info = self._generate_preview_info(config)
            
            # Display preview
            preview_text = self._format_preview_text(preview_info)
            
            QMessageBox.information(
                self, "Export Preview", preview_text
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Preview Error",
                f"Failed to generate export preview:\n{str(e)}"
            )
    
    def _generate_preview_info(self, config: ExportConfiguration) -> Dict:
        """Generate preview information for the export."""
        info = {
            'pipes_layer': config.pipes_mapping.layer_name if config.pipes_mapping else None,
            'junctions_layer': config.junctions_mapping.layer_name if config.junctions_mapping else None,
            'output_path': config.output_path,
            'scale_factor': config.scale_factor,
            'layer_prefix': config.layer_prefix,
            'template_path': config.template_path,
            'options': {
                'arrows': config.include_arrows,
                'labels': config.include_labels,
                'elevations': config.include_elevations
            }
        }
        
        # Count features if layers are available
        if config.pipes_mapping and config.pipes_mapping.layer_id:
            layer = QgsProject.instance().mapLayer(config.pipes_mapping.layer_id)
            if layer:
                info['pipes_count'] = layer.featureCount()
        
        if config.junctions_mapping and config.junctions_mapping.layer_id:
            layer = QgsProject.instance().mapLayer(config.junctions_mapping.layer_id)
            if layer:
                info['junctions_count'] = layer.featureCount()
        
        return info
    
    def _format_preview_text(self, info: Dict) -> str:
        """Format preview information as readable text."""
        lines = ["Export Configuration Preview:", ""]
        
        # Layers
        lines.append("Layers:")
        if info.get('pipes_layer'):
            count = info.get('pipes_count', 'unknown')
            lines.append(f"  • Pipes: {info['pipes_layer']} ({count} features)")
        else:
            lines.append("  • Pipes: Not selected")
        
        if info.get('junctions_layer'):
            count = info.get('junctions_count', 'unknown')
            lines.append(f"  • Junctions: {info['junctions_layer']} ({count} features)")
        else:
            lines.append("  • Junctions: Not selected")
        
        lines.append("")
        
        # Output settings
        lines.append("Output Settings:")
        lines.append(f"  • File: {info['output_path']}")
        lines.append(f"  • Scale Factor: {info['scale_factor']}")
        lines.append(f"  • Layer Prefix: {info['layer_prefix']}")
        
        if info['template_path']:
            lines.append(f"  • Template: {info['template_path']}")
        else:
            lines.append("  • Template: Default template will be used")
        
        lines.append("")
        
        # Options
        lines.append("Export Options:")
        options = info['options']
        lines.append(f"  • Flow Arrows: {'Yes' if options['arrows'] else 'No'}")
        lines.append(f"  • Pipe Labels: {'Yes' if options['labels'] else 'No'}")
        lines.append(f"  • Elevation Data: {'Yes' if options['elevations'] else 'No'}")
        
        return "\n".join(lines)
    
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
        
        # Check template path if specified
        template_path = self.templatePathEdit.text().strip()
        if template_path and not os.path.exists(template_path):
            errors.append(f"Template file does not exist: {template_path}")
        
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
            template_path=self.templatePathEdit.text().strip() or None,
            include_arrows=self.includeArrowsCheckBox.isChecked(),
            include_labels=self.includeLabelsCheckBox.isChecked(),
            include_elevations=self.includeElevationsCheckBox.isChecked(),
            label_format=self.labelFormatEdit.text().strip()
        )
    
    def _load_configuration(self):
        """Load saved configuration settings."""
        try:
            # Load basic settings
            self.scaleFactorSpinBox.setValue(
                self.configuration.get_setting('scale_factor', 2000)
            )
            self.layerPrefixEdit.setText(
                self.configuration.get_setting('layer_prefix', 'ESG_')
            )
            self.templatePathEdit.setText(
                self.configuration.get_setting('template_path', '')
            )
            
            # Load advanced options
            self.includeArrowsCheckBox.setChecked(
                self.configuration.get_setting('include_arrows', True)
            )
            self.includeLabelsCheckBox.setChecked(
                self.configuration.get_setting('include_labels', True)
            )
            self.includeElevationsCheckBox.setChecked(
                self.configuration.get_setting('include_elevations', True)
            )
            self.labelFormatEdit.setText(
                self.configuration.get_setting('label_format', '{length:.0f}-{diameter:.0f}-{slope:.5f}')
            )
            
            # Load last output path
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
            self.configuration.set_setting('template_path', self.templatePathEdit.text())
            self.configuration.set_setting('include_arrows', self.includeArrowsCheckBox.isChecked())
            self.configuration.set_setting('include_labels', self.includeLabelsCheckBox.isChecked())
            self.configuration.set_setting('include_elevations', self.includeElevationsCheckBox.isChecked())
            self.configuration.set_setting('label_format', self.labelFormatEdit.text())
            self.configuration.set_setting('last_output_path', self.outputPathEdit.text())
            
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
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Layer selection changes
        self.pipesLayerCombo.layerChanged.connect(self._on_pipes_layer_changed)
        self.junctionsLayerCombo.layerChanged.connect(self._on_junctions_layer_changed)
        
        # Configuration buttons
        self.configurePipesButton.clicked.connect(self._configure_pipes_mapping)
        self.configureJunctionsButton.clicked.connect(self._configure_junctions_mapping)
        
        # Output path selection
        self.browseOutputButton.clicked.connect(self._browse_output_file)
        self.browseTemplateButton.clicked.connect(self._browse_template_file)
        
        # Export and validation
        self.previewButton.clicked.connect(self._validate_configuration)
        self.buttonBox.accepted.connect(self._execute_export)
        
        # Real-time validation triggers
        self.outputPathEdit.textChanged.connect(self._on_configuration_changed)
        self.scaleFactorSpinBox.valueChanged.connect(self._on_configuration_changed)
        self.layerPrefixEdit.textChanged.connect(self._on_configuration_changed)
    
    def _on_validation_progress(self, progress: int, message: str):
        """Handle validation progress updates."""
        # Progress updates shown in validation text
        if message:
            self.validationTextEdit.append(f"Progress: {message}")
    
    def _on_pipes_layer_changed(self, layer: QgsVectorLayer):
        """Handle pipes layer selection change."""
        if layer and layer.isValid():
            # Validate layer compatibility
            validation_result = self.layer_manager.validate_layer_compatibility(layer, GeometryType.LINE)
            
            if validation_result.is_valid:
                self.configurePipesButton.setEnabled(True)
                self._show_validation_message("Pipes layer selected successfully", "info")
            else:
                self.configurePipesButton.setEnabled(False)
                error_msg = "\n".join(validation_result.errors)
                self._show_validation_message(f"Pipes layer validation failed:\n{error_msg}", "error")
        else:
            self.configurePipesButton.setEnabled(False)
            self._show_validation_message("No pipes layer selected", "warning")
        
        self._on_configuration_changed()
    
    def _on_junctions_layer_changed(self, layer: QgsVectorLayer):
        """Handle junctions layer selection change."""
        if layer and layer.isValid():
            # Validate layer compatibility
            validation_result = self.layer_manager.validate_layer_compatibility(layer, GeometryType.POINT)
            
            if validation_result.is_valid:
                self.configureJunctionsButton.setEnabled(True)
                self._show_validation_message("Junctions layer selected successfully", "info")
            else:
                self.configureJunctionsButton.setEnabled(False)
                error_msg = "\n".join(validation_result.errors)
                self._show_validation_message(f"Junctions layer validation failed:\n{error_msg}", "error")
        else:
            self.configureJunctionsButton.setEnabled(False)
            self._show_validation_message("No junctions layer selected (optional)", "info")
        
        self._on_configuration_changed()
    
    def _configure_pipes_mapping(self):
        """Open pipes attribute mapping dialog."""
        pipes_layer = self.pipesLayerCombo.currentLayer()
        if not pipes_layer:
            self._show_error_message("Please select a pipes layer first")
            return
        
        try:
            dialog = AttributeMapperDialog(
                layer_manager=self.layer_manager,
                parent=self
            )
            
            # Configure the dialog for pipes layer
            from ..core.field_definitions import SewageNetworkFields
            dialog.configure_for_layer(
                layer=pipes_layer,
                geometry_type=GeometryType.LINE,
                required_fields=SewageNetworkFields.get_pipes_required_fields(),
                optional_fields=SewageNetworkFields.get_pipes_optional_fields()
            )
            
            if dialog.exec_() == QDialog.Accepted:
                mapping = dialog.get_mapping()
                # Store mapping configuration
                self.pipes_mapping = mapping
                self._show_validation_message("Pipes mapping configured successfully", "info")
                self._update_validation()
                
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            error_msg = self.error_formatter.format_mapping_error("mapping_dialog_failed", error=error_details)
            self._show_error_message(error_msg)
    
    def _configure_junctions_mapping(self):
        """Open junctions attribute mapping dialog."""
        junctions_layer = self.junctionsLayerCombo.currentLayer()
        if not junctions_layer:
            self._show_error_message("Please select a junctions layer first")
            return
        
        try:
            dialog = AttributeMapperDialog(
                layer_manager=self.layer_manager,
                parent=self
            )
            
            # Configure the dialog for junctions layer
            from ..core.field_definitions import SewageNetworkFields
            dialog.configure_for_layer(
                layer=junctions_layer,
                geometry_type=GeometryType.POINT,
                required_fields=SewageNetworkFields.get_junctions_required_fields(),
                optional_fields=SewageNetworkFields.get_junctions_optional_fields()
            )
            
            if dialog.exec_() == QDialog.Accepted:
                mapping = dialog.get_mapping()
                # Store mapping configuration
                self.junctions_mapping = mapping
                self._show_validation_message("Junctions mapping configured successfully", "info")
                self._update_validation()
                
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            error_msg = self.error_formatter.format_mapping_error("mapping_dialog_failed", error=error_details)
            self._show_error_message(error_msg)
    
    def _browse_output_path(self):
        """Browse for output DXF file path."""
        current_path = self.outputPathEdit.text()
        if not current_path:
            current_path = os.path.expanduser("~/export.dxf")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output DXF File",
            current_path,
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.outputPathEdit.setText(file_path)
    
    def _browse_template_path(self):
        """Browse for template DXF file path."""
        current_path = self.templatePathEdit.text()
        if not current_path:
            current_path = os.path.expanduser("~")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template DXF File",
            current_path,
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.templatePathEdit.setText(file_path)
    
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
            template_path=self.templatePathEdit.text() or None,
            include_arrows=self.includeArrowsCheckBox.isChecked(),
            include_labels=self.includeLabelsCheckBox.isChecked(),
            include_elevations=self.includeElevationsCheckBox.isChecked(),
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
                self.templatePathEdit.setText(config.template_path or "")
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