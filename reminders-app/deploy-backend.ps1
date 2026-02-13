# Push reminders backend to reminders-backend repo
# Run: cd D:\programs\Smart_CRM_Final_Arabic\reminders-app
#      .\deploy-backend.ps1

$ErrorActionPreference = "Stop"
$sourceDir = Join-Path $PSScriptRoot "backend"
$destDir = Join-Path $PSScriptRoot "..\reminders-backend-deploy"
$destDir = [System.IO.Path]::GetFullPath($destDir)

Write-Host "=== Step 1: Clone reminders-backend ===" -ForegroundColor Cyan
if (-not (Test-Path $destDir)) {
    git clone https://github.com/magdyzaki/reminders-backend.git $destDir
    if ($LASTEXITCODE -ne 0) { Write-Host "Clone failed"; exit 1 }
} else {
    Write-Host "Folder exists - pulling..."
    Push-Location $destDir
    git pull origin main
    Pop-Location
}

Write-Host "`n=== Step 2: Copy backend files ===" -ForegroundColor Cyan
cmd /c "robocopy `"$sourceDir`" `"$destDir`" /E /XD node_modules .git /NFL /NDL"
if ($LASTEXITCODE -ge 8) { Write-Host "Copy failed"; exit 1 }

Write-Host "`n=== Step 3: Push to GitHub ===" -ForegroundColor Cyan
Push-Location $destDir
git add -A
$status = git status --porcelain
if ($status) {
    git commit -m "Update backend - invite links and admin"
    git push origin main
    Write-Host "Push succeeded!" -ForegroundColor Green
} else {
    Write-Host "No changes." -ForegroundColor Yellow
}
Pop-Location
Write-Host "`nDone. Redeploy on Koyeb." -ForegroundColor Green
