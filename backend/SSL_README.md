# Video Game Calendar Backend with SSL Support

This document explains how to run the backend with SSL support to handle ZScaler certificates.

## Overview

The backend has been configured to use SSL certificate support in two ways:

1. **On Windows**: Using Flask's built-in SSL support
2. **On Linux/Mac**: Using Gunicorn with SSL

Both implementations can:

1. Use an existing certificate from the trusted root store
2. Use the Root.pem certificate from your Downloads folder (for ZScaler)

## Requirements

- Python 3.6+
- certifi (installed via requirements.txt)
- cryptography (installed via requirements.txt)
- Gunicorn (installed via requirements.txt, for Linux/Mac only)

## Running the Backend

### On Windows:

#### Comprehensive PowerShell Script (Recommended)

Use the PowerShell script that supports both SSL and non-SSL modes:

```powershell
# Run with SSL (default)
.\run_backend.ps1

# Run without SSL
.\run_backend.ps1 -NoSSL

# Run with SSL on a custom port
.\run_backend.ps1 -Port 8080
```

#### Alternative Options

1. SSL-only PowerShell script:

```powershell
.\run_backend_ssl.ps1
```

2. Batch file for SSL:

```
run_backend_ssl.bat
```

### On Linux/Mac:

Make the script executable and run it:

```bash
chmod +x run_backend_ssl.sh
./run_backend_ssl.sh
```

This will run Gunicorn with SSL support using the `run_with_ssl.py` script.

### Using Docker:

The Docker setup has been updated to handle SSL certificates automatically:

```bash
# Build and run with docker-compose
docker-compose up -d

# Or build and run the backend container only
docker build -t videogame-calendar-backend ./backend
docker run -p 5050:5050 -v ~/Downloads/Root.pem:/app/ssl/Root.pem:ro videogame-calendar-backend
```

## Certificate Configuration

The system checks for a ZScaler certificate at `~/Downloads/Root.pem`. If found:

1. It sets this certificate file as the default for SSL operations
2. It creates a self-signed certificate for the HTTPS server
3. It configures the environment to use the ZScaler certificate for outgoing requests

If the ZScaler certificate is not found, it uses the default certifi certificate bundle.

## Implementation Details

### Windows Implementation

On Windows, we use Flask's built-in HTTPS server with a self-signed certificate.

### Linux/Mac Implementation

On Linux/Mac, we use Gunicorn with a self-signed certificate.

## Troubleshooting

If you encounter SSL issues:

1. Make sure the Root.pem file is in your Downloads folder
2. Check that required packages are installed:
   ```
   pip install -r requirements.txt
   ```
3. Try running with administrator/root privileges
4. Check the terminal output for detailed error messages
5. If you're using the application behind a proxy, make sure the proxy is configured to accept SSL certificates

### Common Issues

1. **Certificate not trusted by browser**: This is normal with self-signed certificates. You can add an exception in your browser.

2. **ZScaler certificate not found**: The application will still work, but may not properly connect through ZScaler.

3. **Gunicorn not working on Windows**: Windows is not fully supported by Gunicorn. Use the Windows-specific script instead.
