# Creates a desktop shortcut for RAGGITY ZYZTEM 2.0

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "RAGGITY ZYZTEM 2.0.lnk"
$TargetPath = "C:\Users\Julian Poopat\Documents\RAGGITY_ZYZTEM\launch_raggity.ps1"
$IconPath = "C:\Windows\System32\shell32.dll"
$IconIndex = 165  # Gear/settings icon

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$TargetPath`""
$Shortcut.WorkingDirectory = "C:\Users\Julian Poopat\Documents\RAGGITY_ZYZTEM"
$Shortcut.IconLocation = "$IconPath,$IconIndex"
$Shortcut.Description = "Launch RAGGITY ZYZTEM 2.0 - AI Research Assistant"
$Shortcut.Save()

Write-Host "✅ Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host "🎯 Double-click 'RAGGITY ZYZTEM 2.0' on your desktop to launch!" -ForegroundColor Cyan

