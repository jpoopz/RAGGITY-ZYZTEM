# SSH Key Setup for Hostinger VPS - Passwordless Authentication
# Run this on your local Windows machine

param(
    [string]$VpsHost = "",
    [string]$VpsUser = "root",
    [int]$VpsPort = 22
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SSH Key Setup for Hostinger VPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SSH is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: SSH not found. Install OpenSSH client:" -ForegroundColor Red
    Write-Host "  Settings > Apps > Optional Features > Add OpenSSH Client" -ForegroundColor Yellow
    exit 1
}

# Get VPS details if not provided
if (-not $VpsHost) {
    $VpsHost = Read-Host "Enter your Hostinger VPS IP or domain"
}

Write-Host "VPS Configuration:" -ForegroundColor Green
Write-Host "  Host: $VpsHost"
Write-Host "  User: $VpsUser"
Write-Host "  Port: $VpsPort"
Write-Host ""

# SSH directory setup
$SshDir = "$env:USERPROFILE\.ssh"
if (-not (Test-Path $SshDir)) {
    New-Item -ItemType Directory -Path $SshDir -Force | Out-Null
    Write-Host "Created SSH directory: $SshDir" -ForegroundColor Green
}

$KeyFile = "$SshDir\hostinger_vps_rsa"

# Generate SSH key if not exists
if (-not (Test-Path $KeyFile)) {
    Write-Host "Generating SSH key pair..." -ForegroundColor Yellow
    ssh-keygen -t rsa -b 4096 -f $KeyFile -N '""' -C "julian-assistant-vps"
    Write-Host "✅ SSH key pair generated:" -ForegroundColor Green
    Write-Host "   Private: $KeyFile"
    Write-Host "   Public:  ${KeyFile}.pub"
} else {
    Write-Host "✅ SSH key already exists: $KeyFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 1: Copy SSH Key to VPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Read public key
$PublicKey = Get-Content "${KeyFile}.pub"

Write-Host "Option A: Automated (requires password once):" -ForegroundColor Yellow
Write-Host ""
Write-Host "ssh-copy-id -i ${KeyFile}.pub $VpsUser@$VpsHost" -ForegroundColor White
Write-Host ""

Write-Host "Option B: Manual (if ssh-copy-id not available):" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Copy this public key:" -ForegroundColor White
Write-Host "   $PublicKey" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. SSH to VPS and run:" -ForegroundColor White
Write-Host "   mkdir -p ~/.ssh" -ForegroundColor White
Write-Host "   chmod 700 ~/.ssh" -ForegroundColor White
Write-Host "   echo '$PublicKey' >> ~/.ssh/authorized_keys" -ForegroundColor White
Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor White
Write-Host ""

$CopyKey = Read-Host "Try automated setup now? (y/N)"
if ($CopyKey -eq 'y' -or $CopyKey -eq 'Y') {
    Write-Host "Copying SSH key to VPS (you'll need to enter password once)..." -ForegroundColor Yellow
    
    # Try ssh-copy-id (may not exist on Windows)
    try {
        $PublicKeyContent = Get-Content "${KeyFile}.pub"
        ssh $VpsUser@$VpsHost -p $VpsPort "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$PublicKeyContent' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
        Write-Host "✅ SSH key copied successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Failed automated copy. Please use manual method above." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 2: Test Passwordless SSH" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TestNow = Read-Host "Test SSH connection now? (Y/n)"
if ($TestNow -ne 'n' -and $TestNow -ne 'N') {
    Write-Host "Testing passwordless SSH..." -ForegroundColor Yellow
    ssh -i $KeyFile $VpsUser@$VpsHost -p $VpsPort "echo 'SSH connection successful!'"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Passwordless SSH working!" -ForegroundColor Green
    } else {
        Write-Host "❌ SSH test failed. Verify key was copied correctly." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 3: Create SSH Config" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create/update SSH config
$SshConfig = "$SshDir\config"
$ConfigEntry = @"

# Hostinger VPS - Julian Assistant
Host hostinger-vps
    HostName $VpsHost
    User $VpsUser
    Port $VpsPort
    IdentityFile $KeyFile
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
"@

if (Test-Path $SshConfig) {
    # Check if entry already exists
    $ExistingConfig = Get-Content $SshConfig -Raw
    if ($ExistingConfig -notmatch "Host hostinger-vps") {
        Add-Content -Path $SshConfig -Value $ConfigEntry
        Write-Host "✅ Added 'hostinger-vps' entry to SSH config" -ForegroundColor Green
    } else {
        Write-Host "✅ SSH config entry already exists" -ForegroundColor Green
    }
} else {
    Set-Content -Path $SshConfig -Value $ConfigEntry
    Write-Host "✅ Created SSH config with 'hostinger-vps' entry" -ForegroundColor Green
}

Write-Host ""
Write-Host "You can now connect with:" -ForegroundColor White
Write-Host "  ssh hostinger-vps" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 4: Update Local VPS Config" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ConfigFile = "config\vps_config.json"
$UpdateConfig = Read-Host "Update $ConfigFile with VPS details? (Y/n)"

if ($UpdateConfig -ne 'n' -and $UpdateConfig -ne 'N') {
    # Create config update script
    $VpsUrl = Read-Host "Enter VPS URL (e.g., https://your-domain.com or http://$VpsHost:8000)"
    
    Write-Host ""
    Write-Host "To get your auth token from VPS, run:" -ForegroundColor Yellow
    Write-Host "  ssh hostinger-vps 'cat ~/assistant/.auth_token'" -ForegroundColor White
    Write-Host ""
    
    $Token = Read-Host "Paste the auth token here (or press Enter to set manually later)"
    
    $VpsConfig = @{
        enabled = $true
        vps_url = $VpsUrl
        vps_host = $VpsHost
        vps_user = $VpsUser
        vps_port = $VpsPort
        ssh_key = $KeyFile
        api_token = if ($Token) { $Token } else { "" }
        rsa_public = "remote/keys/public.pem"
        rsa_private = "remote/keys/private.pem"
        sync_interval = 900
        auto_sync = $true
        auto_reconnect = $true
        verify_tls = $true
    }
    
    $VpsConfig | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile -Encoding UTF8
    Write-Host "✅ Updated $ConfigFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. Deploy cloud bridge to VPS:" -ForegroundColor White
Write-Host "   .\remote\deploy_to_vps.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Test connection:" -ForegroundColor White
Write-Host "   python -c 'from core.cloud_bridge import bridge; print(bridge.health())'" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Enable auto-sync in GUI:" -ForegroundColor White
Write-Host "   Cloud Bridge tab > Enable Auto-Sync" -ForegroundColor Cyan
Write-Host ""


