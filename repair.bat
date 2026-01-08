@echo off
setlocal enabledelayedexpansion

:: Blend_Repair - Windows Launcher
:: Place your corrupted .blend file in this folder and run this script

cd /d "%~dp0"

:: Find Python
set "PYTHON="
where python >nul 2>&1 && set "PYTHON=python"
where python3 >nul 2>&1 && set "PYTHON=python3"
where py >nul 2>&1 && set "PYTHON=py"

if "%PYTHON%"=="" (
    echo [ERROR] Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

:: Check for zstandard module
%PYTHON% -c "import zstandard" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required module: zstandard...
    %PYTHON% -m pip install zstandard --quiet
)

:: Find .blend files in current directory
set "BLEND_COUNT=0"
set "BLEND_FILE="
for %%f in (*.blend) do (
    if /i not "%%f"=="*_repaired.blend" (
        set /a BLEND_COUNT+=1
        set "BLEND_FILE=%%f"
    )
)

if %BLEND_COUNT%==0 (
    echo.
    echo [ERROR] No .blend files found in this directory.
    echo         Place your corrupted .blend file here and run this script again.
    echo.
    pause
    exit /b 1
)

if %BLEND_COUNT% gtr 1 (
    echo.
    echo [INFO] Multiple .blend files found. Processing all...
    echo.
    for %%f in (*.blend) do (
        echo %%f | findstr /i "_repaired.blend" >nul
        if errorlevel 1 (
            echo.
            echo ========================================
            echo Processing: %%f
            echo ========================================
            %PYTHON% "%~dp0repair_blend.py" "%%f"
        )
    )
) else (
    echo.
    echo Processing: %BLEND_FILE%
    echo.
    %PYTHON% "%~dp0repair_blend.py" "%BLEND_FILE%"
)

echo.
echo Done! Check for *_repaired.blend files.
pause
