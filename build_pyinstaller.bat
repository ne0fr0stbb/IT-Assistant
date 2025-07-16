@echo off
echo ========================================
echo Building I.T Assistant with PyInstaller
echo ========================================
echo.

:: Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

:: Install/update required packages
echo Installing/updating required packages...
pip install -r requirements.txt

:: Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: Build with PyInstaller
echo Building application...
pyinstaller --clean NetworkMonitor_PyInstaller_Fixed.spec

:: Check if build was successful
if exist "dist\I.T Assistant\I.T Assistant.exe" (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Application built to: dist\I.T Assistant\
    echo Executable: dist\I.T Assistant\I.T Assistant.exe
    echo.
    echo You can now copy the entire "I.T Assistant" folder
    echo to any Windows computer and run the application.
    echo.
    pause
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    echo.
    echo Please check the output above for errors.
    echo.
    pause
)
