# Deploy reminders frontend to reminders-frontend repo
# Run: cd D:\programs\Smart_CRM_Final_Arabic\reminders-app
#      .\deploy-frontend.ps1

$ErrorActionPreference = "Stop"
$sourceDir = Join-Path $PSScriptRoot "frontend"
# استخدم مسار داخل المشروع لتجنب مشاكل الصلاحيات
$destDir = Join-Path $PSScriptRoot "..\reminders-frontend-deploy"
$destDir = [System.IO.Path]::GetFullPath($destDir)

Write-Host "=== Step 1: Clone reminders-frontend ===" -ForegroundColor Cyan
if (-not (Test-Path $destDir)) {
    $parentDir = Split-Path $destDir -Parent
    git clone https://github.com/magdyzaki/reminders-frontend.git $destDir
    if ($LASTEXITCODE -ne 0) { Write-Host "Clone failed"; exit 1 }
} else {
    Write-Host "Folder exists - pulling updates..."
    Push-Location $destDir
    git pull origin main
    Pop-Location
}

Write-Host "`n=== Step 2: Copy files (exclude node_modules) ===" -ForegroundColor Cyan
cmd /c "robocopy `"$sourceDir`" `"$destDir`" /E /XD node_modules .git dist /NFL /NDL"
if ($LASTEXITCODE -ge 8) { Write-Host "Copy failed"; exit 1 }

Write-Host "`n=== Step 3: Push to GitHub ===" -ForegroundColor Cyan
Push-Location $destDir
git add -A
$status = git status --porcelain
if ($status) {
    git commit -m "Update reminders frontend - admin buttons"
    git push origin main
    Write-Host "Push succeeded!" -ForegroundColor Green
} else {
    Write-Host "No changes - files match." -ForegroundColor Yellow
}
Pop-Location

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "In Vercel: Connect to reminders-frontend, Root Directory = empty, Redeploy"
