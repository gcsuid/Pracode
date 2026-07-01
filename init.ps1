Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

Write-Host "==> Working directory: $(Get-Location)"
Write-Host "==> Syncing dependencies"
python -m pip install -r requirements.txt

Write-Host "==> Running baseline verification"
python -m pytest -q

$startCommand = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
Write-Host "==> Startup command"
Write-Host "    $startCommand"

if ($env:RUN_START_COMMAND -eq "1") {
    Write-Host "==> Starting the app"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
}
else {
    Write-Host "Set RUN_START_COMMAND=1 if you want init.ps1 to launch the app directly."
}
