# 🎨 Garment Workshop - User Guide

## Overview

The **Garment Workshop** is a new module in RAGGITY ZYZTEM 2.0 that allows you to design, preview, and export garments **without requiring a live CLO 3D connection**. This replaces the fragile socket-based listener with a safe, file-based workflow.

## Features

✅ **No CLO Required** - Design garments entirely within RAGGITY ZYZTEM  
✅ **5 Base Templates** - T-shirt, Pants, Jacket, Dress, Shirt  
✅ **7 Fabric Presets** - Cotton, Linen, Silk, Denim, Leather, Wool, Polyester  
✅ **Live Previews** - See your design before exporting  
✅ **One-Click Export** - Open finished garments directly in CLO 3D  
✅ **Project Management** - Track iterations and versions  

---

## Quick Start

### 1. Open the Workshop

Launch RAGGITY ZYZTEM and click:
- **Dashboard** → **"Open Workshop"** button, OR
- **Sidebar** → **🎨 Workshop** tab

### 2. Create Your First Garment

**Fill in the form:**
- **Garment Name**: e.g., "Summer T-Shirt"
- **Garment Type**: Choose from tshirt, pants, jacket, dress, shirt
- **Fabric**: Select a fabric preset (cotton, denim, etc.)
- **Color** (optional): Enter a hex code like `#FF5733` or leave blank
- **Notes** (optional): Add design notes

**Click "🎨 Generate Garment"**

### 3. Preview Your Design

After generation:
- Click **"👁️ Preview"** to render a visual preview
- The preview appears in the right panel
- Previews are cached in `exports/previews/`

### 4. Export to CLO

When ready:
- Click **"📤 Export to CLO"**
- CLO 3D will launch with your garment file
- Edit patterns, run simulations, and refine in CLO

---

## File Structure

```
RAGGITY-ZYZTEM/
├── templates/garments/          # Base templates
│   ├── tshirt_base.zprj
│   ├── pants_base.zprj
│   ├── jacket_base.zprj
│   ├── dress_base.zprj
│   └── shirt_base.zprj
├── exports/garments/            # Generated garments
│   ├── Summer_Tshirt_20251031_220000.zprj
│   ├── Summer_Tshirt_20251031_220000.json  # Metadata
│   └── index.json               # Garment library index
├── exports/previews/            # Preview images
│   └── Summer_Tshirt.png
└── config/settings.json         # Workshop settings
```

---

## Settings

Edit `config/settings.json` to customize:

```json
{
  "clo_executable": "C:\\Program Files\\CLO\\CLO.exe",
  "export_dir": "exports/garments",
  "template_dir": "templates/garments",
  "auto_open_clo": false,
  "default_fabric": "cotton",
  "default_style": "tshirt"
}
```

**Key Settings:**
- `clo_executable`: Path to your CLO 3D installation
- `auto_open_clo`: Auto-launch CLO after generation (default: false)
- `default_fabric`: Default fabric selection
- `default_style`: Default garment type

---

## API Endpoints

The Workshop also exposes REST API endpoints:

### Generate Garment
```http
POST /generate_garment
Content-Type: application/json

{
  "name": "Summer Dress",
  "fabric": "silk",
  "style": "dress",
  "color": "#FFB6C1",
  "notes": "Flowy summer design"
}
```

### List Garments
```http
GET /list_garments

Response:
{
  "garments": [...],
  "count": 5
}
```

### Get Presets
```http
GET /garment_presets

Response:
{
  "fabrics": {...},
  "styles": {...}
}
```

### Open in CLO
```http
POST /open_in_clo
Content-Type: application/json

{
  "file_path": "exports/garments/Summer_Dress_20251031.zprj"
}
```

---

## Workflow Example

### Scenario: Design a Casual T-Shirt

1. **Open Workshop** → Click "🎨 Workshop" in sidebar
2. **Fill Form:**
   - Name: "Casual Logo Tee"
   - Type: tshirt
   - Fabric: cotton
   - Color: #4A90E2 (blue)
   - Notes: "Add logo on front"
3. **Generate** → Click "🎨 Generate Garment"
4. **Preview** → Automatic preview renders
5. **Export** → Click "📤 Export to CLO"
6. **Edit in CLO** → Add logo, adjust fit, run simulation
7. **Iterate** → Generate new versions with different colors/fabrics

---

## Troubleshooting

### "CLO executable not found"
**Solution:** Update `config/settings.json` with correct CLO path:
```json
{
  "clo_executable": "C:\\Program Files\\CLO\\CLO.exe"
}
```

### Preview not showing
**Solution:** 
- Check `exports/previews/` directory exists
- Ensure Pillow is installed: `pip install Pillow`
- Try clicking "🔄 Refresh" in the library

### Garment won't open in CLO
**Solution:**
- Verify CLO 3D is installed
- Check file exists in `exports/garments/`
- Try opening the .zprj file manually in CLO

### "Module not found" errors
**Solution:** Install required dependencies:
```bash
pip install Pillow
```

---

## Advanced Features

### Project Management

Create projects to track multiple iterations:

```python
from modules.project_manager import create_project, add_iteration

# Create project
project = create_project(
    name="Summer Collection 2025",
    description="Casual summer wear designs"
)

# Add iterations
add_iteration(
    project_id=project["project_id"],
    garment_path="exports/garments/tshirt_v1.zprj",
    notes="Initial design"
)
```

### Custom Templates

Add your own templates to `templates/garments/`:

1. Create a base garment in CLO
2. Export as `.zprj`
3. Place in `templates/garments/`
4. Update `STYLE_TEMPLATES` in `modules/garment_generator.py`

### Batch Generation

Generate multiple garments programmatically:

```python
from modules.garment_generator import generate_garment

fabrics = ["cotton", "linen", "silk"]
for fabric in fabrics:
    generate_garment(
        name=f"Summer Tee - {fabric.title()}",
        fabric=fabric,
        style="tshirt"
    )
```

---

## Migration from Old CLO Listener

If you were using the old socket-based CLO listener:

**Old Workflow:**
1. Start CLO
2. Run listener script in CLO
3. Connect from RAGGITY UI
4. Send commands over socket
5. ❌ **Frequent crashes**

**New Workflow:**
1. Open Workshop in RAGGITY
2. Design garment
3. Generate preview
4. Export to CLO when ready
5. ✅ **No crashes, stable workflow**

---

## Future Enhancements

- [ ] Real-time 3D preview (pythreejs integration)
- [ ] Pattern editing within RAGGITY
- [ ] Fabric simulation parameters
- [ ] Batch export to multiple formats (OBJ, FBX, GLTF)
- [ ] Integration with CLO CLI (when available)
- [ ] AI-powered design suggestions
- [ ] Collaborative design features

---

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
- Open an issue on GitHub

---

## Credits

**RAGGITY ZYZTEM 2.0 - Garment Workshop**  
Built with ❤️ for fashion designers and CLO 3D users

---

**Happy Designing! 🎨👗**

