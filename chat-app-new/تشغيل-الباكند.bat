@echo off
chcp 65001 >nul
title Chat Backend - Port 5002
cd /d "%~dp0backend"
echo تشغيل الباكند على البورت 5002...
echo.
call npm start
pause
