@echo off
setlocal enabledelayedexpansion

echo === Ollama Chat Setup for Windows ===
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo + Python %PYTHON_VERSION% found

REM Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

REM Check if version is 3.8 or higher
if %MAJOR% LSS 3 (
    echo X Python 3.8 or higher required. Found: %PYTHON_VERSION%
    echo Please install Python from https://python.org
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 8 (
    echo X Python 3.8 or higher required. Found: %PYTHON_VERSION%
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment already exists
if exist ".venv" (
    echo Virtual environment already exists. Removing old environment...
    rmdir /s /q .venv
)

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo X Failed to create virtual environment
    pause
    exit /b 1
)
echo + Virtual environment created

REM Activate virtual environment
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo Installing requirements...
if not exist "requirements.txt" (
    echo X requirements.txt not found!
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo X Failed to install requirements
    pause
    exit /b 1
)
echo + Requirements installed

REM Check if Ollama is accessible
echo.
echo Checking Ollama connection...
curl -s -m 5 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ! Ollama not found or not running
    echo Please ensure Ollama is installed and running (http://localhost:11434)
    echo Download from: https://ollama.ai
) else (
    echo + Ollama is running
    
    REM Check for available models (basic check)
    curl -s -m 5 http://localhost:11434/api/tags > temp_models.json 2>nul
    if exist temp_models.json (
        findstr /C:"models" temp_models.json >nul
        if errorlevel 1 (
            echo ! No models found. Run 'ollama pull llama3.2' to download a model
        ) else (
            echo + Models available
        )
        del temp_models.json >nul 2>&1
    )
)

echo.
echo === Setup Complete! ===
echo.
echo To run the application, use:
echo   run-windows.bat
echo.
echo Or create a shortcut to run-windows.bat for easy access
echo.
pause