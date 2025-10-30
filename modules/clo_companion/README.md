# CLO 3D Companion Module

Integration module for connecting RAGGITY ZYZTEM with CLO 3D software.

## Overview

This module enables automated interaction with CLO 3D for garment design, pattern manipulation, and simulation tasks. It provides two integration modes to accommodate different workflow preferences and security requirements.

---

## Integration Modes

### Mode A: External Bridge (Recommended)

**Description:**  
A persistent listener service runs inside CLO's Python environment, accepting commands from the RAGGITY UI via TCP socket.

**How it works:**
1. User starts CLO 3D
2. User runs `clo_bridge_listener.py` inside CLO's built-in Python console
3. Listener opens a local socket on `127.0.0.1:51235` (configurable)
4. RAGGITY UI sends JSON commands to the bridge
5. Bridge executes commands in CLO's context and returns results

**Advantages:**
- Real-time bidirectional communication
- No file I/O overhead
- Immediate feedback and error handling
- Supports complex multi-step workflows

**Setup:**
1. Copy `clo_bridge_listener.py` to a known location
2. In CLO 3D: `File > Script > Run Script...` → Select `clo_bridge_listener.py`
3. Listener will print "CLO Bridge listening on 127.0.0.1:51235"
4. Use RAGGITY UI Bridge tab to send commands

---

### Mode B: Direct Script Execution

**Description:**  
RAGGITY generates standalone Python scripts that users manually run in CLO's script console.

**How it works:**
1. User describes desired operation in RAGGITY UI
2. RAGGITY generates a `.py` script file in `/exports/clo_scripts/`
3. User manually opens the script in CLO: `File > Script > Run Script...`
4. User reviews results and reports back to RAGGITY

**Advantages:**
- No persistent service required
- User can review and modify scripts before execution
- Works in air-gapped or restricted environments
- Simpler setup for one-off tasks

**Use cases:**
- Batch operations on garment files
- One-time pattern exports
- Educational/learning scenarios
- Environments where socket connections are restricted

---

## Configuration

See `modules/clo_companion/config.py` for connection settings:
- `CLO_HOST`: Host address (default: `127.0.0.1`)
- `CLO_PORT`: TCP port for bridge listener (default: `51235`)
- `CLO_TIMEOUT`: Command timeout in seconds (default: `10`)

Override via environment variables:
```bash
set CLO_PORT=52000
set CLO_TIMEOUT=30
```

---

## Command Examples

**Mode A (Bridge):**
```python
from modules.clo_companion.bridge_client import CLOBridgeClient

client = CLOBridgeClient()
result = client.send_command("get_garment_info")
print(result)
```

**Mode B (Script Generation):**
```python
from modules.clo_companion.script_generator import generate_script

script = generate_script("export_patterns", output_dir="C:/Exports")
# Script saved to /exports/clo_scripts/export_patterns_20231030-1530.py
# User manually runs in CLO
```

---

## Security Notes

- Mode A listener binds to `127.0.0.1` (localhost only) by default
- No external network exposure
- Commands are validated before execution
- File paths are sanitized to prevent directory traversal

---

## Troubleshooting

**Bridge won't connect:**
- Ensure CLO is running and listener script is active
- Check CLO's script console for error messages
- Verify firewall isn't blocking localhost connections
- Confirm port isn't in use by another application

**Scripts fail in CLO:**
- Check CLO's Python version compatibility
- Review script console output for tracebacks
- Ensure required CLO API modules are available
- Verify file paths are absolute and exist

---

## Future Enhancements

- Auto-detect CLO installation and version
- Visual pattern editor in RAGGITY UI
- Batch processing queue
- CLO project file parsing without CLO running
- Integration with RAG for garment design suggestions

---

*Last Updated: 2024*

