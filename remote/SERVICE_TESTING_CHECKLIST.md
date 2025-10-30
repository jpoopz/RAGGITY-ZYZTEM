# Service Testing Checklist - Phase 7.1

**Purpose:** Verify all core Julian Assistant Suite services after VPS optimization

## Pre-Testing Checklist

- [ ] Backup created (`backup_pre_cleanup.sh`)
- [ ] Cleanup completed (`cleanup.sh`)
- [ ] Optimization completed (`optimize.sh`)
- [ ] Security hardening completed (`security_harden.sh`)

## Automated Testing

Run the automated test script:
```bash
./test_services.sh
```

Expected: All tests pass (11/11)

## Manual Testing Checklist

### 1. SSH Access ✓
- [ ] Can connect via SSH from local machine
- [ ] SSH key authentication works
- [ ] Password authentication (if enabled) works

**Test Command:**
```bash
ssh user@vps-ip
```

### 2. Nginx Web Server ✓
- [ ] Nginx service is running
- [ ] HTTP (port 80) responds
- [ ] Default page loads correctly

**Test Commands:**
```bash
systemctl status nginx
curl http://localhost
curl http://[your-domain]
```

### 3. HTTPS/SSL ✓
- [ ] HTTPS (port 443) responds
- [ ] SSL certificate is valid
- [ ] Certificate auto-renewal configured

**Test Commands:**
```bash
curl https://localhost
certbot certificates
certbot renew --dry-run
```

### 4. Docker ✓
- [ ] Docker service is running
- [ ] Can list containers
- [ ] Docker commands work

**Test Commands:**
```bash
systemctl status docker
docker ps -a
docker --version
```

### 5. n8n Workflow Automation ✓
- [ ] n8n service is running
- [ ] Web interface accessible on port 5678
- [ ] Existing workflows still functional

**Test Commands:**
```bash
systemctl status n8n
curl http://localhost:5678
# Open browser: http://[vps-ip]:5678
```

**Expected Response:**
- HTTP 200 or redirect to login page

### 6. Cloud Bridge API ✓
- [ ] Cloud Bridge service is running (if configured)
- [ ] Health endpoint responds on port 8000
- [ ] API endpoints functional

**Test Commands:**
```bash
systemctl status cloud_bridge  # if exists
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status": "healthy", "service": "Cloud Bridge API"}
```

### 7. UFW Firewall ✓
- [ ] UFW is active
- [ ] Required ports are allowed (22, 80, 443, 5678, 8000)
- [ ] Default deny policy active

**Test Commands:**
```bash
sudo ufw status verbose
sudo ufw status numbered
```

**Expected Output:**
```
Status: active
Logging: on
Default: deny (incoming), allow (outgoing)
```

### 8. Fail2ban ✓
- [ ] Fail2ban service is running
- [ ] Jails are active
- [ ] No false positives blocking access

**Test Commands:**
```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

### 9. Python 3.12 ✓
- [ ] Python 3.12 is installed
- [ ] Can import required modules
- [ ] Python scripts execute correctly

**Test Commands:**
```bash
python3.12 --version
python3.12 -c "import sys; print(sys.version)"
```

### 10. Julian Assistant Suite Remote Modules ✓
- [ ] Cloud Bridge connectivity works
- [ ] Remote execution endpoint responds
- [ ] Context sync functional

**Test Commands:**
```bash
# From local machine, test cloud bridge connection
curl -X POST http://[vps-ip]:8000/health \
  -H "Authorization: Bearer [AUTH_TOKEN]"
```

### 11. Resource Availability ✓
- [ ] Disk usage < 90%
- [ ] Free memory > 10%
- [ ] CPU load reasonable

**Test Commands:**
```bash
df -h /
free -h
uptime
```

## Integration Testing

### Test n8n → Cloud Bridge Integration
- [ ] n8n workflow can call Cloud Bridge endpoint
- [ ] Authentication headers work
- [ ] Data syncs correctly

### Test Local → VPS Sync
- [ ] Local suite can connect to VPS
- [ ] Context push/pull works
- [ ] Remote execution returns results

## Performance Testing

### Response Times
- [ ] Nginx serves pages < 100ms
- [ ] n8n loads < 2s
- [ ] Cloud Bridge API < 200ms

**Test Commands:**
```bash
time curl -s http://localhost > /dev/null
time curl -s http://localhost:5678 > /dev/null
time curl -s http://localhost:8000/health > /dev/null
```

## Security Testing

### Port Scanning (from external)
- [ ] Only expected ports are open
- [ ] SSH (22) - ✓
- [ ] HTTP (80) - ✓
- [ ] HTTPS (443) - ✓
- [ ] n8n (5678) - ✓
- [ ] Cloud Bridge (8000) - ✓
- [ ] No unexpected ports open

**Test Command:**
```bash
nmap -p 22,80,443,5678,8000 [vps-ip]
```

## Post-Testing Actions

### If Tests Fail
1. Review service logs: `journalctl -u [service]`
2. Check script logs: `/var/log/julian_*.log`
3. Restore from backup if needed
4. Review audit report for clues

### If Tests Pass
1. Document results in `VPS_OPTIMIZATION_REPORT.md`
2. Update security summary
3. Schedule next maintenance window
4. Monitor system for 24-48 hours

## Testing Schedule

- **After Optimization:** Full test suite (all items)
- **Weekly:** Quick test (automated script only)
- **Monthly:** Full manual test (all items)
- **Quarterly:** Full test + performance audit

## Test Results Template

```
Date: [DATE]
Tester: [NAME]
Environment: [Hostinger VPS]

Automated Tests: [PASS/FAIL] ([X]/11 passed)
Manual Tests: [PASS/FAIL] ([X]/11 passed)

Issues Found:
1. [Issue description]
   Resolution: [If resolved]

Notes:
[Any additional observations]

Signed: [Tester name]
```

---

*Julian Assistant Suite v7.1.0-Julian-VPSClean*  
*Service Testing - Complete Before Production*




