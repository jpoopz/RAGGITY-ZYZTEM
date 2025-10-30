# PowerShell script to install dependencies
# Handles Python path issues

Write-Host "=== Installing RAG System Dependencies ===" -ForegroundColor Cyan
Write-Host ""

# Find Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from python.org" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Found Python: $($python.Source)" -ForegroundColor Green
Write-Host ""

# Try to install pip if missing
Write-Host "Checking pip..." -ForegroundColor Cyan
$pipCheck = & $python.Source -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Pip not available, attempting to install..." -ForegroundColor Yellow
    & $python.Source -m ensurepip --default-pip 2>&1 | Out-Null
}

# Install dependencies
Write-Host "Installing packages from requirements.txt..." -ForegroundColor Cyan
Write-Host ""

& $python.Source -m pip install --upgrade pip --quiet
& $python.Source -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ All dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Index documents: python index_documents.py" -ForegroundColor White
    Write-Host "2. Start API: python rag_api.py" -ForegroundColor White
    Write-Host "3. Test: python query_llm.py 'test query'" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Some packages failed to install" -ForegroundColor Red
    Write-Host "Try manually: python -m pip install -r requirements.txt" -ForegroundColor Yellow
}




