@echo off
chcp 65001 >nul
echo ===== بناء تطبيق Karas شات أندرويد =====
echo.

cd /d "%~dp0"

echo [1/4] بناء الواجهة...
cd ..\frontend
call npm run build
if errorlevel 1 (
    echo فشل بناء الواجهة.
    pause
    exit /b 1
)
cd ..\google-play
echo.

echo [2/4] تثبيت الحزم...
call npm install
if errorlevel 1 (
    echo فشل npm install.
    pause
    exit /b 1
)
echo.

if not exist "android" (
    echo [3/4] إضافة منصة أندرويد لأول مرة...
    call npx cap add android
)
echo.

echo [4/4] مزامنة مع أندرويد...
call npx cap sync android
if errorlevel 1 (
    echo فشل cap sync.
    pause
    exit /b 1
)
echo.
echo تم بنجاح.
echo افتح Android Studio: npx cap open android
echo.
pause
