# Fix Tkinter TclError on Windows
# Sets environment variables and verifies Tkinter installation

Write-Host "=== Fixing Tkinter TclError ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Detect Python
Write-Host "[Step 1] Detecting Python installation..." -ForegroundColor Yellow
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "  ✗ Python not found in PATH" -ForegroundColor Red
    Write-Host "  Please ensure Python is installed and in PATH" -ForegroundColor Yellow
    exit 1
}

$pythonExe = $pythonPath.Source
$pythonDir = Split-Path $pythonExe -Parent
$version = python --version 2>&1

Write-Host "  Python: $pythonExe" -ForegroundColor Green
Write-Host "  Version: $version" -ForegroundColor Green
Write-Host "  Directory: $pythonDir" -ForegroundColor Green

# Step 2: Find Tcl/Tk directories
Write-Host "`n[Step 2] Finding Tcl/Tk directories..." -ForegroundColor Yellow
$tclParent = Join-Path $pythonDir "tcl"

if (-not (Test-Path $tclParent)) {
    Write-Host "  ✗ tcl folder not found!" -ForegroundColor Red
    Write-Host "  Attempting to install tk..." -ForegroundColor Yellow
    python -m pip install --upgrade tk --quiet
    Start-Sleep -Seconds 3
    $tclParent = Join-Path $pythonDir "tcl"
}

if (Test-Path $tclParent) {
    # Find actual version directories
    $tclDirs = Get-ChildItem $tclParent -Directory | Where-Object { $_.Name -like "tcl*" }
    $tkDirs = Get-ChildItem $tclParent -Directory | Where-Object { $_.Name -like "tk*" }
    
    if ($tclDirs) {
        $tclDir = ($tclDirs | Sort-Object Name -Descending | Select-Object -First 1).FullName
        Write-Host "  ✓ Found Tcl: $tclDir" -ForegroundColor Green
    } else {
        Write-Host "  ✗ No Tcl version directory found" -ForegroundColor Red
        $tclDir = Join-Path $tclParent "tcl8.6"
    }
    
    if ($tkDirs) {
        $tkDir = ($tkDirs | Sort-Object Name -Descending | Select-Object -First 1).FullName
        Write-Host "  ✓ Found Tk: $tkDir" -ForegroundColor Green
    } else {
        Write-Host "  ✗ No Tk version directory found" -ForegroundColor Red
        $tkDir = Join-Path $tclParent "tk8.6"
    }
} else {
    Write-Host "  ✗ tcl folder still not found after installation attempt" -ForegroundColor Red
    Write-Host "  Trying alternative Python installation..." -ForegroundColor Yellow
    
    # Try common locations
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python*",
        "$env:PROGRAMFILES\Python*",
        "C:\Python*"
    )
    
    foreach ($pathPattern in $commonPaths) {
        $found = Get-ChildItem $pathPattern -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $tclParent = Join-Path $found.FullName "tcl"
            if (Test-Path $tclParent) {
                $tclDir = (Get-ChildItem $tclParent -Directory | Where-Object { $_.Name -like "tcl*" } | Select-Object -First 1).FullName
                $tkDir = (Get-ChildItem $tclParent -Directory | Where-Object { $_.Name -like "tk*" } | Select-Object -First 1).FullName
                Write-Host "  Found in: $($found.FullName)" -ForegroundColor Yellow
                break
            }
        }
    }
}

# Step 3: Set environment variables
Write-Host "`n[Step 3] Setting environment variables..." -ForegroundColor Yellow

if (Test-Path $tclDir) {
    [Environment]::SetEnvironmentVariable("TCL_LIBRARY", $tclDir, "User")
    Write-Host "  ✓ TCL_LIBRARY = $tclDir" -ForegroundColor Green
} else {
    Write-Host "  ✗ Tcl directory not found, cannot set TCL_LIBRARY" -ForegroundColor Red
}

if (Test-Path $tkDir) {
    [Environment]::SetEnvironmentVariable("TK_LIBRARY", $tkDir, "User")
    Write-Host "  ✓ TK_LIBRARY = $tkDir" -ForegroundColor Green
} else {
    Write-Host "  ✗ Tk directory not found, cannot set TK_LIBRARY" -ForegroundColor Red
}

# Step 4: Test Tkinter
Write-Host "`n[Step 4] Testing Tkinter..." -ForegroundColor Yellow

$testScript = @"
import sys
import os

# Set environment variables if not already set
tcl_dir = r"$tclDir"
tk_dir = r"$tkDir"

if os.path.exists(tcl_dir):
    os.environ['TCL_LIBRARY'] = tcl_dir
if os.path.exists(tk_dir):
    os.environ['TK_LIBRARY'] = tk_dir

try:
    import tkinter
    print("✓ Tkinter imported successfully")
    tkinter._test()
    print("✓ Tkinter test passed")
    sys.exit(0)
except Exception as e:
    print(f"✗ Tkinter test failed: {e}")
    sys.exit(1)
"@

$testScript | python
$tkinterWorks = $LASTEXITCODE -eq 0

if ($tkinterWorks) {
    Write-Host "`n✓ Tkinter is working!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Restart any open PowerShell/Command Prompt windows" -ForegroundColor White
    Write-Host "  2. Run: python RAG_Control_Panel.py" -ForegroundColor White
} else {
    Write-Host "`n✗ Tkinter still not working" -ForegroundColor Red
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "  - Try reinstalling Python with 'tcl/tk and IDLE' option" -ForegroundColor White
    Write-Host "  - Or install Python from python.org with all components" -ForegroundColor White
    Write-Host "  - Current environment variables set but may need restart" -ForegroundColor White
}

Write-Host ""




