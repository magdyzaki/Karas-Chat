@echo off
chcp 65001 >nul
title ngrok - Chat Backend
cd /d "%~dp0"

set "NGROK_DIR=ngrok-tool"
set "NGROK_EXE=%NGROK_DIR%\ngrok.exe"
set "NGROK_ZIP=%NGROK_DIR%\ngrok.zip"
set "NGROK_URL=https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"

if not exist "%NGROK_DIR%" mkdir "%NGROK_DIR%"

if not exist "%NGROK_EXE%" (
    echo جاري تحميل ngrok...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri '%NGROK_URL%' -OutFile '%NGROK_ZIP%' -UseBasicParsing"
    if not exist "%NGROK_ZIP%" (
        echo فشل التحميل. حمّل يدوياً من: https://ngrok.com/download
        pause
        exit /b 1
    )
    powershell -NoProfile -Command "Expand-Archive -Path '%NGROK_ZIP%' -DestinationPath '%NGROK_DIR%' -Force"
    del "%NGROK_ZIP%" 2>nul
    echo تم تحميل ngrok.
)

echo.
echo تأكد أن الباكند شغّال: cd backend ^& npm start
echo.
echo تشغيل ngrok على البورت 5002...
echo انسخ الرابط https الظاهر وضعه في frontend\.env كقيمة VITE_API_URL
echo.
"%NGROK_EXE%" http 5002
pause
