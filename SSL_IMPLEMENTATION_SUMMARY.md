# SSL Implementation Summary

This document summarizes the changes made to enable SSL support for the Video Game Calendar application, particularly to handle ZScaler certificates.

## Files Created or Modified

### New Files:
- `run_with_ssl.py`: Script for running the backend with Gunicorn and SSL on Linux/Mac
- `run_with_ssl_windows.py`: Script for running the backend with Flask's built-in SSL on Windows
- `run_backend_ssl.sh`: Shell script for easily running the backend with SSL on Linux/Mac
- `run_backend_ssl.bat`: Batch script for easily running the backend with SSL on Windows
- `run_backend_ssl.ps1`: PowerShell script for easily running the backend with SSL on Windows
- `run_backend.ps1`: Comprehensive PowerShell script that supports both SSL and non-SSL modes
- `SSL_README.md`: Documentation for SSL setup and usage

### Modified Files:
- `requirements.txt`: Added Gunicorn, certifi, and cryptography packages
- `Dockerfile`: Updated to support SSL certificates and added a Docker entrypoint script
- `docker-compose.yml`: Updated to mount ZScaler certificate and use HTTPS for backend
- `README.md`: Updated with instructions for running the backend with SSL support

## Implementation Details

### Windows Implementation
- Uses Flask's built-in SSL server with a self-signed certificate
- Automatically detects and uses ZScaler Root.pem certificate if available
- Provides both PowerShell and batch scripts for easy execution

### Linux/Mac Implementation
- Uses Gunicorn with SSL support
- Automatically detects and uses ZScaler Root.pem certificate if available
- Provides a shell script for easy execution

### Docker Implementation
- Mounts the ZScaler Root.pem certificate from the host's Downloads folder
- Sets appropriate environment variables for SSL certificate usage
- Uses the Linux implementation with Gunicorn
- Includes a custom entrypoint script to handle certificate detection

## SSL Certificates
- Primary approach: Use the ZScaler Root.pem certificate from the Downloads folder
- Fallback approach: Generate a self-signed certificate for the server
- Environment variables:
  - SSL_CERT_FILE: Points to the ZScaler certificate for system-wide SSL
  - REQUESTS_CA_BUNDLE: Used by the requests library for outgoing HTTPS connections

## Usage Notes
- Always check if the ZScaler certificate exists before running
- The server listens on port 5050 with HTTPS
- Self-signed certificates will generate browser warnings (expected behavior)
