@echo off
chcp 65001 >nul 2>&1
cls

echo ============================================
echo   BUILD: Auto SEO Desktop App  v1.0.0
echo ============================================
echo.

cd /d "%~dp0"

:: ---- Buoc 1: Tao icon.ico -----------------------------------------------
echo [1/4] Tao icon.ico...
python make_icon.py
if errorlevel 1 (
    echo     Canh bao: Khong tao duoc icon, dung icon mac dinh.
)
echo     OK
echo.

:: ---- Buoc 2: Cai dependencies neu thieu ----------------------------------
echo [2/4] Kiem tra va cai dependencies...
pip install pyinstaller eel pillow --quiet
if errorlevel 1 (
    echo     LOI: pip install that bai!
    pause
    exit /b 1
)
echo     OK
echo.

:: ---- Buoc 3: Build .exe bang PyInstaller ----------------------------------
echo [3/4] Build exe (PyInstaller) - co the mat 3-5 phut...
echo.

if exist "build"  rmdir /s /q "build"
if exist "dist"   rmdir /s /q "dist"

pyinstaller seo_desktop.spec --noconfirm
if errorlevel 1 (
    echo.
    echo *** LOI: PyInstaller that bai! Xem log o tren. ***
    pause
    exit /b 1
)
echo.
echo     Build exe thanh cong!
echo.

:: ---- Buoc 4: Tao installer bang Inno Setup --------------------------------
echo [4/4] Tao file cai dat (Inno Setup)...

set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe
)

if "%ISCC%"=="" (
    echo.
    echo     Inno Setup chua duoc cai dat - bo qua buoc nay.
    echo     Tai tai: https://jrsoftware.org/isdl.php
    echo.
    goto :done
)

if not exist "installer_output" mkdir "installer_output"
"%ISCC%" installer.iss
if errorlevel 1 (
    echo *** LOI: Inno Setup that bai! ***
    pause
    exit /b 1
)

:done
echo.
echo ============================================
echo   BUILD HOAN TAT!
echo ============================================
echo.
echo   App chay truc tiep:
echo     dist\AutoSEO\AutoSEO.exe
echo.
echo   File cai dat (neu co Inno Setup):
echo     installer_output\AutoSEO_Setup_v1.0.0.exe
echo.
pause
