# VPS Bridge Setup Guide - Hostinger VPS Configuration

**Version:** 4.0.0  
**Last Updated:** 2025-10-29

---

## 📋 **OVERVIEW**

This guide walks through setting up the Cloud Bridge server on a Hostinger VPS running Ubuntu 25.04. The server provides secure context synchronization and remote task execution capabilities.

---

## 🔧 **PREREQUISITES**

- Hostinger VPS with Ubuntu 25.04
- SSH access to VPS
- Python 3.8+ installed
- Root or sudo access (for systemd service)

---

## 🚀 **STEP 1: INITIAL VPS SETUP**

### Connect to VPS

```bash
ssh user@your-vps-ip
```

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Install Python and Dependencies

```bash
sudo apt install python3 python3-pip python3-venv -y
```

---

## 📦 **STEP 2: DEPLOY CLOUD BRIDGE SERVER**

### Create Directory Structure

```bash
mkdir -p ~/assistant
cd ~/assistant
```

### Upload Server Files

From your local machine:

```bash
scp remote/cloud_bridge_server.py user@your-vps-ip:~/assistant/
scp remote/deploy.sh user@your-vps-ip:~/assistant/
```

### Run Deployment Script

```bash
cd ~/assistant
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Create directories (`context_storage`, `backups`, `keys`)
- Install Python dependencies
- Generate auth token
- Create systemd service file

---

## 🔐 **STEP 3: CONFIGURE SECURITY**

### Generate Auth Token

The deployment script generates a token in `~/assistant/.auth_token`. Copy this token:

```bash
cat ~/assistant/.auth_token
```

**Save this token** - you'll need it for local configuration.

### Copy Public Key

From your local machine:

```bash
scp remote/keys/public.pem user@your-vps-ip:~/assistant/keys/
```

### Set Environment Variable

On VPS, edit `~/.bashrc` or create `~/assistant/.env`:

```bash
export VPS_AUTH_TOKEN="your-token-from-above"
```

Or use the token file directly (systemd service reads from `~/assistant/.auth_token`).

---

## 🌐 **STEP 4: CONFIGURE FIREWALL**

### Allow Port 8000 (or your chosen port)

```bash
sudo ufw allow 8000/tcp
sudo ufw enable
```

### Or use Hostinger Firewall

In Hostinger control panel:
- Add rule: Port 8000, TCP, Allow

---

## 🚀 **STEP 5: START SERVER**

### Manual Start (Testing)

```bash
cd ~/assistant
python3 cloud_bridge_server.py
```

Test in another terminal:

```bash
curl http://localhost:8000/health
```

### Systemd Service (Production)

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable julian-cloud-bridge

# Start service
sudo systemctl start julian-cloud-bridge

# Check status
sudo systemctl status julian-cloud-bridge

# View logs
journalctl -u julian-cloud-bridge -f
```

---

## 🔧 **STEP 6: NGINX REVERSE PROXY (OPTIONAL)**

For HTTPS and domain access:

### Install Nginx

```bash
sudo apt install nginx -y
```

### Configure Nginx

Create `/etc/nginx/sites-available/cloud-bridge`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/cloud-bridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt (Recommended)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## ✅ **STEP 7: VERIFY SETUP**

### Test Health Endpoint

```bash
curl https://your-domain.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "Cloud Bridge Server",
  "version": "4.0.0",
  "encryption": true,
  "timestamp": "2025-10-29T..."
}
```

### Test Ping (Latency)

```bash
curl https://your-domain.com/ping
```

### Test from Local Machine

Update `config/vps_config.json`:

```json
{
  "enabled": true,
  "vps_url": "https://your-domain.com",
  "api_token": "your-token-here",
  "sync_interval": 900,
  "auto_sync": true
}
```

Then test from GUI: "Cloud Sync Now" button

---

## 🔍 **TROUBLESHOOTING**

### Server Won't Start

**Check logs:**
```bash
journalctl -u julian-cloud-bridge -n 50
```

**Check Python:**
```bash
python3 --version
which python3
```

**Check dependencies:**
```bash
pip3 list | grep -E "fastapi|uvicorn|cryptography"
```

### Connection Refused

**Check firewall:**
```bash
sudo ufw status
```

**Check if port is in use:**
```bash
sudo netstat -tulpn | grep 8000
```

**Check server is running:**
```bash
ps aux | grep cloud_bridge_server
```

### Authentication Fails

**Verify token:**
```bash
echo $VPS_AUTH_TOKEN
cat ~/assistant/.auth_token
```

**Check request headers** (use `curl` with `-v` flag)

### High CPU Usage

**Check server logs:**
```bash
journalctl -u julian-cloud-bridge --since "1 hour ago"
```

**Restart service:**
```bash
sudo systemctl restart julian-cloud-bridge
```

---

## 📊 **MONITORING**

### View Live Logs

```bash
journalctl -u julian-cloud-bridge -f
```

### Check Resource Usage

```bash
# CPU, RAM
top

# Disk usage
df -h
du -sh ~/assistant/*
```

### Check Connection Count

```bash
netstat -an | grep :8000 | wc -l
```

---

## 🔒 **SECURITY BEST PRACTICES**

1. **Never commit private keys** to git
2. **Use strong auth tokens** (32+ characters, random)
3. **Enable HTTPS** with Let's Encrypt
4. **Restrict firewall** to known IPs if possible
5. **Regular updates:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
6. **Monitor logs** for suspicious activity
7. **Keep Python packages updated:**
   ```bash
   pip3 install --upgrade fastapi uvicorn cryptography
   ```

---

## 📁 **FILE PERMISSIONS**

Ensure proper permissions:

```bash
chmod 600 ~/assistant/.auth_token
chmod 600 ~/assistant/keys/private.pem  # If exists
chmod 644 ~/assistant/keys/public.pem
chmod 755 ~/assistant
```

---

## 🔄 **UPDATING SERVER**

### Pull New Version

```bash
cd ~/assistant
# Upload new cloud_bridge_server.py
# Then restart:
sudo systemctl restart julian-cloud-bridge
```

### Update Dependencies

```bash
pip3 install --upgrade fastapi uvicorn cryptography
sudo systemctl restart julian-cloud-bridge
```

---

## ✅ **VERIFICATION CHECKLIST**

- [ ] Server starts without errors
- [ ] `/health` endpoint responds
- [ ] `/ping` endpoint returns latency
- [ ] Firewall allows port 8000
- [ ] Auth token is set and working
- [ ] Systemd service auto-starts on boot
- [ ] Nginx (if used) proxies correctly
- [ ] SSL certificate (if used) is valid
- [ ] Local client can connect
- [ ] Context sync works end-to-end
- [ ] Remote execution works
- [ ] Logs are being written

---

**VPS Setup Status:** ✅ Complete  
**Ready for Production:** After verification checklist

---

## 📞 **SUPPORT**

If you encounter issues:

1. Check logs: `journalctl -u julian-cloud-bridge`
2. Verify configuration: `cat ~/assistant/.auth_token`
3. Test connectivity: `curl http://localhost:8000/health`
4. Check firewall: `sudo ufw status`




