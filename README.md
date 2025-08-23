# RedBasica Export - Flexible Sewerage DXF Export Plugin

Professional-grade DXF export plugin for sewerage network designs in QGIS with complete flexibility in layer selection and field mapping.

## 🎯 Key Features

### Universal Compatibility
- Works with **ANY** layer names (not restricted to 'PIPES'/'JUNCTIONS')
- Supports **ANY** field naming conventions
- Compatible with existing QEsg projects and custom data structures

### Intelligent Field Mapping
- Auto-suggests field mappings based on common patterns
- Supports QEsg field names as suggestions (not requirements)
- Allows completely manual mapping when needed
- Handles multilingual field names (Portuguese, English, etc.)

### Robust Data Processing
- Converts string numbers ("1.05", "2,50") to proper numeric values
- Handles NULL/empty values gracefully with appropriate defaults
- Supports Portuguese decimal notation (comma to dot conversion)
- Automatic type conversion with fallback to safe defaults

### Professional DXF Output
- Organized layer structure compatible with AutoCAD
- 3D geometry support with elevation data
- Flow arrows and comprehensive labeling
- QEsg-compatible styling and blocks
- Extended entity data (XDATA) for software compatibility

## 🚀 Quick Start

1. **Install Plugin**: Available in QGIS Plugin Repository
2. **Load Your Data**: Any sewerage network layers with any field names
3. **Launch Plugin**: Click RedBasica Export icon in toolbar
4. **Select Layers**: Choose your pipe and junction layers
5. **Map Fields**: Auto-mapping suggests field assignments
6. **Export**: Generate professional DXF output

## 📋 Requirements

- QGIS 3.16 or later
- Python 3.7 or later (included with QGIS)
- No external dependencies (all libraries bundled)

## 📦 Installation

### From QGIS Plugin Repository (Recommended)
1. Open QGIS → **Plugins** → **Manage and Install Plugins**
2. Search for "RedBasica Export"
3. Click **Install Plugin**

### Manual Installation
1. Download plugin ZIP file
2. **Plugins** → **Install from ZIP**
3. Select downloaded file and install

See [INSTALLATION.md](INSTALLATION.md) for detailed installation instructions.

## 📖 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete feature documentation
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Technical architecture and API
- **[API Reference](docs/API_REFERENCE.md)** - Comprehensive API documentation
- **[Installation Guide](INSTALLATION.md)** - Detailed installation instructions
- **[Examples](examples/)** - Sample datasets and tutorials

## 🎓 Tutorials

- **[Basic Export](examples/tutorials/basic_export.md)** - Your first export
- **Field Mapping** - Advanced mapping techniques
- **Custom Templates** - Creating custom DXF templates
- **Data Conversion** - Handling different data formats

## 🔧 Technical Highlights

### Architecture
- Modular design with clear separation of concerns
- Comprehensive error handling and validation
- Extensible field mapping system
- Template-based DXF generation

### Data Handling
- Robust type conversion system
- Graceful NULL/empty value handling
- Portuguese decimal notation support
- Calculated field generation (slope, depth)

### Export Quality
- QEsg-compatible layer organization
- Professional CAD styling
- 3D coordinate support
- Extended entity data for software compatibility

## 🌍 Internationalization

- Portuguese (primary language)
- English (full support)
- Extensible translation system
- Localized field display names

## 🧪 Testing

Comprehensive test coverage including:
- Unit tests for all core components
- Integration tests for complete workflows
- Data conversion validation
- UI functionality testing

Run tests:
```bash
python -m pytest tests/
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on QEsg plugin architecture
- Uses ezdxf library for DXF processing
- Inspired by the sewerage engineering community's needs

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/leonazareth/redbasica_export/issues)
- **Discussions**: [GitHub Discussions](https://github.com/leonazareth/redbasica_export/discussions)
- **Email**: leonazareth@gmail.com

## 🔄 Version History

### v1.0.0 - Initial Professional Release
- Universal layer selection and field mapping
- Robust data type conversion system
- Professional DXF output with comprehensive styling
- Self-contained operation with bundled libraries
- Comprehensive documentation and examples

---

**RedBasica Export** - Bringing flexibility and professionalism to sewerage network DXF export in QGIS.