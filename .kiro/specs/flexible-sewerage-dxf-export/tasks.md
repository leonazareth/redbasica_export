# Implementation Plan

- [x] 1. Set up enhanced plugin structure and core dependencies
  - [x] 1.1 Copy and integrate QEsg addon libraries


    - Copy ezdxf and c3d libraries from QEsg/addon/ to redbasica_export/addon/
    - Copy QEsg_template.dxf to redbasica_export/resources/templates/
    - Set up bundled library imports from addon/ directory with proper path handling
    - Test ezdxf import and basic DXF creation functionality
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Create enhanced plugin structure


    - Modify existing plugin structure to support new modular architecture
    - Create core package directories (ui/, core/, resources/)
    - Update metadata.txt with new plugin information and dependencies
    - Set up proper __init__.py files for all packages
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement core data structures and field definitions




  - [x] 2.1 Create field definitions and data classes







    - Implement GeometryType, FieldType, RequiredField, LayerMapping, and ExportConfiguration dataclasses
    - Create SewageNetworkFields class with flexible field definitions (not restricted to QEsg names)
    - Add calculated field support for depth and slope calculations when source data is available
    - Add field validation rules and default values for flexible field assignments
    - _Requirements: 2.1, 2.2, 8.1, 9.1, 9.3_

  - [x] 2.2 Implement robust data conversion system







    - Create DataConverter class with methods for string-to-number conversion
    - Implement handling of Portuguese decimal notation (comma to dot conversion)
    - Add NULL/None value handling with appropriate defaults
    - Create comprehensive type conversion with graceful error handling
    - Add unit tests for various data format scenarios (string numbers, NULL values, type mismatches)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 2.3 Implement configuration management system


    - Create Configuration class for settings persistence using QSettings
    - Implement save/load methods for export configurations and user preferences
    - Add template path management and field mapping storage
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 3. Build flexible layer management and validation system





  - [x] 3.1 Implement LayerManager class for ANY project layers


    - Create methods to discover and list ALL project layers regardless of naming conventions
    - Implement geometry type filtering (line layers for pipes, point layers for junctions) without name restrictions
    - Add layer field extraction and type mapping from QGIS to plugin field types for ANY field names
    - Create sample data extraction for layer preview and mapping verification
    - Remove any hardcoded layer name dependencies (no requirement for 'PIPES' or 'JUNCTIONS' layers)
    - _Requirements: 1.1, 1.2, 1.5, 4.1, 4.2_

  - [x] 3.2 Implement flexible AttributeMapper class with robust data conversion


    - Create auto-mapping suggestion logic that suggests common field patterns (including QEsg patterns as suggestions, not requirements)
    - Implement completely manual field mapping capability for ANY field names
    - Add comprehensive data type conversion system (DataConverter class) to handle:
      - String representations of numbers ("1.05", "2,50") converted to proper numeric types
      - NULL/None values converted to appropriate defaults (0 for numbers, "" for strings)
      - Portuguese decimal notation (comma to dot conversion)
      - Type mismatches with graceful fallback to defaults
    - Create feature data extraction using user-configured mappings with automatic type conversion
    - Add support for calculated fields when source data is available (depth = ground - invert, slope = elevation difference / length)
    - Implement graceful handling when expected fields are not mapped or conversion fails
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.2, 4.3, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4, 10.5_
-

- [x] 4. Create user interface components




  - [x] 4.1 Design and implement flexible main export dialog UI


    - Create main_export_dialog.ui with layer selection dropdowns populated with ALL project layers
    - Implement MainExportDialog class with QgsMapLayerComboBox showing all available layers (not filtered by name)
    - Add geometry type filtering to show only appropriate layers (lines for pipes, points for junctions)
    - Add real-time validation feedback that works with any selected layers
    - Connect configuration buttons to attribute mapping dialogs for flexible field mapping
    - _Requirements: 1.1, 1.2, 1.5, 4.3, 4.4, 5.4_

  - [x] 4.2 Implement layer selector dialog


    - Create layer_selector_dialog.ui with filtering and preview capabilities
    - Implement LayerSelectorDialog class with geometry type filtering
    - Add layer information display, field list, and sample data table
    - Integrate with LayerManager for layer discovery and validation
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 4.3 Implement flexible attribute mapper dialog


    - Create attribute_mapper_dialog.ui with mapping tables showing ALL available layer fields
    - Implement AttributeMapperDialog class with suggestion-based auto-mapping (not enforcement)
    - Add required/optional field tables with dropdown selectors populated with ANY layer field names
    - Implement default value configuration for unmapped fields
    - Add completely manual mapping capability when auto-suggestions don't work
    - Add real-time validation that works with flexible field assignments
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.2, 4.3, 9.3, 9.4_

- [x] 5. Build DXF export engine




  - [x] 5.1 Implement geometry processing utilities


    - Create GeometryProcessor class with azimuth, midpoint, and point-along-line calculations
    - Implement perpendicular point generation and text rotation alignment
    - Add arrow placement calculations and coordinate transformation utilities
    - _Requirements: 3.2, 3.4_

  - [x] 5.2 Implement template management system


    - Create TemplateManager class for DXF template discovery and validation
    - Copy and adapt QEsg_template.dxf with predefined blocks (pv_dados_NE, pv_dados_NO, pv_dados_SE, pv_dados_SO, tr_curto, notq)
    - Implement template loading from bundled template or create default if missing
    - Add block library management for arrow blocks (SETA) and manhole data blocks
    - Create ROMANS text style and standard layer definitions
    - _Requirements: 3.1, 3.5_

  - [x] 5.3 Implement flexible core DXF exporter


    - Create DXFExporter class with ezdxf integration from bundled addon library
    - Implement DXF document initialization with QEsg template loading
    - Add QEsg-compatible layer structure creation (REDE, NUMERO, TEXTO, TEXTOPVS, PV, NUMPV, SETA, NO, AUX, LIDER)
    - Implement pipe export that works with ANY user-selected layer and field mappings
    - Add pipe ID labels above pipes using mapped pipe_id field (regardless of original field name)
    - Add length-diameter-slope labels below pipes using mapped fields with graceful fallback for missing data
    - Implement flow arrows using SETA blocks for reaches longer than 20 scale units
    - Add manhole elevation blocks (pv_dados_XX) with mapped elevation data
    - Implement calculated depth values when ground and invert elevations are available
    - Add extended entity data (XDATA) using mapped field values
    - Handle missing or unmapped fields gracefully with default values or feature skipping
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2, 8.3, 8.4, 8.5_
-

- [x] 6. Enhance existing plugin integration




  - [x] 6.1 Update main plugin class


    - Modify redbasica_export.py to integrate new export functionality
    - Update plugin initialization to check bundled dependencies
    - Integrate new MainExportDialog with existing dockwidget structure
    - Add proper error handling and user feedback through QGIS message bar
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 6.2 Enhance dockwidget interface


    - Update redbasica_export_dockwidget_base.ui to include new export controls
    - Modify RedBasicaExportDockWidget to integrate with new export system
    - Add layer selection shortcuts and quick export options
    - Implement progress reporting and status updates during export
    - _Requirements: 1.1, 4.4, 7.5_
-

- [x] 7. Implement comprehensive error handling and validation




  - Create ValidationError, LayerValidationError, MappingValidationError, and ExportError exception classes
  - Implement graceful error recovery with feature skipping and progress reporting
  - Add comprehensive validation at layer, mapping, and export levels
  - Create user-friendly error messages with suggested solutions and multilingual support
  - Implement file permission checking and path validation for security
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Add internationalization support





  - Set up translation infrastructure with .ts files for multiple languages
  - Implement translatable strings throughout the UI and error messages
  - Add localized field display names and descriptions
  - Create translation files for Portuguese (primary) and English
  - Integrate QTranslator with QGIS locale detection
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Create comprehensive testing and validation







  - [x] 9.1 Implement unit tests for core components


    - Create tests for LayerManager layer discovery and validation methods
    - Test AttributeMapper auto-mapping algorithms and validation logic
    - Test GeometryProcessor calculations and coordinate transformations
    - Test Configuration save/load functionality and settings persistence
    - _Requirements: All requirements validation_

  - [x] 9.2 Create integration tests for export workflows



    - Test complete export workflows with various layer types and configurations
    - Validate DXF output structure and entity creation
    - Test error handling scenarios with invalid data and missing permissions
    - Verify template loading and block usage functionality
    - _Requirements: All requirements integration_

- [x] 10. Finalize plugin packaging and documentation





  - Update metadata.txt with final plugin information and dependencies
  - Create comprehensive user documentation with screenshots and examples
  - Add code documentation and developer comments throughout
  - Package plugin with bundled libraries and test installation
  - Create example datasets and configuration templates for testing
  - _Requirements: All requirements completion_