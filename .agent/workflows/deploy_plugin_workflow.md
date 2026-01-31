---
description: How to compile and deploy the RedBasica Export plugin
---

# QGIS Plugin Deployment Workflow

Follow these steps to deploy changes to the QGIS plugin.

## 1. Determine if Compilation is Needed
- **UI Changes (.ui files)**: No compilation needed. 
- **Python Changes (.py files)**: No compilation needed.
- **Resource Changes (.qrc, icons)**: **COMPILATION REQUIRED**.

## 2. Compile Resources (If Needed)
If you modified `resources.qrc` or files in `resources/`, run:

```powershell
pyrcc5 -o resources.py resources.qrc
```
*Note: Ensure you are in the OSGeo4W shell or have `pyrcc5` in your PATH.*

## 3. Reload Plugin in QGIS
1. Open QGIS.
2. Use the **Plugin Reloader** plugin (install if missing).
3. Select "RedBasica Export" and click reload.
4. **Alternative**: Restart QGIS.

## 4. Verify
- Check if icons appear correctly.
- Run a test export to ensure no `ImportError` or UI crashes.
