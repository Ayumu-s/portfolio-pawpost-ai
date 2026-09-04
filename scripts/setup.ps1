$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$FrontendPath = Join-Path $ProjectRoot "frontend"
$VenvPath = Join-Path $BackendPath ".venv"

Write-Host "[1/4] Preparing the Python virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $VenvPath)) {
    python -m venv $VenvPath
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
Write-Host "[2/4] Installing backend dependencies..." -ForegroundColor Cyan
& $PythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip (exit code $LASTEXITCODE)." }
& $PythonExe -m pip install -r (Join-Path $BackendPath "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install backend dependencies (exit code $LASTEXITCODE)." }

$BackendEnv = Join-Path $BackendPath ".env"
if (-not (Test-Path -LiteralPath $BackendEnv)) {
    Copy-Item -LiteralPath (Join-Path $BackendPath ".env.example") -Destination $BackendEnv
    Write-Host "Created backend/.env. The public copy runs in Mock mode and needs no API key." -ForegroundColor Yellow
}

Write-Host "[3/4] Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location $FrontendPath
try {
    npm.cmd install
    if ($LASTEXITCODE -ne 0) { throw "Failed to install frontend dependencies (exit code $LASTEXITCODE)." }
}
finally {
    Pop-Location
}

$FrontendEnv = Join-Path $FrontendPath ".env.local"
if (-not (Test-Path -LiteralPath $FrontendEnv)) {
    Copy-Item -LiteralPath (Join-Path $FrontendPath ".env.local.example") -Destination $FrontendEnv
}

Write-Host "[4/4] Setup complete." -ForegroundColor Green
Write-Host "Next, run scripts\run-backend.ps1 and scripts\run-frontend.ps1 in separate PowerShell windows."
