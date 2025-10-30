# Smart Troubleshooter Guide

**Version:** v7.0.0-Julian-SelfHealing

## Overview

The Smart Troubleshooter automatically detects, analyzes, and fixes issues in the Julian Assistant Suite. It monitors log files continuously and can either auto-fix safe problems or generate Cursor-ready repair prompts for complex issues.

## Features

✅ **Automatic Detection** - Scans logs every 60 seconds  
✅ **Pattern Recognition** - Identifies common error types  
✅ **Safe Auto-Fix** - Automatically fixes safe issues (pip installs, cache clears)  
✅ **Cursor Prompts** - Generates repair instructions for complex problems  
✅ **Event Integration** - Publishes alerts to event bus  
✅ **GUI Interface** - Visual troubleshooting dashboard

## Usage

### 1. Running Diagnostics

1. Open Julian Assistant Suite Control Panel
2. Navigate to **🛠 Troubleshooter** tab
3. Click **"Run Diagnostics"** button
4. Review detected issues in the list (color-coded by severity)

### 2. Auto-Fixing Issues

1. After running diagnostics, review the issues list
2. Click **"Auto-Fix (Safe Only)"** button
3. The system will attempt to fix:
   - Missing Python packages (pip install)
   - Cache clearing (with backup)
   - Safe configuration updates

**Note:** Only safe operations are auto-fixed. Complex issues require manual intervention.

### 3. Generating Cursor Prompts

1. Select an issue from the list
2. Click **"Copy Cursor Prompt"** button
3. The system generates a Markdown-formatted prompt with:
   - Error summary
   - Recommended fix steps
   - Context information
4. Paste into Cursor AI for automated repair assistance

### 4. Explaining Fixes

1. Select an issue
2. Click **"Explain Fix"** button
3. (Coming soon) LLM-powered explanation of the fix

## Error Categories

### Auto-Fixable
- **Missing Dependency** - Automatically installs via pip
- **Cache Issues** - Clears cache with backup
- **File Permissions** - (Planned) Adjusts permissions safely

### Manual Fix Required
- **Service Down** - Requires manual service restart
- **Database Errors** - May need backup/restore
- **Configuration Errors** - Requires review
- **Port Conflicts** - Needs process management

## Severity Levels

- 🟢 **INFO** - Informational messages
- 🟡 **WARNING** - Non-critical issues
- 🔴 **ERROR** - Critical problems requiring attention

## Log Files

- `Logs/troubleshooter.log` - Troubleshooter activity
- `Logs/YYYY-MM-DD.log` - Main system logs (scanned)
- `backups/troubleshooter/` - Auto-fix backups

## Configuration

Error patterns and fix recommendations are defined in:
- `modules/smart_troubleshooter/troubleshooter_rules.json`

## Safety

- All file modifications are backed up before changes
- Only safe operations (pip install, cache clear) are auto-executed
- Complex fixes always generate Cursor prompts for review
- Event bus alerts notify other modules of detected issues

## Troubleshooting the Troubleshooter

If the troubleshooter itself has issues:

1. Check `Logs/troubleshooter.log`
2. Verify Python dependencies are installed
3. Ensure log files are readable
4. Review event bus connectivity

---

*Julian Assistant Suite v7.0.0-Julian-SelfHealing*




