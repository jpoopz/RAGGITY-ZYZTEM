# VPS Maintenance Guide - Phase 7.1

**Version:** v7.1.0-Julian-VPSClean  
**Purpose:** Usage guide for cleanup, audit, and optimization scripts

## Overview

This guide explains how to use the maintenance scripts created for the Julian Assistant Suite VPS optimization.

## Prerequisites

- SSH access to VPS
- Root or sudo privileges
- Basic Linux command line knowledge

## Scripts Overview

### 1. `audit.sh` - System Health Check

**Purpose:** Generates comprehensive system audit report

**Usage:**
```bash
cd /remote  # or wherever scripts are located
chmod +x audit.sh
./audit.sh
```

**Output:**
- Report saved to `/backups/VPS_PRE_7_1/audit_reports/audit_[DATE].txt`
- Includes: disk usage, memory, services, packages, ports, processes

**When to Run:**
- Before optimization
- Monthly health checks
- When troubleshooting issues
- After major changes

### 2. `backup_pre_cleanup.sh` - Pre-Optimization Backup

**Purpose:** Creates complete backup before making changes

**Usage:**
```bash
chmod +x backup_pre_cleanup.sh
./backup_pre_cleanup.sh
```

**Output:**
- Backup directory: `/backups/VPS_PRE_7_1/pre_cleanup_[DATE]/`
- Compressed archive: `/backups/VPS_PRE_7_1/pre_cleanup_[DATE].tar.gz`
- Includes: system info, services, packages, configs, cron jobs

**When to Run:**
- **BEFORE** running cleanup.sh
- **BEFORE** running optimize.sh
- Before any major system changes

### 3. `cleanup.sh` - Safe Cleanup

**Purpose:** Removes temporary files, caches, and old logs safely

**Usage:**
```bash
chmod +x cleanup.sh
./cleanup.sh
```

**Actions:**
- Clears apt cache
- Removes unused packages
- Cleans pip cache
- Removes old temp files (>7 days)
- Rotates logs (keeps 30 days)
- Cleans Docker unused resources
- Removes Python cache

**Safety:**
- Creates backup before changes
- Only removes safe files
- Preserves all Julian Assistant Suite data

**When to Run:**
- Monthly maintenance
- When disk space is low
- After package updates

### 4. `optimize.sh` - System Optimization

**Purpose:** Auto-tunes memory, CPU, and I/O settings

**Usage:**
```bash
chmod +x optimize.sh
sudo ./optimize.sh  # Requires root for sysctl changes
```

**Actions:**
- Optimizes swap usage (swappiness = 10)
- Increases file handle limits
- Optimizes TCP settings
- Configures I/O scheduler (for SSDs)
- Sets CPU governor to performance
- Optimizes nginx workers

**Warning:**
- Makes system-wide changes
- Requires root/sudo access
- Review changes before rebooting

**When to Run:**
- After initial setup
- Quarterly optimization
- After hardware changes

### 5. `security_harden.sh` - Security Hardening

**Purpose:** Ensures firewall, fail2ban, and SSL are configured

**Usage:**
```bash
chmod +x security_harden.sh
sudo ./security_harden.sh  # Requires root for firewall/SSL
```

**Actions:**
- Configures UFW firewall (ports 22, 80, 443, 5678, 8000)
- Enables and starts fail2ban
- Verifies SSL certificates
- Reviews SSH configuration
- Audits listening ports

**When to Run:**
- Initial setup
- After security updates
- Quarterly security audits

### 6. `test_services.sh` - Service Testing

**Purpose:** Tests all core services functionality

**Usage:**
```bash
chmod +x test_services.sh
./test_services.sh
```

**Tests:**
- SSH service
- Nginx web server
- HTTPS/SSL
- Docker
- n8n (port 5678)
- Cloud Bridge (port 8000)
- UFW firewall
- Fail2ban
- Python 3.12
- Disk space
- Memory availability

**Output:**
- Test results: ✓ Pass / ✗ Fail
- Summary report at end
- Log file: `/var/log/julian_service_test.log`

**When to Run:**
- After optimization
- After service changes
- Weekly health checks
- When troubleshooting

## Maintenance Workflow

### Initial Optimization (One-Time)

```bash
# 1. Audit current state
./audit.sh

# 2. Create backup
./backup_pre_cleanup.sh

# 3. Run cleanup (safe)
./cleanup.sh

# 4. Optimize system (requires sudo)
sudo ./optimize.sh

# 5. Harden security (requires sudo)
sudo ./security_harden.sh

# 6. Test services
./test_services.sh

# 7. Review reports
cat /backups/VPS_PRE_7_1/audit_reports/audit_*.txt
```

### Monthly Maintenance

```bash
# 1. Quick audit
./audit.sh

# 2. Cleanup
./cleanup.sh

# 3. Test services
./test_services.sh
```

### Quarterly Maintenance

```bash
# 1. Full audit
./audit.sh

# 2. Backup before changes
./backup_pre_cleanup.sh

# 3. Cleanup
./cleanup.sh

# 4. Optimize (if needed)
sudo ./optimize.sh

# 5. Security check
sudo ./security_harden.sh

# 6. Full service test
./test_services.sh
```

## Troubleshooting

### Script Permission Denied
```bash
chmod +x script_name.sh
```

### Script Requires Root
```bash
sudo ./script_name.sh
```

### Can't Find Scripts
```bash
# Locate scripts
find / -name "*.sh" -path "*/remote/*" 2>/dev/null

# Or check expected location
ls -la ~/assistant/remote/
ls -la /remote/
```

### Services Not Responding After Optimization
1. Check service status: `systemctl status [service]`
2. Review logs: `journalctl -u [service]`
3. Restore from backup if needed
4. Test services: `./test_services.sh`

### Restore from Backup

```bash
# Extract backup
cd /backups/VPS_PRE_7_1
tar -xzf pre_cleanup_[DATE].tar.gz

# Review manifest
cat pre_cleanup_[DATE]/manifest.txt

# Restore specific service (example)
cp pre_cleanup_[DATE]/systemd/n8n.service /etc/systemd/system/
systemctl daemon-reload
systemctl restart n8n
```

## Best Practices

1. **Always Backup First** - Run `backup_pre_cleanup.sh` before major changes
2. **Test After Changes** - Run `test_services.sh` after optimization
3. **Monitor Resources** - Run `audit.sh` regularly
4. **Review Logs** - Check script log files for warnings
5. **Gradual Changes** - Make changes incrementally, not all at once
6. **Document Changes** - Note any manual modifications

## Log Files

All scripts create logs:
- `cleanup.sh` → `/var/log/julian_cleanup.log`
- `optimize.sh` → `/var/log/julian_optimize.log`
- `security_harden.sh` → `/var/log/julian_security.log`
- `test_services.sh` → `/var/log/julian_service_test.log`

## Backup Locations

- **Pre-cleanup backups:** `/backups/VPS_PRE_7_1/pre_cleanup_[DATE]/`
- **Audit reports:** `/backups/VPS_PRE_7_1/audit_reports/`
- **Compressed archives:** `/backups/VPS_PRE_7_1/*.tar.gz`

## Support

If issues occur:
1. Review relevant log file
2. Check service status: `systemctl status [service]`
3. Restore from backup if needed
4. Review audit report for clues
5. Test services to identify problem

---

*Julian Assistant Suite v7.1.0-Julian-VPSClean*  
*Maintenance Scripts - Ready for Use*




