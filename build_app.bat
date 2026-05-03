@echo off
cd /d D:\Bot_SEO

echo.
echo ========================================
echo   BUILD APP_QUAN_LY.EXE - HUYNH KHANG
echo ========================================
echo.

:: Step 1: Write build_info.json (hash + python path)
echo [1/3] Writing build_info.json...
python -c "import hashlib, json, sys; d=open('App_Quan_Ly.pyw','rb').read(); json.dump({'hash': hashlib.md5(d).hexdigest(), 'python_path': sys.executable}, open('build_info.json','w')); print('Hash:', hashlib.md5(d).hexdigest()); print('Python:', sys.executable)"
if %errorlevel% neq 0 (
    echo ERROR: Cannot write build_info.json
    pause & exit /b 1
)

:: Step 2: Build exe with PyInstaller
echo [2/3] Running PyInstaller...
python -m PyInstaller --onefile --windowed --name "App_Quan_Ly" --add-data "build_info.json;." --clean --noconfirm App_Quan_Ly.pyw
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller failed!
    pause & exit /b 1
)

:: Step 3: Copy to Desktop
echo [3/3] Copying to Desktop...
copy /y "dist\App_Quan_Ly.exe" "%USERPROFILE%\Desktop\App_Quan_Ly.exe"
if %errorlevel% neq 0 (
    echo WARNING: Could not copy to Desktop. Find exe at: dist\App_Quan_Ly.exe
) else (
    echo Copied to: %USERPROFILE%\Desktop\App_Quan_Ly.exe
)

echo.
echo ========================================
echo   BUILD SUCCESS!  dist\App_Quan_Ly.exe
echo ========================================
echo.
pause
