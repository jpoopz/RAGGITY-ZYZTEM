# Test script for all RAG API endpoints

$baseUrl = "http://127.0.0.1:5000"

Write-Host "=== Testing RAG API Endpoints ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "[1/6] Testing /health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "  ✓ Health check passed: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Health check failed - API server may not be running" -ForegroundColor Red
    Write-Host "  Start server with: python rag_api.py" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Query endpoint
Write-Host "[2/6] Testing /query..." -ForegroundColor Yellow
try {
    $body = @{
        query = "What is management?"
        reasoning_mode = "Analytical"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/query" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  ✓ Query successful" -ForegroundColor Green
    Write-Host "  Response length: $($response.response.Length) characters" -ForegroundColor Gray
    Write-Host "  Sources found: $($response.sources.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Query failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Retrieve endpoint
Write-Host "[3/6] Testing /retrieve..." -ForegroundColor Yellow
try {
    $body = @{
        query = "management theories"
        n_results = 3
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/retrieve" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  ✓ Retrieve successful" -ForegroundColor Green
    Write-Host "  Contexts found: $($response.contexts.Count)" -ForegroundColor Gray
    Write-Host "  Average distance: $([math]::Round($response.average_distance, 3))" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Retrieve failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 4: Reindex endpoint
Write-Host "[4/6] Testing /reindex..." -ForegroundColor Yellow
Write-Host "  (This may take a few minutes)" -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/reindex" -Method POST -TimeoutSec 600
    Write-Host "  ✓ Reindex successful: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Reindex may have timed out (normal if many documents)" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host ""

# Test 5: Summarize endpoint
Write-Host "[5/6] Testing /summarize..." -ForegroundColor Yellow
try {
    $body = @{
        text = "Management is the coordination of resources and people to achieve organizational goals. It involves planning, organizing, leading, and controlling activities."
        length = "medium"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/summarize" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  ✓ Summarize successful" -ForegroundColor Green
    Write-Host "  Summary: $($response.summary.Substring(0, [Math]::Min(100, $response.summary.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Summarize failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 6: Plan essay endpoint
Write-Host "[6/6] Testing /plan_essay..." -ForegroundColor Yellow
try {
    $body = @{
        topic = "Strategic Management"
        type = "academic"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/plan_essay" -Method POST -Body $body -ContentType "application/json"
    Write-Host "  ✓ Plan essay successful" -ForegroundColor Green
    Write-Host "  Plan created for: $($response.topic)" -ForegroundColor Gray
    Write-Host "  Sources found: $($response.sources.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Plan essay failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "If all tests passed, your RAG system is working!" -ForegroundColor Cyan
Write-Host "You can now use it in Obsidian via ChatGPT MD plugin." -ForegroundColor Cyan




