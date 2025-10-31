# Deploy Cloud Bridge to Hostinger VPS via SSH
# Automated deployment script using SSH key authentication

param(
    [string]$SshAlias = "hostinger-vps"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Cloud Bridge to VPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SSH config exists
$SshConfig = "$env:USERPROFILE\.ssh\config"
if (-not (Test-Path $SshConfig)) {
    Write-Host "ERROR: SSH config not found. Run setup_ssh_keys.ps1 first" -ForegroundColor Red
    exit 1
}

# Verify SSH alias exists
$ConfigContent = Get-Content $SshConfig -Raw
if ($ConfigContent -notmatch "Host $SshAlias") {
    Write-Host "ERROR: SSH alias '$SshAlias' not found in config" -ForegroundColor Red
    Write-Host "Run: .\remote\setup_ssh_keys.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Using SSH alias: $SshAlias" -ForegroundColor Green
Write-Host ""

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
ssh $SshAlias "echo 'Connection successful'"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH connection failed. Check your SSH keys." -ForegroundColor Red
    exit 1
}

Write-Host "✅ SSH connection working" -ForegroundColor Green
Write-Host ""

# Create remote directory
Write-Host "Creating remote directories..." -ForegroundColor Yellow
ssh $SshAlias "mkdir -p ~/assistant/keys ~/assistant/context_storage ~/assistant/backups"

# Copy server files
Write-Host "Uploading server files..." -ForegroundColor Yellow
scp remote/cloud_bridge_server.py "${SshAlias}:~/assistant/"
scp remote/deploy.sh "${SshAlias}:~/assistant/"

# Copy RSA keys if they exist
if (Test-Path "remote/keys/public.pem") {
    Write-Host "Uploading RSA public key..." -ForegroundColor Yellow
    scp remote/keys/public.pem "${SshAlias}:~/assistant/keys/"
}

# Run deployment script on VPS
Write-Host ""
Write-Host "Running deployment script on VPS..." -ForegroundColor Yellow
ssh $SshAlias "cd ~/assistant && chmod +x deploy.sh && ./deploy.sh"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Getting VPS Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get auth token from VPS
$AuthToken = ssh $SshAlias "cat ~/assistant/.auth_token 2>/dev/null"

if ($AuthToken) {
    Write-Host "✅ Retrieved auth token from VPS" -ForegroundColor Green
    Write-Host ""
    Write-Host "Auth Token: $AuthToken" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Save this token securely!" -ForegroundColor Yellow
    
    # Update local config
    $UpdateLocal = Read-Host "Update local config/vps_config.json with this token? (Y/n)"
    
    if ($UpdateLocal -ne 'n' -and $UpdateLocal -ne 'N') {
        $ConfigPath = "config\vps_config.json"
        
        if (Test-Path $ConfigPath) {
            $Config = Get-Content $ConfigPath | ConvertFrom-Json
        } else {
            $Config = @{
                enabled = $true
                vps_url = ""
                api_token = ""
                sync_interval = 900
                auto_sync = $true
                auto_reconnect = $true
            }
        }
        
        # Get VPS IP
        $VpsIp = ssh $SshAlias "curl -s ifconfig.me"
        
        # Update config
        $Config.enabled = $true
        $Config.api_token = $AuthToken
        $Config.auto_sync = $true
        $Config.auto_reconnect = $true
        $Config.ssh_host = $SshAlias
        
        # Prompt for URL
        $DefaultUrl = "http://${VpsIp}:8000"
        Write-Host ""
        Write-Host "VPS URL options:" -ForegroundColor White
        Write-Host "  1. HTTP (testing): $DefaultUrl" -ForegroundColor White
        Write-Host "  2. HTTPS (production): https://your-domain.com" -ForegroundColor White
        Write-Host ""
        $VpsUrl = Read-Host "Enter VPS URL (or press Enter for $DefaultUrl)"
        
        if (-not $VpsUrl) {
            $VpsUrl = $DefaultUrl
        }
        
        $Config.vps_url = $VpsUrl
        
        # Save config
        $Config | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath -Encoding UTF8
        Write-Host "✅ Updated $ConfigPath" -ForegroundColor Green
        
        # Also update environment variables
        Write-Host ""
        Write-Host "Setting environment variables..." -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable("CLOUD_URL", $VpsUrl, "User")
        [Environment]::SetEnvironmentVariable("CLOUD_KEY", $AuthToken, "User")
        Write-Host "✅ Environment variables set (restart terminal to apply)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting VPS Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$StartService = Read-Host "Start cloud bridge service on VPS? (Y/n)"

if ($StartService -ne 'n' -and $StartService -ne 'N') {
    Write-Host "Starting cloud bridge server..." -ForegroundColor Yellow
    
    # Try systemd first
    ssh $SshAlias "sudo systemctl daemon-reload 2>/dev/null && sudo systemctl enable julian-cloud-bridge 2>/dev/null && sudo systemctl start julian-cloud-bridge 2>/dev/null"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Systemd service started" -ForegroundColor Green
        
        # Check status
        ssh $SshAlias "sudo systemctl status julian-cloud-bridge --no-pager"
    } else {
        Write-Host "Systemd not available, starting manually..." -ForegroundColor Yellow
        ssh $SshAlias "cd ~/assistant && nohup python3 cloud_bridge_server.py > bridge.log 2>&1 &"
        Write-Host "✅ Server started in background" -ForegroundColor Green
    }
    
    # Wait for server to start
    Start-Sleep -Seconds 3
    
    # Test health endpoint
    Write-Host ""
    Write-Host "Testing VPS health endpoint..." -ForegroundColor Yellow
    ssh $SshAlias "curl -s http://localhost:8000/ping"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ VPS server is responding!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host ""
Write-Host "1. Test connection from Python:" -ForegroundColor White
Write-Host "   python -c `"from core.cloud_bridge import bridge; print(bridge.health())`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Configure firewall on Hostinger:" -ForegroundColor White
Write-Host "   - Allow port 8000 (or your chosen port)" -ForegroundColor White
Write-Host ""
Write-Host "3. Optional: Set up HTTPS with domain name" -ForegroundColor White
Write-Host "   - See VPS_BRIDGE_SETUP.md for Nginx/SSL guide" -ForegroundColor White
Write-Host ""
Write-Host "4. Enable auto-sync in Control Panel:" -ForegroundColor White
Write-Host "   - Bridge tab > Enable Auto-Sync" -ForegroundColor White
Write-Host ""

# Save SSH alias to config for future use
if (Test-Path $ConfigPath) {
    Write-Host "SSH alias '$SshAlias' configured for automatic connections" -ForegroundColor Green
}

Write-Host ""
Write-Host "Quick Commands:" -ForegroundColor White
Write-Host "  Connect to VPS:       ssh $SshAlias" -ForegroundColor Cyan
Write-Host "  View server logs:     ssh $SshAlias 'tail -f ~/assistant/bridge.log'" -ForegroundColor Cyan
Write-Host "  Restart service:      ssh $SshAlias 'sudo systemctl restart julian-cloud-bridge'" -ForegroundColor Cyan
Write-Host "  Check service status: ssh $SshAlias 'sudo systemctl status julian-cloud-bridge'" -ForegroundColor Cyan
Write-Host ""


