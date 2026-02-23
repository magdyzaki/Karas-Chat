@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ===== تشغيل الباكند + ngrok =====
echo.

start "Chat Backend" cmd /k "cd /d %~dp0backend && npm start"
timeout /t 5 /nobreak >nul
start "ngrok" cmd /k "%~dp0فتح-ngrok.bat"

echo.
echo تم فتح نافذتين:
echo   1 - الباكند
echo   2 - ngrok
echo.
echo انتظر ngrok يعرض الرابط ثم انسخه وضع في frontend\.env:
echo   VITE_API_URL=https://xxxx.ngrok-free.app
echo.
pause
