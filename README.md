# RedBasica Export - Flexible Sewerage DXF Export Plugin

DXF Exporter plugin for sewerage network designs in QGIS with complete flexibility in layer selection and field mapping.

## Inspiration & Attribution

This plugin draws inspiration from the excellent **QEsg export to DXF functionality** developed by Jorge Almerio.

**Original QEsg Project**: https://github.com/jorgealmerio/QEsg

💝 **Support Open Source Development**  
If you find RedBasica Export or QEsg useful for your work, please consider supporting the original QEsg author through donations. Your contribution helps maintain and improve these valuable tools for the QGIS community.

## Key Features

### Universal Compatibility
- Works with **ANY** layer names (not restricted to 'PIPES'/'JUNCTIONS')
- Supports **ANY** field naming conventions

### Intelligent Field Mapping
- Auto-suggests field mappings based on common patterns
- Allows completely manual mapping when needed

## Quick Start

1. **Install Plugin**: Available in QGIS Plugin Repository
2. **Load Your Data**: Any sewerage network layers with any field names
3. **Launch Plugin**: Click RedBasica Export icon in toolbar
4. **Select Layers**: Choose your pipe and junction layers
5. **Map Fields**: Auto-mapping suggests field assignments
6. **Export**: Generate professional DXF output

## Requirements

- QGIS 3.16 or later
- Python 3.7 or later (included with QGIS)
- No external dependencies (all libraries bundled)

## Installation

### From QGIS Plugin Repository (Recommended)
1. Open QGIS → **Plugins** → **Manage and Install Plugins**
2. Search for "RedBasica Export"
3. Click **Install Plugin**

### Manual Installation
1. Download plugin ZIP file
2. **Plugins** → **Install from ZIP**
3. Select downloaded file and install

See [INSTALLATION.md](INSTALLATION.md) for detailed installation instructions.


## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on QEsg plugin architecture
- Uses ezdxf library for DXF processing

## 📞 Support

- **Email**: leonazareth@gmail.com

## Version History

### v0.5.0 - Beta Release
- Universal layer selection and field mapping
- Robust data type conversion system
- Professional DXF output with comprehensive styling
- Self-contained operation with bundled libraries
- Comprehensive documentation and examples

---

