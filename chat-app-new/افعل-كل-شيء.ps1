# Karas Chat - Deploy web + prepare APK
# Run from: D:\programs\Smart_CRM_Final_Arabic\chat-app-new

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$frontendDir = Join-Path $here "frontend"
$googlePlayDir = Join-Path $here "google-play"
$parentDir = Split-Path $here -Parent

Write-Host ""
Write-Host "=== Karas Chat - Deploy ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Building frontend..." -ForegroundColor Yellow
Set-Location $frontendDir
npm run build
if ($LASTEXITCODE -ne 0) { Set-Location $here; exit 1 }
Write-Host "      Done." -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Syncing Android..." -ForegroundColor Yellow
Set-Location $googlePlayDir
npm run sync
if ($LASTEXITCODE -ne 0) { Set-Location $here; exit 1 }
Write-Host "      Done." -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] Pushing to GitHub..." -ForegroundColor Yellow
Set-Location $parentDir
if (Test-Path ".git") {
    $lockFile = Join-Path $parentDir ".git\index.lock"
    if (Test-Path $lockFile) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue }
    if (Test-Path "chat-app-new") { git add chat-app-new/ } else { git add -A }
    $status = git status --porcelain
    if ($status) {
        git commit -m "Karas Chat: invite and auth fixes"
        git push origin main 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      Pushed. Vercel will update in few minutes." -ForegroundColor Green
        } else { Write-Host "      Push failed. Check internet and GitHub." -ForegroundColor Red }
    } else { Write-Host "      No changes to push." -ForegroundColor Yellow }
} else { Write-Host "      Git folder not found - skip push." -ForegroundColor Yellow }
Write-Host ""

$apkPath = Join-Path $googlePlayDir "android\app\build\outputs\apk\release\app-release.apk"
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next: Open Android Studio -> Build -> Generate Signed APK -> Create" -ForegroundColor White
Write-Host "APK path: $apkPath" -ForegroundColor Gray
Write-Host ""

Set-Location $here
