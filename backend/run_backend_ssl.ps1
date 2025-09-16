# PowerShell script to run the backend with SSL support on Windows
Write-Host "Starting Video Game Calendar Backend with SSL support..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "Using $pythonVersion"
}
catch {
    Write-Host "Python is not found. Please ensure Python is installed and in your PATH." -ForegroundColor Red
    exit 1
}

# Install all required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install required packages. Please check your internet connection and try again." -ForegroundColor Red
    exit 1
}

# Check for ZScaler certificate
Write-Host "Checking ZScaler certificate..." -ForegroundColor Yellow
$zscalerCertPath = "$env:USERPROFILE\Downloads\Root.pem"
if (Test-Path $zscalerCertPath) {
    Write-Host "Found ZScaler certificate at $zscalerCertPath" -ForegroundColor Green
}
else {
    Write-Host "ZScaler certificate not found. Will use default certificates." -ForegroundColor Yellow
}

# Set environment variables
$env:SSL_CERT_FILE = $zscalerCertPath
$env:REQUESTS_CA_BUNDLE = $zscalerCertPath

Write-Host "Starting backend with SSL support..." -ForegroundColor Green
Write-Host "Access the API at: https://localhost:5050" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run the Flask app with SSL
python run_with_ssl_windows.py
