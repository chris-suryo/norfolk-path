# Creates a "Norfolk Path (playtest)" shortcut on your Desktop that launches
# the game via play-norfolk-path.ps1. Run this ONCE:
#
#   powershell -ExecutionPolicy Bypass -File launcher\Install-Shortcut.ps1
#
# Re-run it any time to fix the shortcut. Pass -Branch to pin a different build
# (default: the combined playtest/beta).

param([string]$Branch = "playtest/beta")

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$launcher = Join-Path $PSScriptRoot "play-norfolk-path.ps1"
$icon = Join-Path $PSScriptRoot "norfolk-path.ico"
$link = Join-Path ([Environment]::GetFolderPath("Desktop")) "Norfolk Path (playtest).lnk"

$sh = New-Object -ComObject WScript.Shell
$sc = $sh.CreateShortcut($link)
$sc.TargetPath = "powershell.exe"
$sc.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launcher`" $Branch"
$sc.WorkingDirectory = $repo
if (Test-Path $icon) { $sc.IconLocation = $icon }
$sc.Description = "Launch Norfolk Path ($Branch), syncing to the latest first."
$sc.Save()

Write-Host "Created: $link" -ForegroundColor Green
Write-Host "It launches: $Branch" -ForegroundColor Green
Write-Host "Double-click it to play." -ForegroundColor Green
