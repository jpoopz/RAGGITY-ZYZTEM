# Complete Connection Setup Guide - CLO 3D + Hostinger VPS

**Date:** October 30, 2025  
**Purpose:** Set up passwordless connections for CLO 3D Bridge and Hostinger VPS Cloud Bridge

---

## 🎯 Quick Setup (2 Commands)

```powershell
# 1. Setup SSH keys for VPS (passwordless authentication)
.\remote\setup_ssh_keys.ps1

# 2. Deploy cloud bridge to VPS
.\remote\deploy_to_vps.ps1
```

**Then in CLO 3D:**
- Script → Run Script… → `modules\clo_companion\clo_bridge_listener.py`

---

## 📋 Part 1: CLO 3D Bridge Connection

### What It Does:
- Allows your RAG system to control CLO 3D remotely
- Create garments, run simulations, take screenshots
- Two-way communication via TCP socket (port 51235)

### Setup Steps:

#### **Step 1: Locate the Listener Script**
```
Path: C:\Users\Julian Poopat\Desktop\RAG_System\modules\clo_companion\clo_bridge_listener.py
```

#### **Step 2: Run in CLO 3D**
1. Open **CLO 3D** application
2. Go to: **File → Script → Run Script…**
3. Browse to and select: `modules\clo_companion\clo_bridge_listener.py`
4. Click **Run**

You should see in CLO's console:
```
CLO Bridge listening on 127.0.0.1:51235
Ready to receive commands...
```

#### **Step 3: Test from Control Panel**
1. Open RAG Control Panel
2. Go to **CLO 3D** tab
3. Click **🔌 Connect** (should connect automatically to 127.0.0.1:51235)
4. Status should show: **🟢 Connected to 127.0.0.1:51235**

### Verification:
```powershell
# Test TCP connection
Test-NetConnection 127.0.0.1 -Port 51235

# Should show: TcpTestSucceeded: True
```

### Troubleshooting:

**Issue:** "Listener not found"
- **Solution:** Verify CLO 3D is running and listener script is active
- Check CLO's Python console for errors

**Issue:** Firewall prompt
- **Solution:** Click "Allow" for localhost connections

**Issue:** Port already in use
- **Solution:** Close other CLO listener instances or change port:
  ```powershell
  $env:CLO_PORT = "51236"
  ```

---

## 📋 Part 2: Hostinger VPS Cloud Bridge

### What It Does:
- Secure SSH connection to your Hostinger VPS
- Automatic, passwordless authentication
- Cloud backups, remote execution, context sync

### Prerequisites:
- Hostinger VPS with Ubuntu
- SSH access (you should have IP, username, password)
- Port 8000 open for cloud bridge API

### Setup Steps:

#### **Step 1: Run SSH Key Setup**

```powershell
cd "C:\Users\Julian Poopat\Desktop\RAG_System"
.\remote\setup_ssh_keys.ps1
```

**What it does:**
- Generates 4096-bit RSA key pair (if not exists)
- Saves to: `~\.ssh\hostinger_vps_rsa`
- Copies public key to VPS (requires password **once**)
- Creates SSH config alias: `hostinger-vps`
- Updates local VPS config

**Prompts you'll see:**
```
Enter your Hostinger VPS IP or domain: [your-vps-ip]
Try automated setup now? (y/N): y
[Enter VPS password once]
Test SSH connection now? (Y/n): y
Update config/vps_config.json with VPS details? (Y/n): y
```

#### **Step 2: Deploy Cloud Bridge to VPS**

```powershell
.\remote\deploy_to_vps.ps1
```

**What it does:**
- Uploads cloud_bridge_server.py to VPS via SSH
- Installs FastAPI, uvicorn on VPS
- Generates secure auth token
- Creates systemd service
- Starts the server

**No password needed** - uses SSH keys from Step 1!

#### **Step 3: Test Connection**

```powershell
# Test from Python
python -c "from core.cloud_bridge import bridge; print(bridge.health())"

# Should return:
# {'status': 'ok', 'service': 'Cloud Bridge', ...}
```

### After Setup:

**Connect with one command:**
```powershell
ssh hostinger-vps
# No password prompt! ✅
```

**Manage VPS service:**
```bash
# On VPS
sudo systemctl status julian-cloud-bridge
sudo systemctl restart julian-cloud-bridge
tail -f ~/assistant/bridge.log
```

---

## 🔐 Security Features

### SSH Key Authentication:
- ✅ 4096-bit RSA encryption
- ✅ Passwordless (private key stays local)
- ✅ Automatic reconnection
- ✅ Timeout protection (10s max)

### VPS API Authentication:
- ✅ Bearer token (64-char hex)
- ✅ Token stored securely on VPS
- ✅ All requests require Authorization header

### Cloud Bridge:
- ✅ Optional RSA+AES encryption for payloads
- ✅ Signature verification
- ✅ TLS/HTTPS support

---

## 🧪 Testing Checklist

### CLO 3D Connection:
```
□ CLO 3D application is running
□ Listener script loaded in CLO
□ Console shows "listening on 127.0.0.1:51235"
□ Control Panel shows "🟢 Connected"
□ Can send test command (e.g., import garment)
```

### VPS Cloud Bridge:
```
□ SSH key generated (~/.ssh/hostinger_vps_rsa)
□ Public key copied to VPS
□ Can SSH without password: ssh hostinger-vps
□ Cloud bridge server running on VPS
□ Health endpoint responds: curl http://vps-ip:8000/ping
□ Local client can connect: bridge.health()
□ Config file updated (config/vps_config.json)
```

---

## 📊 Configuration Summary

### CLO Config (`modules/clo_companion/config.py`):
```python
CLO_HOST = "127.0.0.1"
CLO_PORT = 51235
CLO_TIMEOUT = 10
```

### VPS Config (`config/vps_config.json`):
```json
{
  "enabled": true,
  "vps_url": "http://your-vps-ip:8000",
  "api_token": "your-64-char-token",
  "ssh_host": "hostinger-vps",
  "auto_sync": true,
  "auto_reconnect": true
}
```

### SSH Config (`~/.ssh/config`):
```
Host hostinger-vps
    HostName your-vps-ip
    User root
    Port 22
    IdentityFile ~/.ssh/hostinger_vps_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

---

## 🚀 Quick Commands Reference

### CLO 3D:
```powershell
# Test connection
Test-NetConnection 127.0.0.1 -Port 51235

# Check listener process
Get-Process python | Where-Object {$_.MainWindowTitle -like "*CLO*"}
```

### VPS Cloud Bridge:
```powershell
# Connect to VPS (no password!)
ssh hostinger-vps

# View logs
ssh hostinger-vps "tail -f ~/assistant/bridge.log"

# Restart service
ssh hostinger-vps "sudo systemctl restart julian-cloud-bridge"

# Check health
ssh hostinger-vps "curl http://localhost:8000/ping"
```

### From RAG System:
```python
# Test CLO bridge
python -c "from modules.academic_rag.health_endpoint import get_clo_health; import json; print(json.dumps(get_clo_health(), indent=2))"

# Test VPS bridge
python -c "from core.cloud_bridge import bridge; import json; print(json.dumps(bridge.health(), indent=2))"

# Get full system health
python -c "from modules.academic_rag.health_endpoint import get_full_health; import json; print(json.dumps(get_full_health(), indent=2))"
```

---

## 🎁 What You Get

### CLO 3D Integration:
- ✅ Automatic garment generation from text prompts
- ✅ Remote simulation control
- ✅ Screenshot capture
- ✅ Real-time status in UI
- ✅ "Why?" button shows connection errors
- ✅ Periodic health checks (every 5s)

### VPS Cloud Bridge:
- ✅ Passwordless SSH access (no typing passwords!)
- ✅ Automatic cloud backups every 15 minutes
- ✅ Remote LLM execution (offload to VPS GPU)
- ✅ Context synchronization
- ✅ Auto-reconnect on network hiccup

---

## 🔧 Maintenance

### Update CLO Listener:
```powershell
# If you update the listener code, just re-run in CLO:
# Script → Run Script → modules\clo_companion\clo_bridge_listener.py
```

### Update VPS Server:
```powershell
# Re-deploy latest code
.\remote\deploy_to_vps.ps1

# Or manually:
scp remote/cloud_bridge_server.py hostinger-vps:~/assistant/
ssh hostinger-vps "sudo systemctl restart julian-cloud-bridge"
```

---

## 📞 Support

**CLO Issues:**
- Check: CLO 3D console output
- Logs: See CLO's script console
- Help: Click "❓ How to connect" in CLO tab

**VPS Issues:**
- Check: `ssh hostinger-vps "tail ~/assistant/bridge.log"`
- Logs: Systemd journal: `ssh hostinger-vps "journalctl -u julian-cloud-bridge -n 50"`
- Help: See VPS_BRIDGE_SETUP.md

---

## ✅ Success Indicators

**CLO Connected:**
```
✓ Warning banner hidden
✓ Connection status: 🟢 Connected to 127.0.0.1:51235
✓ Action buttons enabled (Import, Export, Simulate, Screenshot)
✓ /health/clo returns: {"ok": true, "handshake": "ok"}
```

**VPS Connected:**
```
✓ bridge.health() returns status: ok
✓ Auto-sync running (check logs for "[Bridge] Sync complete")
✓ SSH works without password: ssh hostinger-vps
✓ /health/full shows all green indicators
```

---

**Ready to start?** Run these two commands and you'll be fully connected! 🚀


