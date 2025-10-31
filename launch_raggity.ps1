param()
$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot"

# Ensure venv
if (-not (Test-Path ".venv\Scripts\python.exe")) { py -3 -m venv .venv }
$py  = ".\.venv\Scripts\python.exe"
$pyw = ".\.venv\Scripts\pythonw.exe"

# Upgrade pip quietly and install deps idempotently
& $py -m pip --disable-pip-version-check -q install --upgrade pip | Out-Null
& $py -m pip -q install -r requirements.txt | Out-Null

# Ensure .env has APP_PORT=8000
$envFile = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envFile) -and (Test-Path ".env.sample")) { Copy-Item .env.sample .env }
if (-not (Test-Path $envFile)) {
  "APP_ENV=local`nAPP_PORT=8000`nLOG_LEVEL=INFO`nDEBUG=false`nCLO_BRIDGE_PORT=9933`n" | Set-Content -NoNewline -Encoding ascii $envFile
} else {
  (Get-Content $envFile) -replace '^APP_PORT=.*','APP_PORT=8000' | Set-Content -NoNewline $envFile
}

# Start API if not running
$apiRunning = Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'uvicorn\s+rag_api:app' }
if (-not $apiRunning) {
  Start-Process -WindowStyle Hidden -FilePath $py -ArgumentList "-m uvicorn rag_api:app --host 127.0.0.1 --port 8000" -WorkingDirectory (Get-Location) | Out-Null
  Start-Sleep -Seconds 2
}

# Launch UI using pythonw (no console)
if (Test-Path $pyw) { Start-Process -FilePath $pyw -ArgumentList "ui\main_window.py" -WorkingDirectory (Get-Location) | Out-Null }
else { Start-Process -FilePath $py -ArgumentList "ui\main_window.py" -WorkingDirectory (Get-Location) | Out-Null }
