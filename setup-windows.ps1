# Ollama Chat Setup Script for Windows
# This script creates a virtual environment and installs dependencies

Write-Host "=== Ollama Chat Setup for Windows ===" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $majorVersion = [int]$matches[1]
        $minorVersion = [int]$matches[2]
        if ($majorVersion -eq 3 -and $minorVersion -ge 8) {
            Write-Host "✓ Python $pythonVersion found" -ForegroundColor Green
        } else {
            Write-Host "✗ Python 3.8 or higher required. Found: $pythonVersion" -ForegroundColor Red
            Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
            Read-Host -Prompt "Press Enter to exit"
            exit 1
        }
    }
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or higher from https://python.org" -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# Check if virtual environment already exists
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists. Removing old environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
try {
    python -m venv .venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host ""
Write-Host "Installing requirements..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "✓ Requirements installed" -ForegroundColor Green
} else {
    Write-Host "✗ requirements.txt not found!" -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# Check if Ollama is accessible
Write-Host ""
Write-Host "Checking Ollama connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Ollama is running" -ForegroundColor Green
        
        # Check for available models
        $models = ($response.Content | ConvertFrom-Json).models
        if ($models.Count -gt 0) {
            Write-Host "✓ Found $($models.Count) model(s) available" -ForegroundColor Green
        } else {
            Write-Host "! No models found. Run 'ollama pull llama3.2' to download a model" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "! Ollama not found or not running" -ForegroundColor Yellow
    Write-Host "Please ensure Ollama is installed and running (http://localhost:11434)" -ForegroundColor Yellow
    Write-Host "Download from: https://ollama.ai" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application, use:" -ForegroundColor Cyan
Write-Host "  .\run-windows.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or create a shortcut to run-windows.ps1 for easy access" -ForegroundColor Cyan
Write-Host ""
Read-Host -Prompt "Press Enter to exit"