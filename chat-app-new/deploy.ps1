# Deploy Karas Chat - Build and push to GitHub
# Run: cd D:\programs\Smart_CRM_Final_Arabic\chat-app-new
#      .\deploy.ps1

$ErrorActionPreference = "Stop"
$rootDir = Split-Path $PSScriptRoot -Parent
$frontendDir = Join-Path $PSScriptRoot "frontend"

Write-Host "=== Karas Chat - Deploy ===" -ForegroundColor Cyan

Write-Host "" -NoNewline
Write-Host "--- Step 1: Build frontend ---" -ForegroundColor Yellow
Push-Location $frontendDir
npm run build
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
Pop-Location

Write-Host "" -NoNewline
Write-Host "--- Step 2: Push to GitHub ---" -ForegroundColor Yellow
Push-Location $rootDir

$lockFile = Join-Path $rootDir ".git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}

git add chat-app-new/
git add .gitignore
$status = git status --porcelain
if ($status) {
    git commit -m "Chat: settings menu consolidation"
    git push origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Push succeeded!" -ForegroundColor Green
        Write-Host "Vercel will update in a few minutes." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Push failed. Check internet and GitHub." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "No changes to push." -ForegroundColor Yellow
}
Pop-Location

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
