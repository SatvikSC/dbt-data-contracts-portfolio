# Run this before working on the project:
#   . .\activate_env.ps1
#
# NOTE: venv lives at C:\venvs\proj02_dbt (short path) to avoid Windows 260-char path limit.
# The deep OneDrive path caused pip to fail installing metricflow's long subpaths.

$venvPath = "C:\venvs\proj02_dbt"

if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    . "$venvPath\Scripts\Activate.ps1"
    Write-Host "venv activated: $venvPath" -ForegroundColor Green
    Write-Host "dbt version: $(dbt --version 2>&1 | Select-String 'installed')" -ForegroundColor Cyan
} else {
    Write-Host "venv not found at $venvPath" -ForegroundColor Red
    Write-Host "Recreate it with:" -ForegroundColor Yellow
    Write-Host "  python -m venv C:\venvs\proj02_dbt" -ForegroundColor Yellow
    Write-Host "  C:\venvs\proj02_dbt\Scripts\pip install dbt-databricks==1.12.5" -ForegroundColor Yellow
}
