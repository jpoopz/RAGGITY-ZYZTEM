# RAG Academic Assistant - Silent Launcher (PowerShell)
# Runs GUI without console window

# Change to script directory
Set-Location $PSScriptRoot

# Log launch time
$logDir = Join-Path $PSScriptRoot "Logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$logFile = Join-Path $logDir "launch.log"
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Launching RAG Control Panel" | Add-Content -Path $logFile

# Check for pythonw (windowless Python)
$pythonw = Get-Command pythonw -ErrorAction SilentlyContinue

if ($pythonw) {
    # Use pythonw for silent execution
    Start-Process pythonw -ArgumentList "`"$PSScriptRoot\RAG_Control_Panel.py`"" -WindowStyle Hidden
} else {
    # Fallback to python with minimized window
    Start-Process python -ArgumentList "`"$PSScriptRoot\RAG_Control_Panel.py`"" -WindowStyle Minimized
}




