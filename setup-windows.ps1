# Ollama Chat Setup Script for Windows
# This script creates a virtual environment and installs dependencies

Write-Host '=== Ollama Chat Setup for Windows ===' -ForegroundColor Cyan
Write-Host ''

# Check if Python is installed
try {
    $pythonVersionOutput = python --version 2>&1
    if ($pythonVersionOutput -match "Python (\d+)\.(\d+)") {
        $majorVersion = [int]$matches[1]
        $minorVersion = [int]$matches[2]
        if ($majorVersion -eq 3 -and $minorVersion -ge 8) {
            Write-Host "[OK] Python $($matches[0]) found" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Python 3.8 or higher required. Found: $pythonVersionOutput" -ForegroundColor Red
            Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
            Read-Host -Prompt 'Press Enter to exit'
            exit 1
        }
    } else {
        Write-Host "[ERROR] Could not determine Python version. Output: $pythonVersionOutput" -ForegroundColor Red
        Write-Host "Please ensure Python 3.8+ is installed and in PATH." -ForegroundColor Yellow
        Read-Host -Prompt 'Press Enter to exit'
        exit 1
    }
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.8 or higher from https://python.org" -ForegroundColor Red
    Read-Host -Prompt 'Press Enter to exit'
    exit 1
}

# Check if virtual environment already exists
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists. Removing old environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
}

# Create virtual environment
Write-Host ''
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
try {
    python -m venv .venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Read-Host -Prompt 'Press Enter to exit'
    exit 1
}

# Activate virtual environment
Write-Host ''
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    & .\.venv\Scripts\Activate.ps1
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment." -ForegroundColor Red
    Write-Host "Ensure .\.venv\Scripts\Activate.ps1 exists and is executable." -ForegroundColor Yellow
    Write-Host $_.Exception.Message
    Read-Host -Prompt 'Press Enter to exit'
    exit 1
}


# Upgrade pip
Write-Host ''
Write-Host "Upgrading pip..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    Write-Host "[OK] pip upgraded" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to upgrade pip" -ForegroundColor Red
    Write-Host $_.Exception.Message
}


# Install requirements
Write-Host ''
Write-Host 'Installing requirements...' -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    try {
        pip install -r requirements.txt
        Write-Host '✓ Requirements installed' -ForegroundColor Green
    } catch {
        Write-Host '✗ Failed to install requirements from requirements.txt' -ForegroundColor Red
        Write-Host $_.Exception.Message
        Read-Host -Prompt 'Press Enter to exit'
        exit 1
    }
} else {
    Write-Host '✗ requirements.txt not found!' -ForegroundColor Red
    Read-Host -Prompt 'Press Enter to exit'
    exit 1
}

Write-Host ''
Write-Host "Checking Ollama connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    
    Write-Host '✓ Ollama is running and reachable' -ForegroundColor Green
    
    $models = ($response.Content | ConvertFrom-Json).models
    if ($models -and $models.Count -gt 0) {
        Write-Host "[OK] Found $($models.Count) model(s) available" -ForegroundColor Green
    } else {
        Write-Host '! No models found. Run `ollama pull llama3` (or another model) to download a model.' -ForegroundColor Yellow
    }
    
} catch {
    Write-Host '! Ollama not found or not running (or timed out after 5 seconds)' -ForegroundColor Yellow
    Write-Host 'Please ensure Ollama is installed and running (check http://localhost:11434 in your browser)' -ForegroundColor Yellow
    Write-Host 'Download from: https://ollama.ai' -ForegroundColor Cyan
}

Write-Host ''
Write-Host '=== Setup Complete! ===' -ForegroundColor Green
Write-Host ''
Write-Host 'To run the application, use:' -ForegroundColor Cyan
Write-Host '  .\run-windows.ps1' -ForegroundColor White
Write-Host ''
Write-Host 'Or create a shortcut to run-windows.ps1 for easy access' -ForegroundColor Cyan
Write-Host ''
Read-Host -Prompt 'Press Enter to exit'
