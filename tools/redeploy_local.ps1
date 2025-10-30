Param()


$ErrorActionPreference = 'Stop'
$ts = (Get-Date).ToString("yyyy-MM-dd_HHmmss")
$NewRoot = "C:\Users\Julian Poopat\Documents\RAGGITY_ZYZTEM"
$ArchiveRoot = "C:\Users\Julian Poopat\Documents\RAGGITY_Archive\$ts"
$RepoUrl = "https://github.com/jpoopz/RAGGITY-ZYZTEM"
$Port = 8000

Write-Host "=== RAGGITY Local Redeploy @ $ts ==="

# 1) Create archive dir
New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null

# 2) Stop any previous API on port 8000
try {
  $pidList = netstat -ano | Select-String ":$Port " | ForEach-Object {
    ($_ -split '\s+')[-1]
  } | Sort-Object -Unique
  foreach ($p in $pidList) {
    if ($p -match '^\d+$') {
      Write-Host "Stopping process on port $Port, PID=$p"
      taskkill /PID $p /F | Out-Null
    }
  }
} catch { Write-Host "No running API to stop or could not enumerate. Continuing..." }

# 3) Archive candidate old paths if exist
$Candidates = @(
  "C:\Users\Julian Poopat\Desktop\RAG_System",
  "C:\Users\Julian Poopat\Desktop\RAGGITY_ZYZTEM",
  "C:\Users\Julian Poopat\Documents\RAG_System"
)
foreach ($c in $Candidates) {
  if (Test-Path $c) {
    $dest = Join-Path $ArchiveRoot ([IO.Path]::GetFileName($c))
    Write-Host "Archiving $c -> $dest"
    try { Move-Item -Force $c $dest } catch { Write-Host "Skip (locked): $c" }
  }
}

# 3b) Archive sibling leftovers matching patterns (excluding new root)
$Parent = Split-Path $NewRoot -Parent
Get-ChildItem -Path $Parent -Directory | Where-Object {
  $_.FullName -ne $NewRoot -and ($_.Name -match "RAG" -or $_.Name -match "RAGGITY")
} | ForEach-Object {
  $dest = Join-Path $ArchiveRoot $_.Name
  Write-Host "Archiving leftover $($_.FullName) -> $dest"
  try { Move-Item -Force $_.FullName $dest } catch { Write-Host "Skip (locked): $($_.FullName)" }
}

# 4) Fresh clone to NewRoot
if (Test-Path $NewRoot) {
  $backup = "$NewRoot.bak.$ts"
  Write-Host "Existing working dir found. Moving to $backup"
  try { Move-Item -Force $NewRoot $backup } catch { Write-Host "Skip (locked): $NewRoot" }
}
git clone $RepoUrl $NewRoot

# 5) Create venv & install deps
$venv = Join-Path $NewRoot ".venv"
Push-Location $NewRoot
if (!(Test-Path $venv)) { py -3 -m venv .venv }
& .\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# 6) Settings migration (prefer API route if available; else call module)
try {
  Write-Host "Running settings migration helper..."
  python - << 'PYCODE'
import os
try:
    from core.settings_migrate import migrate
    from pathlib import Path
    root = Path(__file__).resolve().parent
    changed, report = migrate(str(root))
    print("MIGRATE:", changed, report)
except Exception as e:
    print("MIGRATE-ERROR:", e)
PYCODE
} catch { Write-Host "Migration helper not available, continuing..." }

# 7) Detect Ollama
$ollamaUp = $false
try {
  $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2
  if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { $ollamaUp = $true }
} catch { $ollamaUp = $false }

# 8) Write provider choice to ui/config.json (fallback if missing)
$uiCfgPath = Join-Path $NewRoot "ui\config.json"
if (!(Test-Path $uiCfgPath)) {
  New-Item -ItemType Directory -Force -Path (Split-Path $uiCfgPath) | Out-Null
  '{}' | Out-File -Encoding utf8 $uiCfgPath
}
$cfgRaw = Get-Content $uiCfgPath -ErrorAction SilentlyContinue | Out-String
try { $cfg = $cfgRaw | ConvertFrom-Json } catch { $cfg = $null }
if ($null -eq $cfg) { $cfg = @{} }
if ($ollamaUp) {
  $cfg.provider = "ollama"
} else {
  if ($null -eq $cfg.provider) { $cfg.provider = "ollama" }
}
$cfg | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $uiCfgPath

# 9) Start API (new window) and UI
if (Test-Path (Join-Path $NewRoot "start_api.bat")) {
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$NewRoot`"; & .\start_api.bat"
} else {
  Write-Host "start_api.bat not found; skipping API start"
}
Start-Sleep -Seconds 3
if (Test-Path (Join-Path $NewRoot "run_ui.bat")) {
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$NewRoot`"; & .\run_ui.bat"
} else {
  Write-Host "run_ui.bat not found; skipping UI start"
}

Pop-Location
Write-Host "=== Redeploy complete. Archives: $ArchiveRoot ==="
Write-Host "API health: http://localhost:8000/health"
if (-not $ollamaUp) {
  Write-Host "Ollama not detected. Optional: install/run Ollama, then: ollama run llama3"
}

