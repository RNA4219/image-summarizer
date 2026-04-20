# Start Backend Script

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"
$venvDir = Join-Path $backendDir ".venv"
$venvActivatePath = Join-Path $venvDir "Scripts\\Activate.ps1"
$venvPythonPath = Join-Path $venvDir "Scripts\\python.exe"
$venvPipPath = Join-Path $venvDir "Scripts\\pip.exe"
$venvUvicornPath = Join-Path $venvDir "Scripts\\uvicorn.exe"

Write-Host "Starting backend..." -ForegroundColor Green
Set-Location $backendDir

# Load .env file from project root
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    Write-Host "Loading .env file..." -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

if (-not $env:OPENAI_API_KEY) {
    Write-Host "Error: OPENAI_API_KEY is not set in .env file" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "API Key loaded" -ForegroundColor Green

if (-not (Test-Path $venvPythonPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan

    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $venvDir
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venvDir
    } else {
        Write-Host "Error: Python launcher not found. Install Python 3.11+ and retry." -ForegroundColor Red
        Read-Host "Press Enter to exit..."
        exit 1
    }
}

if (Test-Path $venvActivatePath) {
    . $venvActivatePath
    Write-Host "Virtual environment activated (.venv)" -ForegroundColor Cyan
}

& $venvPipPath install -r requirements.txt --quiet

& $venvUvicornPath app.main:app --reload --port 8000
