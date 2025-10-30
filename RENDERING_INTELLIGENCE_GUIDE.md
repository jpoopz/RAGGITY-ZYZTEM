# Rendering Intelligence Layer Guide

**Version:** v7.0.0-Julian-SelfHealing

## Overview

The Rendering Intelligence Layer provides dual-mode rendering for CLO Companion garments with automatic GPU awareness and adaptive performance optimization.

## Rendering Modes

### 🟢 Fast Preview Mode
- **Resolution:** 512x512 pixels
- **Quality:** Medium
- **Speed:** Instant (< 1 second)
- **Use Case:** Quick preview during design iteration
- **GPU Usage:** Minimal

### 🔵 Realistic Render Mode
- **Resolution:** 2048x2048 pixels
- **Quality:** High (shadows, lighting enabled)
- **Speed:** 5-30 seconds (depends on GPU)
- **Use Case:** Final presentation renders
- **GPU Usage:** High

## GPU Auto-Fallback

The system automatically monitors GPU utilization and switches to Fast Preview mode when:
- GPU utilization > 85%
- GPU temperature > 80°C
- nvidia-smi unavailable (CPU mode)

**Benefits:**
- Prevents GPU overload
- Maintains system responsiveness
- Ensures render queue doesn't block

## Usage

### 1. Selecting Render Mode

In the **👗 CLO Companion** tab:

1. **Fast Preview** button (🟢) - Default, always available
2. **Realistic Render** button (🔵) - High-quality output

The active mode is highlighted (depressed button).

### 2. GPU Status Monitor

The GPU status indicator shows:
- **Green:** GPU < 70% utilization (optimal)
- **Orange:** GPU 70-85% (throttled)
- **Red:** GPU > 85% (auto-fallback active)
- **Gray:** CPU mode (nvidia-smi not available)

Updates automatically every 5 seconds.

### 3. Viewing Renders

1. Click **"📷 View Full Render"** button
2. Opens `modules/clo_companion/outputs/renders/` folder
3. Realistic renders are saved here with metadata

### 4. Render During Generation

- New garments automatically render in Fast Preview mode
- Can switch to Realistic Render after generation
- Preview updates automatically after each iteration

## Avatar Management

The system supports parametric avatar scaling:

- **Male** - Default: 175cm height
- **Female** - Default: 165cm height  
- **Unisex** - Default: 170cm height

Avatar parameters are configurable in `render_config.json`:
```json
{
  "avatar": {
    "type": "unisex",
    "scale": 1.0
  }
}
```

## Configuration

Edit `modules/clo_companion/render_config.json`:

```json
{
  "default_mode": "fast_preview",
  "gpu_limits": {
    "max_utilization": 85,
    "max_temperature": 80,
    "auto_fallback": true
  },
  "preview": {
    "resolution": 512,
    "quality": "medium"
  },
  "realistic": {
    "resolution": 2048,
    "quality": "high",
    "enable_shadows": true,
    "enable_lighting": true
  }
}
```

## Performance Tips

1. **Use Fast Preview for Iteration** - Faster feedback loop
2. **Use Realistic Render for Final** - Better presentation quality
3. **Monitor GPU Status** - Avoid overloading system
4. **Queue Management** - System throttles automatically

## Technical Details

### Render Pipeline

1. **Garment Generation** → OBJ file created
2. **Render Manager** → Routes to appropriate renderer
3. **GPU Monitor** → Checks utilization
4. **Auto-Fallback** → Switches mode if needed
5. **Preview/Render** → Output generated
6. **Metadata** → Saved alongside render

### GPU Detection

- Uses `nvidia-smi` if available
- Falls back to CPU mode if not available
- Monitors: utilization, memory, temperature

### Render Output

**Fast Preview:**
- `outputs/previews/{base_name}_preview.png`
- Lightweight, quick access

**Realistic Render:**
- `outputs/renders/{base_name}_render.png`
- High-quality, large file size

## Troubleshooting

**GPU Not Detected:**
- Verify nvidia-smi is installed
- Check GPU drivers are up to date
- System will use CPU mode automatically

**Render Fails:**
- Check trimesh or open3d installation
- Verify OBJ file is valid
- Review `Logs/clo_render.log`

**Slow Rendering:**
- Reduce render resolution in config
- Close other GPU-intensive applications
- System will auto-throttle if overloaded

---

*Julian Assistant Suite v7.0.0-Julian-SelfHealing*




