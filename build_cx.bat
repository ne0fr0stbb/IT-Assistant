@echo off
echo Building NetworkMonitor with cx_Freeze...
echo.

REM Clean previous builds
if exist "build" (
    echo Cleaning previous build...
    rmdir /s /q "build"
)

echo.
echo Starting cx_Freeze build...
echo This may take several minutes...
echo.

REM Build with cx_Freeze
python setup.py build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created at: build\exe\NetworkMonitor.exe
    echo File size: 
    dir "build\exe\NetworkMonitor.exe" | findstr "NetworkMonitor.exe"
    echo.
    echo You can now distribute the entire build\exe folder.
    echo All dependencies are included and it can run on Windows machines
    echo without Python or any other dependencies installed.
    echo.
) else (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Common solutions:
    echo - Make sure all Python dependencies are installed
    echo - Check that all source files are present
    echo - Try running: pip install --upgrade cx_Freeze
    echo.
)

pause
