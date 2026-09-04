$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendPath = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path -LiteralPath (Join-Path $FrontendPath "node_modules"))) {
    throw "Frontend dependencies not found. Run scripts\setup.ps1 first."
}

Push-Location $FrontendPath
try {
    npm.cmd run dev -- --hostname 0.0.0.0 --port 3000
    if ($LASTEXITCODE -ne 0) { throw "Frontend process failed (exit code $LASTEXITCODE)." }
}
finally {
    Pop-Location
}
