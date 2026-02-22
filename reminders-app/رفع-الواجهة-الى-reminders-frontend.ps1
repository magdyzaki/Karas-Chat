# سكربت رفع واجهة التنبيهات إلى مستودع reminders-frontend
# نفّذه من PowerShell من داخل مجلد reminders-app:
#   cd D:\programs\Smart_CRM_Final_Arabic\reminders-app
#   .\رفع-الواجهة-الى-reminders-frontend.ps1

$ErrorActionPreference = "Stop"
$sourceDir = Join-Path $PSScriptRoot "frontend"
$destDir = "D:\programs\reminders-frontend"

Write-Host "=== خطوة 1: استنساخ reminders-frontend ===" -ForegroundColor Cyan
if (-not (Test-Path $destDir)) {
    Push-Location "D:\programs"
    git clone https://github.com/magdyzaki/reminders-frontend.git
    if ($LASTEXITCODE -ne 0) { Write-Host "فشل الاستنساخ"; exit 1 }
    Pop-Location
} else {
    Write-Host "المجلد موجود - جاري جلب التحديثات..."
    Push-Location $destDir
    git pull origin main
    Pop-Location
}

Write-Host "`n=== خطوة 2: نسخ الملفات (بدون node_modules) ===" -ForegroundColor Cyan
# robocopy: 0-7 = نجاح، 8+ = خطأ
cmd /c robocopy """$sourceDir"" ""$destDir"" /E /XD node_modules .git dist /NFL /NDL"
if ($LASTEXITCODE -ge 8) { Write-Host "فشل النسخ"; exit 1 }

Write-Host "`n=== خطوة 3: الرفع إلى GitHub ===" -ForegroundColor Cyan
Push-Location $destDir
git add -A
$status = git status --porcelain
if ($status) {
    git commit -m "تحديث واجهة التنبيهات - أزرار الأدمن"
    git push origin main
    Write-Host "تم الرفع بنجاح!" -ForegroundColor Green
} else {
    Write-Host "لا يوجد تغييرات - الملفات مطابقة." -ForegroundColor Yellow
}
Pop-Location

Write-Host "`n=== تم بنجاح! ===" -ForegroundColor Green
Write-Host "الآن في Vercel:"
Write-Host "  1. Connect → magdyzaki/reminders-frontend"
Write-Host "  2. Root Directory = فارغ (اتركه empty)"
Write-Host "  3. Redeploy"
