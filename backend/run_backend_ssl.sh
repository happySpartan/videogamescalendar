#!/bin/bash
# Script to run the backend with SSL support on Unix/Linux systems
echo -e "\e[32mStarting Video Game Calendar Backend with SSL support...\e[0m"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "\e[31mPython is not found. Please ensure Python is installed and in your PATH.\e[0m"
    exit 1
fi

# Install all required packages
echo -e "\e[33mInstalling required packages...\e[0m"
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "\e[31mFailed to install required packages. Please check your internet connection and try again.\e[0m"
    exit 1
fi

# Check for ZScaler certificate
echo -e "\e[33mChecking ZScaler certificate...\e[0m"
ZSCALER_CERT_PATH="$HOME/Downloads/Root.pem"
if [ -f "$ZSCALER_CERT_PATH" ]; then
    echo -e "\e[32mFound ZScaler certificate at $ZSCALER_CERT_PATH\e[0m"
    # Set environment variables for SSL
    export SSL_CERT_FILE="$ZSCALER_CERT_PATH"
    export REQUESTS_CA_BUNDLE="$ZSCALER_CERT_PATH"
else
    echo -e "\e[33mZScaler certificate not found. Will use default certificates.\e[0m"
fi

echo -e "\e[32mStarting backend with SSL support...\e[0m"
echo -e "\e[36mAccess the API at: https://localhost:5050\e[0m"
echo -e "\e[33mPress Ctrl+C to stop the server\e[0m"
echo

# Run with Gunicorn using SSL
python3 run_with_ssl.py
