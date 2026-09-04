$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $BackendPath ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python virtual environment not found. Run scripts\setup.ps1 first."
}

Push-Location $BackendPath
try {
    & $PythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    if ($LASTEXITCODE -ne 0) { throw "Backend process failed (exit code $LASTEXITCODE)." }
}
finally {
    Pop-Location
}
