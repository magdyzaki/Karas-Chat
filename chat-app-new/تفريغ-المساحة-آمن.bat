@echo off
chcp 65001 >nul
echo ===== تفريغ مساحة آمن - ملفات cache مؤقتة =====
echo.
echo المجلدات التي سيتم تفريغها (آمنة):
echo   - Temp
echo   - npm cache
echo   - pip cache
echo   - Gradle caches (~1.5 GB) - سيُعاد تحميله عند البناء القادم
echo   - Playwright (لو موجود)
echo   - Chrome Code Cache
echo   - node-gyp
echo   - CrashDumps
echo.
set /p confirm=اكتب نعم للمتابعة: 
if /i not "%confirm%"=="نعم" goto :eof

echo.
echo [1/8] تفريغ Temp...
rd /s /q "%TEMP%" 2>nul
mkdir "%TEMP%"

echo [2/8] تفريغ npm cache...
call npm cache clean --force 2>nul

echo [3/8] تفريغ pip cache...
pip cache purge 2>nul

echo [4/8] تفريغ Gradle caches...
if exist "%USERPROFILE%\.gradle\caches" rd /s /q "%USERPROFILE%\.gradle\caches" 2>nul

echo [5/8] حذف Playwright...
if exist "%LOCALAPPDATA%\ms-playwright" rd /s /q "%LOCALAPPDATA%\ms-playwright" 2>nul

echo [6/8] تفريغ Chrome Code Cache...
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache" rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache" 2>nul

echo [7/8] حذف node-gyp...
if exist "%LOCALAPPDATA%\node-gyp" rd /s /q "%LOCALAPPDATA%\node-gyp" 2>nul

echo [8/8] حذف CrashDumps...
if exist "%LOCALAPPDATA%\CrashDumps" rd /s /q "%LOCALAPPDATA%\CrashDumps" 2>nul

echo.
echo تم. المساحة المحررة تقريباً: ~2-3 GB
pause
