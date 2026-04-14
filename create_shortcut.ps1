# Create Desktop Shortcut for AWS Architecture Explorer
# PowerShell script

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptPath "run_app.bat"

if (-not (Test-Path $batPath)) {
    Write-Host "[ERROR] run_app.bat not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the aws_arch_refactor directory" -ForegroundColor Yellow
    pause
    exit 1
}

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "AWS Architecture Explorer.lnk"

Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow
Write-Host "  Target: $batPath" -ForegroundColor Gray
Write-Host "  Desktop: $desktopPath" -ForegroundColor Gray

try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $batPath
    $shortcut.WorkingDirectory = $scriptPath
    $shortcut.Description = "AWS Architecture Explorer - Direct Access"
    $shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"  # Cloud icon
    $shortcut.Save()
    
    Write-Host ""
    Write-Host "[SUCCESS] Shortcut created on desktop!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now double-click the shortcut to launch the app" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to create shortcut" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
pause
