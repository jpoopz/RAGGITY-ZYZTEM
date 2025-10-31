# 🚀 Quick Start: Connect Everything in 5 Minutes

**Goal:** Get CLO 3D and Hostinger VPS fully connected and working

---

## ⚡ Super Quick Setup (Already Coded!)

### All the quality-of-life features are ALREADY IMPLEMENTED! ✅

You have:
- ✅ "Why?" explainer button
- ✅ Unified `/health/full` endpoint
- ✅ Telemetry breadcrumbs
- ✅ Smart TCP backoff
- ✅ IPv4/IPv6 fallbacks
- ✅ Periodic health checks
- ✅ "Retry" and "Hide" buttons
- ✅ Handshake verification
- ✅ 10 passing tests

**Everything is ready - you just need to configure the connections!**

---

## 🎯 Two Simple Steps

### Step 1: Start CLO Listener (30 seconds)

**Without CLO 3D (for testing only):**
```cmd
START_CLO_LISTENER.bat
```

**With CLO 3D (production):**
1. Open CLO 3D
2. File → Script → Run Script...
3. Browse: `modules\clo_companion\clo_bridge_listener.py`
4. Click "Run"
5. See: "CLO Bridge Listener started on 127.0.0.1:51235"

**Test it:**
```cmd
python TEST_CLO_CONNECTION.py
```

Expected output:
```
✓ TCP connection successful!
✓ Handshake successful!
✓ Command executed successfully!
✓ Available commands (6):
   - import_garment
   - export_garment
   - take_screenshot
   - run_simulation
   - get_garment_info
   - reset_garment

🎉 All tests passed! CLO Bridge is working perfectly!
```

---

### Step 2: Setup VPS SSH Keys (2 minutes)

```cmd
SETUP_CONNECTIONS.bat
```

This automated script will:
1. Generate SSH keys (passwordless authentication)
2. Copy key to your Hostinger VPS (password required **once**)
3. Deploy cloud bridge server to VPS
4. Test CLO connection
5. Test VPS connection
6. Show full system health

**Just answer the prompts!**

---

## ✅ How to Verify Everything Works

### Check CLO Bridge:
```cmd
Test-NetConnection 127.0.0.1 -Port 51235
# Should show: TcpTestSucceeded: True
```

### Check VPS Bridge:
```cmd
ssh hostinger-vps
# Should connect WITHOUT password prompt!
```

### Check Full System:
```cmd
python -c "from modules.academic_rag.health_endpoint import get_full_health; import json; print(json.dumps(get_full_health(), indent=2))"
```

Expected output:
```json
{
  "api": {"ok": true, "host": "127.0.0.1", "port": 5000},
  "clo": {"ok": true, "host": "127.0.0.1", "port": 51235, "handshake": "ok"},
  "vector_store": "faiss",
  "ollama": {"ok": true, "model_ok": true, "model": "llama3.2"},
  "sys": {"disk_free_gb": 200.5, "ram_free_gb": 10.3, "py": "3.14"}
}
```

---

## 🎮 Using the Connections

### In Control Panel GUI:

#### CLO 3D Tab:
1. Should show no warning if listener is running
2. Click "🔌 Connect" → Status: "🟢 Connected"
3. Try "📁 Import Garment" or "▶️ Run Simulation"
4. See activity in CLO's console

#### Cloud Bridge Tab:
1. Status should show "🟢 Cloud Online"
2. Click "Test Connection" → Should succeed
3. Enable "Auto-Sync" toggle
4. Every 15 minutes: automatic context sync
5. Click "Sync Now" for manual sync

---

## 🔧 Troubleshooting

### CLO Issues:

**"Listener not found" warning:**
- Click "Why?" button to see error details
- Click "Retry" to test again
- Click "Hide" to suppress warning this session

**Connection fails:**
```cmd
# Check if something else is using port 51235
netstat -ano | findstr 51235

# Change port if needed
$env:CLO_PORT = "51236"
```

### VPS Issues:

**"SSH connection failed":**
```cmd
# Test SSH manually
ssh -i ~/.ssh/hostinger_vps_rsa root@your-vps-ip

# Check SSH config
notepad ~/.ssh/config
```

**"Health check failed":**
```cmd
# Verify VPS server is running
ssh hostinger-vps "sudo systemctl status julian-cloud-bridge"

# Check VPS logs
ssh hostinger-vps "tail -50 ~/assistant/bridge.log"
```

---

## 📊 Status Indicators

### CLO Bridge States:
- 🟢 **Connected** - Listener running, handshake OK
- 🟡 **Uncertain** - Port open but wrong protocol
- 🔴 **Disconnected** - Listener not reachable

### VPS Bridge States:
- 🟢 **Online** - SSH working, API responding
- 🟡 **Degraded** - Partial connectivity
- 🔴 **Offline** - Cannot reach VPS

---

## 🎁 What You Can Do Now

### With CLO Connected:
- Generate garments from text: *"white cotton t-shirt"*
- Run simulations remotely
- Export designs automatically
- Capture screenshots for documentation

### With VPS Connected:
- Auto-backup vector store every 15min
- Execute LLM queries on VPS GPU
- Sync conversation context
- Access from anywhere (with auth)

---

## 💡 Pro Tips

### CLO:
- Keep CLO listener running while using CLO features
- Listener auto-handles multiple requests
- Check CLO console for detailed logs

### VPS:
- Set `CLOUD_URL` env var for permanent config
- Use HTTPS for production (see VPS_BRIDGE_SETUP.md)
- Enable auto-sync for seamless experience

### Health Monitoring:
- Control Panel auto-checks every 5-10 seconds
- Green indicators = everything working
- Click "Why?" on any red indicator for details

---

## 📞 Quick Help

**Can't connect to CLO?**
→ Run `START_CLO_LISTENER.bat` (standalone mode)
→ Or ensure CLO 3D is running with listener script

**Can't connect to VPS?**
→ Run `.\remote\setup_ssh_keys.ps1` again
→ Check Hostinger VPS is online

**Want to see all status?**
→ Open Control Panel → System tab
→ Or run: `python -c "from modules.academic_rag.health_endpoint import get_full_health; import json; print(json.dumps(get_full_health(), indent=2))"`

---

**Total Setup Time:** < 5 minutes  
**Password Entries:** 1 (VPS password, only once)  
**Manual Steps:** 2 (run listener in CLO, run setup script)

**Everything else is automatic!** 🎉


