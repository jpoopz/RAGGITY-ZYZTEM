# PowerShell script to create/update Windows desktop shortcut
# Julian Assistant Suite Launcher - Updated v7.9.7

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Julian Assistant Suite.lnk"
$WorkingDirectory = "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
$LauncherScript = Join-Path $WorkingDirectory "LAUNCH_ASSISTANT.py"

# Find Python interpreter (try multiple locations)
$PythonPaths = @(
    "C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\pythonw.exe",
    "C:\Python312\pythonw.exe",
    "C:\Program Files\Python312\pythonw.exe"
)

$TargetPath = $null
foreach ($path in $PythonPaths) {
    if (Test-Path $path) {
        $TargetPath = $path
        break
    }
}

# If not found, try to find from PATH
if (-not $TargetPath) {
    try {
        $pythonOutput = & where.exe pythonw.exe 2>$null
        if ($pythonOutput) {
            $TargetPath = $pythonOutput[0]
        }
    } catch {
        # Use pythonw.exe from PATH
        $TargetPath = "pythonw.exe"
    }
}

if (-not $TargetPath) {
    Write-Host "❌ Python interpreter not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.12 or update the path in this script." -ForegroundColor Yellow
    exit 1
}

# Verify launcher script exists
if (-not (Test-Path $LauncherScript)) {
    Write-Host "❌ Launcher script not found: $LauncherScript" -ForegroundColor Red
    exit 1
}

# Check and create icon
$IconPath = Join-Path $WorkingDirectory "assets\julian_assistant.ico"
if (-not (Test-Path $IconPath)) {
    Write-Host "Icon not found, generating..." -ForegroundColor Yellow
    $IconGenerator = Join-Path $WorkingDirectory "assets\generate_icon.py"
    if (Test-Path $IconGenerator) {
        python $IconGenerator
    } else {
        Write-Host "⚠️ Icon generator not found, using default icon" -ForegroundColor Yellow
        $IconPath = "$env:SystemRoot\System32\shell32.dll,0"  # Default folder icon
    }
}

# Arguments
$Arguments = "`"$LauncherScript`""

# Remove old shortcut if exists
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "Removed old shortcut" -ForegroundColor Gray
}

# Create new shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

$Shortcut.TargetPath = $TargetPath
$Shortcut.Arguments = $Arguments
$Shortcut.WorkingDirectory = $WorkingDirectory
$Shortcut.Description = "Launch Julian Assistant Suite v7.9.7 - AI Control Hub"
$Shortcut.IconLocation = $IconPath

$Shortcut.Save()

Write-Host "✅ Shortcut created/updated: $ShortcutPath" -ForegroundColor Green
Write-Host "   Target: $TargetPath" -ForegroundColor Gray
Write-Host "   Arguments: $Arguments" -ForegroundColor Gray
Write-Host "   Working Directory: $WorkingDirectory" -ForegroundColor Gray
Write-Host "   Icon: $IconPath" -ForegroundColor Gray
Write-Host "   Version: v7.9.7-Julian-DynamicLLMRouter" -ForegroundColor Gray

# Verify shortcut
if (Test-Path $ShortcutPath) {
    Write-Host "`n✅ Shortcut verification: PASSED" -ForegroundColor Green
} else {
    Write-Host "`n❌ Shortcut verification: FAILED" -ForegroundColor Red
    exit 1
}

