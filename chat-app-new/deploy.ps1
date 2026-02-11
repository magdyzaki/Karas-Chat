# نشر Karas شات — يشغّل البناء ثم يرفع التحديثات لـ GitHub
# Vercel و Koyeb سيحدّثان تلقائياً عند الرفع
#
# التشغيل: cd D:\programs\Smart_CRM_Final_Arabic\chat-app-new
#          .\deploy.ps1

$ErrorActionPreference = "Stop"
$rootDir = Split-Path $PSScriptRoot -Parent
$frontendDir = Join-Path $PSScriptRoot "frontend"

Write-Host "=== Karas شات — نشر التحديثات ===" -ForegroundColor Cyan

Write-Host "`n--- الخطوة 1: بناء الواجهة ---" -ForegroundColor Yellow
Push-Location $frontendDir
npm run build
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "فشل البناء!" -ForegroundColor Red
    exit 1
}
Pop-Location

Write-Host "`n--- الخطوة 2: رفع التحديثات إلى GitHub ---" -ForegroundColor Yellow
Push-Location $rootDir

# إزالة قفل Git إن وجد
$lockFile = Join-Path $rootDir ".git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}

git add chat-app-new/
git add .gitignore
$status = git status --porcelain
if ($status) {
    git commit -m "تحديث الشات: جرس المكالمة + تحسين الاتصال على باقة الموبايل"
    git push origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nتم الرفع بنجاح!" -ForegroundColor Green
        Write-Host "Vercel سيقوم بتحديث الموقع خلال دقائق." -ForegroundColor Green
    } else {
        Write-Host "`nفشل الرفع. تحقق من اتصال الإنترنت وربط GitHub." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "لا توجد تغييرات جديدة للرفع." -ForegroundColor Yellow
}
Pop-Location

Write-Host "`n=== انتهى ===" -ForegroundColor Cyan
