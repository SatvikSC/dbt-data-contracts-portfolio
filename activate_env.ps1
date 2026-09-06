# Run this before working on Project 2:
#   . .\activate_env.ps1
#
# Unified venv at C:\venvs\portfolio covers all portfolio projects.
# NOTE: venv at short path to avoid Windows 260-char path limit (metricflow deep subpaths).

$venvPath = "C:\venvs\portfolio"

if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    . "$venvPath\Scripts\Activate.ps1"
    Write-Host "venv activated: $venvPath" -ForegroundColor Green
    Write-Host "dbt version: $(dbt --version 2>&1 | Select-String 'installed')" -ForegroundColor Cyan
} else {
    Write-Host "venv not found at $venvPath. Create it:" -ForegroundColor Red
    Write-Host "  python -m venv C:\venvs\portfolio" -ForegroundColor Yellow
    Write-Host "  C:\venvs\portfolio\Scripts\pip install pip-system-certs" -ForegroundColor Yellow
    Write-Host "  C:\venvs\portfolio\Scripts\pip install -r Projects\01_Lakehouse_Platform\requirements_unified.txt" -ForegroundColor Yellow
}
