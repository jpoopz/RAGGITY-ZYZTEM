# RAGGITY ZYZTEM 2.0 - Launch Script
# Starts both API and UI

$WorkDir = "C:\Users\Julian Poopat\Documents\RAGGITY_ZYZTEM"

Write-Host "🚀 Launching RAGGITY ZYZTEM 2.0..." -ForegroundColor Cyan

# Check if API is already running on port 8000
$apiRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $apiRunning = $true
        Write-Host "✅ API already running" -ForegroundColor Green
    }
} catch {
    Write-Host "⏳ Starting API..." -ForegroundColor Yellow
}

# Start API if not running
if (-not $apiRunning) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkDir'; .\start_api.bat" -WindowStyle Normal
    Write-Host "⏳ Waiting for API to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Start UI
Write-Host "🎨 Starting UI..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkDir'; .\run_ui.bat" -WindowStyle Normal

Write-Host ""
Write-Host "✨ RAGGITY ZYZTEM 2.0 launched!" -ForegroundColor Green
Write-Host "📍 API: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "🎨 UI: CustomTkinter window" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

