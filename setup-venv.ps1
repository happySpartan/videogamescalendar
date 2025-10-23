# Virtual Environment Setup Script for Video Game Calendar
# Run this script to create isolated Python environments for each service

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Video Game Calendar - Virtual Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Determine script directory
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

Write-Host "Project directory: $scriptDir" -ForegroundColor Gray
Write-Host ""

# Check if Python 3.12 is available
$pythonCmd = $null
$pythonVersion = $null

Write-Host "Searching for Python 3.12..." -ForegroundColor White

# Try py launcher first (most reliable on Windows)
if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
        $testOutput = & py -3.12 --version 2>&1
        if ($testOutput -match "Python 3\.12") {
            $pythonCmd = "py"
            $pythonArgs = @("-3.12")
            $pythonVersion = $testOutput
            Write-Host "✓ Found Python 3.12 via py launcher: $pythonVersion" -ForegroundColor Green
        }
    } catch {
        # Python 3.12 not available via py launcher
    }
}

# If not found via py launcher, try direct python3.12 command
if (-not $pythonCmd -and (Get-Command python3.12 -ErrorAction SilentlyContinue)) {
    try {
        $testOutput = & python3.12 --version 2>&1
        if ($testOutput -match "Python 3\.12") {
            $pythonCmd = "python3.12"
            $pythonArgs = @()
            $pythonVersion = $testOutput
            Write-Host "✓ Found Python 3.12 as python3.12: $pythonVersion" -ForegroundColor Green
        }
    } catch {
        # Not this one either
    }
}

if (-not $pythonCmd) {
    Write-Host ""
    Write-Host "✗ Python 3.12 not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.12 from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/release/python-31210/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "During installation:" -ForegroundColor Yellow
    Write-Host "  1. Check 'Add python.exe to PATH'" -ForegroundColor White
    Write-Host "  2. Check 'Install for all users' (optional)" -ForegroundColor White
    Write-Host "  3. Complete the installation" -ForegroundColor White
    Write-Host "  4. Restart PowerShell/Terminal" -ForegroundColor White
    Write-Host "  5. Run this script again" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Function to create venv for a service
function Setup-ServiceVenv {
    param(
        [string]$ServicePath,
        [string]$ServiceName,
        [string]$PythonCommand,
        [string[]]$PythonArguments
    )

    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host "Setting up: $ServiceName" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan

    # Build full paths
    $fullServicePath = Join-Path $scriptDir $ServicePath
    $venvPath = Join-Path $fullServicePath ".venv"
    $venvPythonPath = Join-Path $venvPath "Scripts\python.exe"
    $venvPipPath = Join-Path $venvPath "Scripts\pip.exe"
    $requirementsPath = Join-Path $fullServicePath "requirements.txt"

    # Verify service directory exists
    if (-not (Test-Path $fullServicePath)) {
        Write-Host "  ✗ Service directory not found: $fullServicePath" -ForegroundColor Red
        Write-Host ""
        return $false
    }

    # Verify requirements.txt exists
    if (-not (Test-Path $requirementsPath)) {
        Write-Host "  ✗ requirements.txt not found: $requirementsPath" -ForegroundColor Red
        Write-Host ""
        return $false
    }

    Write-Host "  Service path: $fullServicePath" -ForegroundColor Gray
    Write-Host "  Virtual env:  $venvPath" -ForegroundColor Gray
    Write-Host ""

    # Remove old venv if exists
    if (Test-Path $venvPath) {
        Write-Host "  Removing old virtual environment..." -ForegroundColor Yellow
        try {
            Remove-Item -Recurse -Force $venvPath -ErrorAction Stop
            Start-Sleep -Milliseconds 500
            Write-Host "  ✓ Old environment removed" -ForegroundColor Gray
        } catch {
            Write-Host "  ⚠ Warning: Could not fully remove old environment: $_" -ForegroundColor Yellow
            Write-Host "  Continuing anyway..." -ForegroundColor Gray
        }
        Write-Host ""
    }

    # Create new venv
    Write-Host "  Creating virtual environment with Python 3.12..." -ForegroundColor White

    try {
        # Change to service directory
        Push-Location $fullServicePath

        # Build command
        $venvCommand = @($PythonCommand) + $PythonArguments + @("-m", "venv", ".venv")

        # Execute venv creation
        $output = & $venvCommand[0] $venvCommand[1..($venvCommand.Length-1)] 2>&1

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Failed to create virtual environment" -ForegroundColor Red
            Write-Host "  Command: $venvCommand" -ForegroundColor Gray
            Write-Host "  Output: $output" -ForegroundColor Red
            Pop-Location
            Write-Host ""
            return $false
        }

        # Verify python.exe exists
        if (-not (Test-Path $venvPythonPath)) {
            Write-Host "  ✗ Virtual environment created but python.exe not found at:" -ForegroundColor Red
            Write-Host "     $venvPythonPath" -ForegroundColor Red

            # Debug: List what's actually in the .venv directory
            if (Test-Path $venvPath) {
                Write-Host "  Contents of .venv:" -ForegroundColor Yellow
                Get-ChildItem $venvPath | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
            }

            Pop-Location
            Write-Host ""
            return $false
        }

        Write-Host "  ✓ Virtual environment created successfully" -ForegroundColor Green
        Write-Host ""

        # Upgrade pip
        Write-Host "  Upgrading pip..." -ForegroundColor White
        $pipOutput = & $venvPythonPath -m pip install --upgrade pip --quiet 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ pip upgraded" -ForegroundColor Gray
        } else {
            Write-Host "  ⚠ Warning: pip upgrade had issues (continuing anyway)" -ForegroundColor Yellow
        }
        Write-Host ""

        # Remove pip-system-certs if present
        Write-Host "  Removing pip-system-certs (if present)..." -ForegroundColor White
        & $venvPythonPath -m pip uninstall pip-system-certs -y --quiet 2>&1 | Out-Null
        Write-Host "  ✓ pip-system-certs removed (if it was there)" -ForegroundColor Gray
        Write-Host ""

        # Install requirements
        Write-Host "  Installing dependencies from requirements.txt..." -ForegroundColor White
        Write-Host "  (This may take a minute...)" -ForegroundColor Gray

        $installOutput = & $venvPythonPath -m pip install -r requirements.txt 2>&1

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
            Write-Host ""
            Write-Host "  Error output:" -ForegroundColor Red
            Write-Host $installOutput -ForegroundColor Red
            Pop-Location
            Write-Host ""
            return $false
        }

        Write-Host "  ✓ Dependencies installed successfully" -ForegroundColor Green
        Write-Host ""

        # Verify installation by counting packages
        Write-Host "  Verifying installation..." -ForegroundColor White
        $packageList = & $venvPythonPath -m pip list --format=freeze 2>&1
        if ($packageList) {
            $packageCount = ($packageList | Measure-Object -Line).Lines
            Write-Host "  ✓ Installed $packageCount packages" -ForegroundColor Green

            # Show a few key packages
            $keyPackages = @("redis", "fastapi", "uvicorn", "celery", "sqlalchemy")
            $foundPackages = @()
            foreach ($pkg in $keyPackages) {
                if ($packageList -match "^$pkg==") {
                    $foundPackages += $pkg
                }
            }
            if ($foundPackages.Count -gt 0) {
                Write-Host "  Key packages: $($foundPackages -join ', ')" -ForegroundColor Gray
            }
        }

        Pop-Location
        Write-Host ""
        Write-Host "  ✓ $ServiceName setup complete!" -ForegroundColor Green
        Write-Host ""
        return $true

    } catch {
        Write-Host "  ✗ Unexpected error: $_" -ForegroundColor Red
        Write-Host "  Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Gray
        if (Get-Location | Select-Object -ExpandProperty Path -ne $scriptDir) {
            Pop-Location
        }
        Write-Host ""
        return $false
    }
}

# Setup each service
Write-Host "Starting setup for all services..." -ForegroundColor Cyan
Write-Host ""

$services = @(
    @{Path = "services\game-api"; Name = "Game API"}
    @{Path = "services\admin-api"; Name = "Admin API"}
    @{Path = "services\data-sync"; Name = "Data Sync"}
)

$successCount = 0
$failCount = 0

foreach ($service in $services) {
    $success = Setup-ServiceVenv -ServicePath $service.Path -ServiceName $service.Name -PythonCommand $pythonCmd -PythonArguments $pythonArgs
    if ($success) {
        $successCount++
    } else {
        $failCount++
    }
}

# Final summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "✓ Successfully created all $successCount virtual environments!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Close VS Code completely:" -ForegroundColor White
    Write-Host "   File → Exit (or Alt+F4)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Reopen the project:" -ForegroundColor White
    Write-Host "   File → Open Folder → Select: videogamecalendar" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Select Python interpreter (if prompted):" -ForegroundColor White
    Write-Host "   Ctrl+Shift+P → Python: Select Interpreter" -ForegroundColor Gray
    Write-Host "   Choose: Python 3.12.x ('.venv': venv)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Start debugging:" -ForegroundColor White
    Write-Host "   Press F5 → Select '🎮 Debug Game API'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To verify it worked:" -ForegroundColor Cyan
    Write-Host "  cd services\game-api" -ForegroundColor Gray
    Write-Host "  .\.venv\Scripts\python.exe --version" -ForegroundColor Gray
    Write-Host "  (should show: Python 3.12.x)" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "⚠ Setup completed with issues:" -ForegroundColor Yellow
    Write-Host "  Successful: $successCount" -ForegroundColor Green
    Write-Host "  Failed: $failCount" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Python 3.12 not installed correctly" -ForegroundColor White
    Write-Host "  2. Antivirus blocking file creation" -ForegroundColor White
    Write-Host "  3. Insufficient permissions" -ForegroundColor White
    Write-Host ""
    Write-Host "Please check the errors above and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "If problems persist, try the manual setup:" -ForegroundColor Cyan
    Write-Host "  See VENV_SETUP.md for manual instructions" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
