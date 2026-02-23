@echo off
chcp 65001 >nul
:: يحتاج تشغيل كمسؤول (Run as Administrator)
:: نقل المجلدات الكبيرة من C إلى G وتعديل المسارات

echo ===== نقل المجلدات من C إلى G =====
echo.
echo يجب تشغيل هذا الملف كمسؤول (Run as Administrator)
echo اضغط يمين على الملف ^> تشغيل كمسؤول
echo.
echo تأكد أن G:\ موجود وبه مساحة كافية
echo.
pause

set G_BASE=G:\UserData
if not exist "%G_BASE%" mkdir "%G_BASE%"

echo.
echo اختر ما تريد نقله:
echo 1 - Downloads
echo 2 - Documents  
echo 3 - Desktop
echo 4 - كل ما سبق
echo 0 - إلغاء
set /p choice=اختر رقم: 

if "%choice%"=="0" goto :eof
if "%choice%"=="4" set move_all=1

:: نقل Downloads
if "%choice%"=="1" set do_dl=1
if "%move_all%"=="1" set do_dl=1

:: نقل Documents
if "%choice%"=="2" set do_doc=1
if "%move_all%"=="1" set do_doc=1

:: نقل Desktop
if "%choice%"=="3" set do_desktop=1
if "%move_all%"=="1" set do_desktop=1

echo.
echo سيتم نقل المجلدات. تأكد من إغلاق البرامج التي تستخدمها.
pause

if defined do_dl (
    echo [1] نقل Downloads...
    if not exist "%G_BASE%\Downloads" mkdir "%G_BASE%\Downloads"
    xcopy "%USERPROFILE%\Downloads\*" "%G_BASE%\Downloads\" /E /H /Y /I 2>nul
    rmdir /s /q "%USERPROFILE%\Downloads" 2>nul
    mklink /D "%USERPROFILE%\Downloads" "%G_BASE%\Downloads" 2>nul
    if exist "%USERPROFILE%\Downloads" (echo   تم إنشاء الرابط الرمزي لـ Downloads) else (echo   فشل - نفذ كمسؤول)
)

if defined do_doc (
    echo [2] نقل Documents...
    if not exist "%G_BASE%\Documents" mkdir "%G_BASE%\Documents"
    xcopy "%USERPROFILE%\Documents\*" "%G_BASE%\Documents\" /E /H /Y /I 2>nul
    rmdir /s /q "%USERPROFILE%\Documents" 2>nul
    mklink /D "%USERPROFILE%\Documents" "%G_BASE%\Documents" 2>nul
    if exist "%USERPROFILE%\Documents" (echo   تم إنشاء الرابط الرمزي لـ Documents) else (echo   فشل - نفذ كمسؤول)
)

if defined do_desktop (
    echo [3] نقل Desktop...
    if not exist "%G_BASE%\Desktop" mkdir "%G_BASE%\Desktop"
    xcopy "%USERPROFILE%\Desktop\*" "%G_BASE%\Desktop\" /E /H /Y /I 2>nul
    rmdir /s /q "%USERPROFILE%\Desktop" 2>nul
    mklink /D "%USERPROFILE%\Desktop" "%G_BASE%\Desktop" 2>nul
    if exist "%USERPROFILE%\Desktop" (echo   تم إنشاء الرابط الرمزي لـ Desktop) else (echo   فشل - نفذ كمسؤول)
)

echo.
echo انتهى.
echo.
echo ملاحظة: نقل Android SDK يتم من داخل Android Studio:
echo   File ^> Settings ^> Android SDK ^> Android SDK location: G:\Android\Sdk
pause
