# PowerShell script to run GROBID in Docker
# GROBID: GeneRation Of BIbliographic Data
# Extracts structured metadata and references from PDFs

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GROBID Docker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Docker is running" -ForegroundColor Green
Write-Host ""

# Pull GROBID image
Write-Host "Pulling GROBID Docker image..." -ForegroundColor Cyan
docker pull lfoppiano/grobid:0.8.0

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to pull GROBID image" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Starting GROBID server on port 8070..." -ForegroundColor Cyan
Write-Host "This may take a minute on first run..." -ForegroundColor Yellow
Write-Host ""

# Run GROBID container
docker run --init --rm -p 8070:8070 lfoppiano/grobid:0.8.0

# Note: --rm removes container when stopped
# Note: --init handles signals properly
# The container will run in foreground; Ctrl+C to stop

Write-Host ""
Write-Host "GROBID server stopped" -ForegroundColor Yellow


