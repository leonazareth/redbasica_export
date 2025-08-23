# Requirements Document

## Introduction

This plugin provides a flexible DXF export solution for sewerage network designs in QGIS. Unlike the original QEsg plugin that requires hardcoded layers named 'PIPES' and 'JUNCTIONS' with specific field names, this plugin allows users to select ANY layers from their current QGIS project and map ANY field names to the required sewerage network attributes. The plugin maintains the same high-quality DXF output and styling as the original QEsg plugin while providing maximum flexibility for different data structures, layer names, and field naming conventions.

## Requirements

### Requirement 1

**User Story:** As a QGIS user, I want to select ANY pipe and junction layers from my current project regardless of their names, so that I can export sewerage networks without being restricted to specific layer naming conventions like the original QEsg plugin.

#### Acceptance Criteria

1. WHEN the plugin is launched THEN the system SHALL display ALL vector layers from the current QGIS project for user selection
2. WHEN filtering by geometry type THEN the system SHALL show only line layers for pipe selection and point layers for junction selection
3. WHEN no suitable layers exist THEN the system SHALL display a warning message to the user
4. WHEN a layer is selected THEN the system SHALL display the layer's field information and sample data for mapping verification
5. WHEN layers have different names than 'PIPES' or 'JUNCTIONS' THEN the system SHALL still allow selection and processing

### Requirement 2

**User Story:** As a sewerage network designer, I want to map ANY of my layer attributes to standard sewerage network fields, so that the exported DXF contains the correct information regardless of my field naming conventions or data structure.

#### Acceptance Criteria

1. WHEN configuring attribute mapping THEN the system SHALL display required fields (pipe_id, upstream_node, downstream_node, length, diameter, upstream_invert, downstream_invert, upstream_ground, downstream_ground, slope) for pipes
2. WHEN configuring attribute mapping THEN the system SHALL display required fields (node_id) for junctions with optional ground elevation
3. WHEN auto-mapping is requested THEN the system SHALL attempt to match ANY layer field names to required fields based on common naming patterns (including QEsg patterns as suggestions, not requirements)
4. WHEN required fields are not mapped THEN the system SHALL allow users to set default values or leave unmapped
5. WHEN field types don't match THEN the system SHALL display validation warnings but still allow export with type conversion

### Requirement 3

**User Story:** As a CAD user, I want the exported DXF to maintain proper styling and organization identical to the original QEsg plugin, so that I can use it directly in AutoCAD or other CAD software.

#### Acceptance Criteria

1. WHEN exporting THEN the system SHALL create organized DXF layers (REDE, NUMERO, TEXTO, TEXTOPVS, PV, NUMPV, SETA, NO, AUX, LIDER) with configurable prefixes
2. WHEN flow arrows are enabled THEN the system SHALL add directional arrows on pipe segments longer than 20 scale units using block references
3. WHEN labels are enabled THEN the system SHALL add pipe ID labels above pipes and length-diameter-slope labels below pipes
4. WHEN elevations are enabled THEN the system SHALL include 3D coordinates and manhole elevation blocks with CT, CF, and PROF attributes
5. WHEN using templates THEN the system SHALL load the QEsg template DXF with predefined blocks (pv_dados_NE, pv_dados_NO, pv_dados_SE, pv_dados_SO, tr_curto, notq)

### Requirement 4

**User Story:** As a project manager, I want to validate my layer configuration before export, so that I can ensure data quality and completeness.

#### Acceptance Criteria

1. WHEN validating layers THEN the system SHALL check geometry types match requirements
2. WHEN validating mappings THEN the system SHALL verify all required fields are mapped or have default values
3. WHEN validation fails THEN the system SHALL display specific error messages
4. WHEN previewing export THEN the system SHALL show a summary of what will be exported
5. WHEN validation passes THEN the system SHALL enable the export button

### Requirement 5

**User Story:** As a frequent user, I want my export settings to be remembered, so that I can quickly repeat exports with the same configuration.

#### Acceptance Criteria

1. WHEN closing the plugin THEN the system SHALL save the last used export configuration
2. WHEN reopening the plugin THEN the system SHALL restore the previous settings
3. WHEN changing scale factors THEN the system SHALL remember the preferred scale
4. WHEN using custom templates THEN the system SHALL remember the template path
5. WHEN configuring label formats THEN the system SHALL save custom format strings

### Requirement 6

**User Story:** As a multilingual user, I want the plugin interface in my preferred language, so that I can use it effectively.

#### Acceptance Criteria

1. WHEN the plugin loads THEN the system SHALL detect the QGIS locale setting
2. WHEN translation files exist THEN the system SHALL display the interface in the user's language
3. WHEN translations are missing THEN the system SHALL fall back to English
4. WHEN field names are displayed THEN the system SHALL use localized display names
5. WHEN error messages are shown THEN the system SHALL display them in the user's language

### Requirement 7

**User Story:** As a network designer, I want comprehensive error handling, so that I can understand and resolve any export issues.

#### Acceptance Criteria

1. WHEN file access fails THEN the system SHALL display specific file permission errors
2. WHEN DXF creation fails THEN the system SHALL show detailed error messages with suggested solutions
3. WHEN geometry processing fails THEN the system SHALL skip invalid features and report the count
4. WHEN template loading fails THEN the system SHALL fall back to default template creation
5. WHEN export completes successfully THEN the system SHALL display a success message with file location

### Requirement 8

**User Story:** As a data analyst, I want to export additional metadata and calculated values, so that the DXF contains comprehensive information about the sewerage network.

#### Acceptance Criteria

1. WHEN extended data is enabled THEN the system SHALL add pipe metadata as DXF XDATA for software compatibility
2. WHEN slope calculation is available THEN the system SHALL compute pipe slopes from invert elevations and include in labels
3. WHEN depth calculation is possible THEN the system SHALL compute manhole depths from ground and invert elevations
4. WHEN additional mapped fields exist THEN the system SHALL include them in the DXF output appropriately
5. WHEN calculated fields are missing source data THEN the system SHALL use default values or skip calculations gracefully

### Requirement 9

**User Story:** As a user with existing sewerage network data, I want the plugin to suggest field mappings based on common naming patterns, so that I can quickly configure the export without manual mapping of every field.

#### Acceptance Criteria

1. WHEN auto-mapping is requested THEN the system SHALL suggest mappings for common field naming patterns (including QEsg patterns like DC_ID, PVM, PVJ, CCM, CCJ as well as generic patterns like ID, LENGTH, DIAMETER)
2. WHEN multiple potential matches exist THEN the system SHALL present options for user selection
3. WHEN suggested mappings are applied THEN the system SHALL allow users to modify or override any mapping
4. WHEN no automatic matches are found THEN the system SHALL allow completely manual field mapping
5. WHEN field mapping is complete THEN the system SHALL validate that sufficient data exists for DXF export

### Requirement 10

**User Story:** As a user with data stored in various formats, I want the plugin to handle different data types automatically, so that I can export networks regardless of how my numeric data is stored (as numbers or formatted strings).

#### Acceptance Criteria

1. WHEN numeric fields are stored as strings THEN the system SHALL convert string representations like "1.05" or "2,50" to proper numeric values
2. WHEN NULL or empty values are encountered THEN the system SHALL use appropriate default values (0 for numeric fields, empty string for text fields)
3. WHEN Portuguese decimal notation is used THEN the system SHALL handle comma decimal separators by converting to dot notation
4. WHEN field types don't match expected types THEN the system SHALL attempt automatic conversion with fallback to defaults
5. WHEN conversion fails THEN the system SHALL log the issue and continue processing with default values rather than failing completely