# Internationalization (i18n) Guide

This document describes the internationalization system implemented in the RedBasica Export plugin.

## Overview

The plugin supports multiple languages through Qt's translation system, with comprehensive translation support for:

- User interface elements
- Field display names and descriptions  
- Error messages and user feedback
- Tooltips and help text

## Supported Languages

- **English (en)** - Source language
- **Portuguese (pt)** - Primary target language (Brazilian Portuguese)

Additional languages can be easily added by creating new translation files.

## Architecture

### I18nManager Class

The `core/i18n_manager.py` module provides the central translation management:

```python
from core.i18n_manager import tr, init_i18n

# Initialize in plugin
i18n_manager = init_i18n(plugin_directory)

# Use global translation function
translated_text = tr("Text to translate")
```

### Key Features

1. **Automatic Locale Detection**: Detects QGIS locale settings
2. **Fallback Support**: Falls back to English if translation not available
3. **Field Localization**: Provides localized field names and descriptions
4. **Error Message Localization**: Contextual error messages with parameters
5. **UI Text Management**: Centralized UI text with translation keys

## File Structure

```
i18n/
├── redbasica_export_en.ts    # English translation source
├── redbasica_export_pt.ts    # Portuguese translations
├── redbasica_export_en.qm    # Compiled English (fallback)
└── redbasica_export_pt.qm    # Compiled Portuguese
```

## Translation Workflow

### 1. Adding New Translatable Strings

Use the `tr()` function for all user-visible text:

```python
from core.i18n_manager import tr

# Simple translation
message = tr("Export completed successfully")

# With context
message = tr("Export", "ButtonText")
```

### 2. Field Display Names

Field definitions automatically use translations:

```python
RequiredField(
    name="pipe_id",
    display_name=tr("Pipe Identifier"),
    description=tr("Unique identifier for each pipe segment"),
    # ...
)
```

### 3. Error Messages

Use the error message system for consistent, localized errors:

```python
error_msg = i18n_manager.get_error_message(
    'layer_not_found', 
    layer_name='MyLayer'
)
```

### 4. UI Text

Access UI text through the i18n manager:

```python
title = i18n_manager.get_ui_text('main_dialog_title')
button_text = i18n_manager.get_ui_text('export')
```

## Translation Files

### .ts File Format

Translation files use Qt's .ts XML format:

```xml
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="pt_BR" sourcelanguage="en">
<context>
    <name>RedBasicaExport</name>
    <message>
        <source>Pipe Identifier</source>
        <translation>Identificador da Tubulação</translation>
    </message>
</context>
</TS>
```

### Compilation

Compile .ts files to .qm format using the provided script:

```bash
python scripts/compile_translations.py
```

## Available Translation Categories

### Field Names
- Pipe fields: pipe_id, upstream_node, downstream_node, length, diameter, etc.
- Junction fields: node_id, ground_elevation, invert_elevation, etc.
- Calculated fields: upstream_depth, downstream_depth, calculated_slope

### UI Elements
- Dialog titles and group boxes
- Button labels and menu items
- Status messages and tooltips
- Validation feedback

### Error Messages
- Layer validation errors
- Field mapping errors
- Export process errors
- File access errors

## Adding New Languages

To add support for a new language (e.g., Spanish):

1. **Create Translation File**:
   ```bash
   cp i18n/redbasica_export_en.ts i18n/redbasica_export_es.ts
   ```

2. **Update Language Code**:
   ```xml
   <TS version="2.1" language="es" sourcelanguage="en">
   ```

3. **Translate Strings**:
   Update all `<translation>` elements with Spanish text.

4. **Update I18nManager**:
   ```python
   self.available_locales = ['en', 'pt', 'es']
   ```

5. **Compile Translations**:
   ```bash
   python scripts/compile_translations.py
   ```

## Best Practices

### 1. Translation Keys
- Use descriptive, context-aware keys
- Keep keys consistent across similar UI elements
- Avoid hardcoded strings in code

### 2. Parameterized Messages
Use parameters for dynamic content:

```python
# Good
tr("Layer '{layer_name}' contains {count} features")

# Avoid
tr("Layer") + " " + layer_name + " " + tr("contains") + " " + str(count)
```

### 3. Context Information
Provide context for ambiguous terms:

```python
tr("Export", "ButtonText")  # Button label
tr("Export", "MenuAction")  # Menu item
tr("Export", "ProcessName") # Process description
```

### 4. Pluralization
Handle plural forms appropriately:

```python
if count == 1:
    message = tr("1 feature processed")
else:
    message = tr("{count} features processed").format(count=count)
```

## Testing Translations

### Validation Script
Use the validation script to check translation files:

```bash
python validate_i18n_files.py
```

### Manual Testing
1. Change QGIS locale in settings
2. Restart QGIS
3. Test plugin functionality
4. Verify all text appears in expected language

## Maintenance

### Updating Translations
When adding new translatable strings:

1. Add `tr()` calls in code
2. Update .ts files (manually or with pylupdate if available)
3. Translate new strings
4. Compile to .qm files
5. Test in target language

### Translation Status
Current translation completion:
- English: 100% (source language)
- Portuguese: 100% (89/89 strings)

## Technical Details

### Qt Integration
The system integrates with Qt's translation framework:

```python
# Install translator
translator = QTranslator()
translator.load(translation_file)
QCoreApplication.installTranslator(translator)

# Use translation
text = QCoreApplication.translate('RedBasicaExport', 'Source text')
```

### QGIS Locale Detection
Automatically detects user's QGIS locale:

```python
locale = QSettings().value('locale/userLocale', 'en')[0:2]
```

### Fallback Mechanism
If translation is missing:
1. Try user's locale (e.g., 'pt')
2. Fall back to English ('en')
3. Return original string if all else fails

## Troubleshooting

### Common Issues

1. **Missing Translations**: Check .qm files are compiled and up to date
2. **Wrong Language**: Verify QGIS locale settings
3. **Encoding Issues**: Ensure .ts files use UTF-8 encoding
4. **Context Errors**: Check translation context matches code

### Debug Information
Enable debug logging to see translation loading:

```python
QgsMessageLog.logMessage(
    f"Translation loaded: {translation_file}",
    "RedBasica Export", Qgis.Info
)
```

## Future Enhancements

Potential improvements:
- Additional language support (Spanish, French, etc.)
- Dynamic language switching without restart
- Translation management tools
- Crowdsourced translation platform integration
- Right-to-left language support

## Resources

- [Qt Internationalization](https://doc.qt.io/qt-5/internationalization.html)
- [QGIS Plugin Internationalization](https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#internationalization)
- [Python gettext module](https://docs.python.org/3/library/gettext.html)