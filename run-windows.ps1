$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host '=== Starting Ollama Chat ===' -ForegroundColor Cyan
Write-Host ''

if (-not (Test-Path '.venv')) {
    Write-Host 'Virtual environment not found!' -ForegroundColor Red
    Write-Host 'Please run setup-windows.ps1 first' -ForegroundColor Yellow
    Read-Host -Prompt 'Press Enter to exit'
    exit 1
}

if (-not (Test-Path 'main.py')) {
    Write-Host 'main.py not found!' -ForegroundColor Red
    Write-Host 'Please ensure you''re in the correct directory' -ForegroundColor Yellow
    Read-Host -Prompt 'Press Enter to exit'
    exit 1
}

Write-Host 'Activating virtual environment...' -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host 'Checking Ollama status...' -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host '[OK] Ollama is running' -ForegroundColor Green
} catch {
    Write-Host '! Warning: Ollama appears to be offline' -ForegroundColor Yellow
    Write-Host 'The app will start but won''t work without Ollama running' -ForegroundColor Yellow
    Write-Host ''
}

# Run the application
Write-Host ''
Write-Host 'Starting application...' -ForegroundColor Green
Write-Host 'Opening browser at http://localhost:7860' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''

python main.py

# Keep window open if there was an error
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host "Application exited with error code: $LASTEXITCODE" -ForegroundColor Red
    Read-Host -Prompt 'Press Enter to exit'
}