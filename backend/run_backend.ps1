# PowerShell script to run the backend with or without SSL support
param (
    [switch]$NoSSL,
    [string]$Port = "5050"
)

function Write-ColorText {
    param (
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

# Display banner
Write-ColorText "=======================================" "Cyan"
Write-ColorText "   Video Game Calendar Backend Runner  " "Green"
Write-ColorText "=======================================" "Cyan"
Write-ColorText ""

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-ColorText "Using $pythonVersion" "Gray"
}
catch {
    Write-ColorText "Python is not found. Please ensure Python is installed and in your PATH." "Red"
    exit 1
}

# Install all required packages
Write-ColorText "Installing required packages..." "Yellow"
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-ColorText "Failed to install required packages. Please check your internet connection and try again." "Red"
    exit 1
}

if ($NoSSL) {
    # Run without SSL
    Write-ColorText "Starting backend WITHOUT SSL support..." "Green"
    Write-ColorText "Access the API at: http://localhost:$Port" "Cyan"
    Write-ColorText "Press Ctrl+C to stop the server" "Yellow"
    Write-ColorText ""
    
    # Use environment variable to specify port
    $env:PORT = $Port
    python run.py
}
else {
    # Check for ZScaler certificate
    Write-ColorText "Checking ZScaler certificate..." "Yellow"
    $zscalerCertPath = "$env:USERPROFILE\Downloads\Root.pem"
    if (Test-Path $zscalerCertPath) {
        Write-ColorText "Found ZScaler certificate at $zscalerCertPath" "Green"
    }
    else {
        Write-ColorText "ZScaler certificate not found. Will use default certificates." "Yellow"
    }

    # Set environment variables
    $env:SSL_CERT_FILE = $zscalerCertPath
    $env:REQUESTS_CA_BUNDLE = $zscalerCertPath
    $env:PORT = $Port

    Write-ColorText "Starting backend with SSL support..." "Green"
    Write-ColorText "Access the API at: https://localhost:$Port" "Cyan"
    Write-ColorText "Press Ctrl+C to stop the server" "Yellow"
    Write-ColorText ""

    # Run the Flask app with SSL
    python run_with_ssl_windows.py
}
