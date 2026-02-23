@echo off
chcp 65001 >nul
echo بناء APK Release...
echo.

cd /d "%~dp0android"

:: جرب مسارات Android Studio JBR الشائعة
set "JBR="
if exist "C:\Program Files\Android\Android Studio\jbr\bin\java.exe" set "JBR=C:\Program Files\Android\Android Studio\jbr"
if exist "C:\Program Files\Android\Android Studio\jre\bin\java.exe" set "JBR=C:\Program Files\Android\Android Studio\jre"
if exist "%LOCALAPPDATA%\Programs\Android Studio\jbr\bin\java.exe" set "JBR=%LOCALAPPDATA%\Programs\Android Studio\jbr"

set "GRADLE_USER_HOME=G:\gradle-cache"
echo Gradle cache: G:\gradle-cache

if defined JBR (
    set "JAVA_HOME=%JBR%"
    echo استخدام Java من Android Studio
) else (
    echo لم يتم العثور على Java. جرب من Terminal داخل Android Studio.
    echo.
    echo افتح: View ^> Tool Windows ^> Terminal
    echo ثم اكتب: gradlew assembleRelease
    pause
    exit /b 1
)

call gradlew.bat assembleRelease --no-build-cache --no-daemon
if errorlevel 1 (
    echo فشل البناء.
    pause
    exit /b 1
)

echo.
echo تم بنجاح.
echo الملف: app\build\outputs\apk\release\app-release.apk
echo.
explorer "app\build\outputs\apk\release"
pause
