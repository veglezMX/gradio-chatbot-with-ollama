@echo off
setlocal enabledelayedexpansion

REM Get the script's directory and change to it
cd /d "%~dp0"

echo === Starting Ollama Chat ===
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo X Virtual environment not found!
    echo Please run setup-windows.bat first
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo X main.py not found!
    echo Please ensure you're in the correct directory
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if Ollama is running
echo Checking Ollama status...
curl -s -m 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ! Warning: Ollama appears to be offline
    echo The app will start but won't work without Ollama running
    echo.
) else (
    echo + Ollama is running
)

REM Run the application
echo.
echo Starting application...
echo Opening browser at http://localhost:7860
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Application exited with error code: %errorlevel%
    pause
)