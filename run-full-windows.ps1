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
$ollamaRunning = $false
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host '[OK] Ollama is already running' -ForegroundColor Green
    $ollamaRunning = $true
} catch {
    Write-Host 'Ollama is not running. Attempting to start...' -ForegroundColor Yellow
    
    # Try to start Ollama
    try {
        # Check if Ollama is installed
        $ollamaPath = Get-Command ollama -ErrorAction Stop
        
        # Start Ollama serve in background
        Write-Host 'Starting Ollama service...' -ForegroundColor Yellow
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        
        # Wait a moment for Ollama to start
        Start-Sleep -Seconds 3
        
        # Check if it started successfully
        try {
            $response = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            Write-Host '[OK] Ollama started successfully' -ForegroundColor Green
            $ollamaRunning = $true
        } catch {
            Write-Host '[ERROR] Failed to start Ollama' -ForegroundColor Red
            Write-Host 'Please start Ollama manually or check installation' -ForegroundColor Yellow
            Read-Host -Prompt 'Press Enter to exit'
            exit 1
        }
    } catch {
        Write-Host '[ERROR] Ollama not found. Please install Ollama first.' -ForegroundColor Red
        Write-Host 'Download from: https://ollama.ai' -ForegroundColor Cyan
        Read-Host -Prompt 'Press Enter to exit'
        exit 1
    }
}

# Check for available models if Ollama is running
if ($ollamaRunning) {
    Write-Host ''
    Write-Host 'Checking available models...' -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        $models = ($response.Content | ConvertFrom-Json).models
        
        if ($models -and $models.Count -gt 0) {
            Write-Host "[OK] Found $($models.Count) model(s) available:" -ForegroundColor Green
            foreach ($model in $models) {
                Write-Host "  - $($model.name)" -ForegroundColor Cyan
            }
        } else {
            Write-Host 'No models found. Pulling recommended models...' -ForegroundColor Yellow
            Write-Host 'This may take a few minutes on first run...' -ForegroundColor Yellow
            
            # Pull the recommended models
            $modelsToInstall = @('deepseek-r1:8b', 'gemma3:12b')
            
            foreach ($model in $modelsToInstall) {
                Write-Host ''
                Write-Host "Pulling $model..." -ForegroundColor Yellow
                try {
                    & ollama pull $model
                    Write-Host "[OK] Successfully pulled $model" -ForegroundColor Green
                } catch {
                    Write-Host "[WARNING] Failed to pull $model" -ForegroundColor Yellow
                    Write-Host "You can manually pull it later with: ollama pull $model" -ForegroundColor Cyan
                }
            }
            
            Write-Host ''
            Write-Host 'Model downloads complete!' -ForegroundColor Green
        }
    } catch {
        Write-Host '[WARNING] Could not check models' -ForegroundColor Yellow
    }
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