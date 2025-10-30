# CLO Companion - User Guide

**Version:** 4.2.0-Julian-CLOLive  
**Last Updated:** 2025-10-29

---

## 🎯 **OVERVIEW**

CLO Companion is a procedural garment generator integrated into the Julian Assistant Suite. It converts natural language prompts into 3D garment files (.obj + .mtl) that can be imported into CLO3D for further refinement.

---

## 🚀 **QUICK START**

### 1. **Launch the Application**
- Double-click `RAG_Control_Panel.py` (or use desktop shortcut)
- Wait for GUI to load

### 2. **Open CLO Companion Tab**
- Click the **"👗 CLO Companion"** tab at the top of the window

### 3. **Generate Your First Garment**
- Enter a prompt like: `"white cotton t-shirt with rolled sleeves"`
- Click **"Generate Garment"**
- Wait 5-10 seconds
- See ✅ confirmation: "Garment generated: garment_YYYYMMDD_HHMMSS_*.obj"

### 4. **Open Output Folder**
- Click **"📁 Open Output Folder"** to view generated files

---

## 📝 **GARMENT PROMPTS**

### **Prompt Format**
CLO Companion understands natural language descriptions. Include:
- **Garment type:** shirt, t-shirt, pants, coat, jacket, trench, dress, skirt
- **Material:** cotton, denim, leather, silk, wool, beige, white, black
- **Attributes:** oversized, fitted, long, short, sleeveless, rolled sleeves, belt, hood

### **Example Prompts**

#### **Basic Garments**
```
white cotton t-shirt with rolled sleeves
black denim pants
blue wool sweater
```

#### **With Attributes**
```
oversized beige trench coat with belt
fitted black leather jacket
long white cotton dress
short denim skirt
```

#### **Specific Styles**
```
sleeveless white tank top
oversized beige trench coat
fitted black leather jacket with hood
long white cotton dress with belt
```

### **How Prompts Are Parsed**

1. **Garment Type Detection:**
   - Searches for keywords: shirt, t-shirt, pants, coat, jacket, trench, dress, skirt
   - Defaults to "shirt" if none found

2. **Material Detection:**
   - Searches for: cotton, denim, leather, silk, wool, beige, white, black
   - Defaults to "cotton" if none found

3. **Attribute Detection:**
   - `oversized` → wider proportions
   - `fitted` / `tight` → tighter fit
   - `long` → extended length
   - `short` → reduced length
   - `sleeveless` / `tank` → removes sleeves
   - `rolled` / `cuffed` → rolled sleeves
   - `belt` → adds belt detail
   - `hood` → adds hood

---

## 📁 **OUTPUT FILES**

### **File Types**

Generated files are saved in:
```
C:\Users\Julian Poopat\Documents\Management Class\RAG_System\modules\clo_companion\outputs\
```

For each garment, you get:

1. **`.obj` file** - 3D mesh model (text-based, human-readable)
   - Example: `garment_20251029_143022_shirt_5678.obj`

2. **`.mtl` file** - Material definition (color, roughness)
   - Example: `garment_20251029_143022_shirt_5678.mtl`

3. **`_metadata.json`** - Generation details
   - Contains: prompt, parsed attributes, seed, timestamp, vertex/face counts
   - Example: `garment_20251029_143022_shirt_5678_metadata.json`

4. **`_preview.png`** (optional) - Visual preview thumbnail
   - Saved in `outputs/previews/`
   - Example: `garment_20251029_143022_shirt_5678_preview.png`

---

## 🎨 **IMPORTING TO CLO3D**

### **Method 1: Direct Import**
1. In CLO3D, go to **File → Import → OBJ**
2. Navigate to: `modules/clo_companion/outputs/`
3. Select your `.obj` file
4. The `.mtl` file will be automatically loaded if in the same folder

### **Method 2: Copy to CLO Project**
1. Copy `.obj` and `.mtl` files to your CLO3D project's `imports/` folder
2. Open CLO3D project
3. Import from project folder

### **CLO3D Not Installed?**
- You can still view `.obj` files in:
  - Blender (free)
  - MeshLab (free)
  - Online OBJ viewers

---

## 🔌 **API USAGE**

### **Direct API Calls**

The CLO Companion API runs on **port 5001** and can be called directly:

#### **Generate Garment**
```bash
curl -X POST http://127.0.0.1:5001/generate_garment \
  -H "Content-Type: application/json" \
  -d '{"prompt": "white cotton t-shirt with rolled sleeves"}'
```

#### **List Outputs**
```bash
curl http://127.0.0.1:5001/list_outputs
```

#### **Get Preview**
```bash
curl http://127.0.0.1:5001/preview/garment_20251029_143022_shirt_5678
```

#### **Health Check**
```bash
curl http://127.0.0.1:5001/health
```

---

## 🎛️ **GUI FEATURES**

### **CLO Companion Tab**

1. **Prompt Entry:**
   - Type your garment description
   - Click example prompts to auto-fill

2. **Generate Button:**
   - Starts generation process
   - Shows progress bar during generation
   - Displays status: "Generating..." → "✅ Garment generated: [filename]"

3. **Outputs List:**
   - Shows all generated garments
   - Displays: timestamp, prompt preview, filename
   - Double-click to open output folder
   - Click "Refresh List" to reload

4. **Open Output Folder:**
   - Opens Windows Explorer to `outputs/` directory
   - Quick access to generated files

---

## 🔧 **TROUBLESHOOTING**

### **"CLO Companion API not running"**
- **Solution:** The API starts automatically when you click "Generate Garment"
- If it fails: Click "Generate Garment" again (it will retry starting the API)
- Check `Logs/clo_api_errors.log` for startup errors

### **Preview Not Generated**
- **Cause:** Requires `trimesh` or `open3d` installed
- **Solution:** Run `pip install trimesh` or `pip install open3d`
- Preview is optional; `.obj` file is always generated

### **"Generation failed" Error**
- Check console logs for details
- Ensure API is running: `http://127.0.0.1:5001/health`
- Verify prompt contains garment type keywords

### **Port 5001 Already in Use**
- Another application is using port 5001
- Close the conflicting app or change port in `config/clo_companion_config.json`

### **GPU Not Available**
- CLO Companion works on CPU (GPU is optional for future enhancements)
- Current version uses lightweight procedural generation (CPU-only)

---

## ⚙️ **CONFIGURATION**

### **Module Config File**
`config/clo_companion_config.json`

```json
{
  "api": {
    "port": 5001,
    "host": "127.0.0.1"
  },
  "output_dir": "modules/clo_companion/outputs",
  "preview_enabled": true,
  "clo3d_project_path": ""
}
```

### **CLO3D Project Path**
Set `clo3d_project_path` to enable auto-export:
- If set, generated garments are copied to `{path}/imports/`
- Leave empty to disable auto-export

---

## 📊 **OUTPUT FORMATS**

### **OBJ File Structure**
```
# Garment generated by Julian Assistant Suite
mtllib garment_xxx.mtl

v 0.000000 0.000000 0.000000
v 0.500000 0.000000 0.000000
...

vn 0.000000 0.000000 1.000000
...

usemtl garment_xxx
f 1//1 2//2 3//3
...
```

### **MTL File Structure**
```
newmtl garment_xxx
Kd 0.900 0.900 0.900
Ns 300
d 1.0
illum 2
```

---

## 🎓 **BEST PRACTICES**

### **Writing Good Prompts**
1. **Be specific:** "white cotton t-shirt" vs. "shirt"
2. **Include material:** Helps assign correct colors/textures
3. **Use attributes:** "oversized", "fitted", "long" for better variation
4. **Avoid ambiguity:** "coat" or "jacket" (not "outerwear")

### **Organizing Outputs**
- Use descriptive filenames (CLO Companion adds timestamps automatically)
- Review `_metadata.json` to see how your prompt was parsed
- Keep `.obj` and `.mtl` files together (required for CLO3D import)

### **Workflow Tips**
1. Generate multiple variations (different seeds)
2. Review previews before importing to CLO3D
3. Use CLO3D to refine proportions after import
4. Export as `.clo` from CLO3D for project files

---

## 🔗 **INTEGRATION**

### **Event Bus Integration**
- CLO Companion publishes `clo.garment_generated` events
- Other modules can subscribe to these events

### **Cloud Bridge Support**
- Garment generation can be offloaded to VPS via `/execute` endpoint
- Task: `"clo_render"` (when implemented on VPS)

### **Memory Integration**
- Generated garments are logged in memory manager
- Category: `clo_projects`
- Can be recalled in context graph

---

## 📚 **ADVANCED USAGE**

### **Seed-Based Generation**
- Use the same seed to regenerate identical mesh
- Seeds are auto-generated (random 1000-9999)
- Custom seed via API: `{"prompt": "...", "seed": 1234}`

### **Custom Material Library**
- Edit `garment_gen.py` → `self.materials` dictionary
- Add new materials with RGB values and roughness

### **Extended Templates**
- Add new garment types in `garment_gen.py`
- Create template function: `_generate_mypattern_template()`
- Register in `self.templates` dictionary

---

## ✅ **SUCCESS CRITERIA VERIFICATION**

After following this guide, you should be able to:

- ✅ Launch Control Panel → See CLO Companion tab
- ✅ Enter prompt → Click "Generate" → See ✅ confirmation
- ✅ Find `.obj` file in `outputs/` folder
- ✅ API responds at `http://127.0.0.1:5001/generate_garment`
- ✅ Logs show `[CLO] Garment generated successfully`
- ✅ Double-click output list → Opens folder

---

## 🆘 **SUPPORT**

**Documentation:**
- `JULIAN_SUITE_FILE_STRUCTURE.md` - File locations
- `CHANGELOG.md` - Version history
- `CLO_COMPANION_SPEC.md` - Technical specification

**Logs:**
- `Logs/YYYY-MM-DD.log` - General logs
- `Logs/clo_api_errors.log` - API startup errors

**Health Check:**
- Click "Health Check" in Control Panel
- Verifies CLO Companion API is running

---

**Happy Designing! 👗**

*CLO Companion v4.2.0-Julian-CLOLive*




