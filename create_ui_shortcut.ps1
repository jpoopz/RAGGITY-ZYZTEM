# PowerShell script to create desktop shortcut for RAGGITY ZYZTEM UI
# Run this with: powershell -ExecutionPolicy Bypass -File create_ui_shortcut.ps1

$WorkingDir = $PSScriptRoot
$TargetPath = Join-Path $WorkingDir "run_ui.bat"
$ShortcutPath = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "RAGGITY ZYZTEM UI.lnk")

# Create WScript.Shell COM object
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# Set shortcut properties
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $WorkingDir
$Shortcut.Description = "RAGGITY ZYZTEM 2.0 - RAG System UI"
$Shortcut.WindowStyle = 1  # Normal window

# Try to set icon if available
$IconPath = Join-Path $WorkingDir "assets\julian_assistant.ico"
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
}

# Save the shortcut
$Shortcut.Save()

Write-Host "✓ Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "Shortcut properties:" -ForegroundColor Cyan
Write-Host "  Name: RAGGITY ZYZTEM UI" -ForegroundColor Gray
Write-Host "  Target: $TargetPath" -ForegroundColor Gray
Write-Host "  Working Dir: $WorkingDir" -ForegroundColor Gray
if (Test-Path $IconPath) {
    Write-Host "  Icon: $IconPath" -ForegroundColor Gray
}
Write-Host ""
Write-Host "You can now double-click the desktop shortcut to launch the UI!" -ForegroundColor Green

