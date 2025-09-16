@echo off
:: Script to run the backend with SSL support on Windows
echo Starting Video Game Calendar Backend with SSL support...
echo.

:: Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not found. Please ensure Python is installed and in your PATH.
    exit /b 1
)

:: Install all required packages
echo Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install required packages. Please check your internet connection and try again.
    exit /b 1
)

echo Checking ZScaler certificate...
if exist "%USERPROFILE%\Downloads\Root.pem" (
    echo Found ZScaler certificate at %USERPROFILE%\Downloads\Root.pem
) else (
    echo ZScaler certificate not found. Will use default certificates.
)

echo Starting backend with Flask SSL support...
python run_with_ssl_windows.py
