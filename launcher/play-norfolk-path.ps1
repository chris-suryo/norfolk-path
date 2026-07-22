# Norfolk Path - local playtest launcher (Windows PowerShell).
#
# Don't run this directly - use the desktop shortcut that Install-Shortcut.ps1
# makes (it sets the execution policy + icon for you). What this does on each
# launch: find Godot 4.7, sync the repo to the EXACT pinned version, import any
# new assets, then run the game - and print a banner so you always know which
# build you're testing.
#
# The playtest branch is treated as READ-ONLY: local edits are stashed (never
# hard-deleted - recover with `git stash list`) so the sync can guarantee the
# right version. Tune by telling the build session the values; it bakes them
# into the real PRs.

param([string]$Branch = "playtest/beta")

$ErrorActionPreference = "Stop"
# The repo is this script's parent folder (launcher/ lives inside the repo).
$Repo = Split-Path $PSScriptRoot -Parent

function Fail($m) { Write-Host "`n[X] $m" -ForegroundColor Red; Read-Host "Press Enter to close"; exit 1 }

if (-not (Test-Path (Join-Path $Repo "project.godot"))) {
	Fail "This script must live in <repo>\launcher\. Couldn't find project.godot in $Repo."
}
Set-Location $Repo

# --- find Godot 4.7 (cache the answer next to this script) -----------------
$cache = Join-Path $PSScriptRoot ".godot-path"
$godot = ""
if (Test-Path $cache) { $godot = (Get-Content $cache -Raw).Trim() }
if (-not $godot -or -not (Test-Path $godot)) {
	$onPath = (Get-Command godot -ErrorAction SilentlyContinue).Source
	if ($onPath) { $godot = $onPath }
	if (-not $godot) {
		$godot = Get-ChildItem "$env:USERPROFILE\Downloads", "$env:USERPROFILE\Desktop", "$env:LOCALAPPDATA" `
			-Recurse -Filter "Godot_v4.7*.exe" -ErrorAction SilentlyContinue |
			Select-Object -First 1 -ExpandProperty FullName
	}
	if (-not $godot) { $godot = Read-Host "Full path to your Godot 4.7 .exe" }
	if (-not (Test-Path $godot)) { Fail "Godot not found at '$godot'." }
	Set-Content $cache $godot
}

# --- sync to the exact pinned version --------------------------------------
Write-Host "Fetching latest..." -ForegroundColor Cyan
git fetch origin --prune
if (git status --porcelain) {
	Write-Host "Stashing local changes (recover later with 'git stash list')..." -ForegroundColor Yellow
	git stash push -u -m "auto-stash before playtest sync" | Out-Null
}
if (git rev-parse --verify --quiet "origin/$Branch") {
	git checkout -B $Branch "origin/$Branch" | Out-Null
	git reset --hard "origin/$Branch" | Out-Null
}
elseif (git rev-parse --verify --quiet $Branch) {
	git checkout $Branch | Out-Null   # local-only branch
}
else {
	Fail "Branch '$Branch' not found locally or on origin."
}
$sha = (git rev-parse --short HEAD)
$when = (git log -1 --format=%cd --date=short)

# --- import new assets (fast when nothing changed), then run ---------------
Write-Host "Importing assets..." -ForegroundColor Cyan
& $godot --headless --editor --path $Repo --quit 2>$null

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "  RUNNING: $Branch @ $sha  ($when)" -ForegroundColor Green
Write-Host "  (close the game window to exit)" -ForegroundColor DarkGray
Write-Host "===============================================================" -ForegroundColor Green
Write-Host ""
& $godot --path $Repo
