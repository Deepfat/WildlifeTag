# PhotoTag Pipeline Invoker
# Usage: .\run_pipeline.ps1 --jpeg <path> --raw <path> [--verbose]
#   or: .\run_pipeline.ps1 --manifest <path> [--verbose]

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

# Get script directory and project root
$ScriptDir = $PSScriptRoot
$ProjectRoot = $ScriptDir

# Activate virtual environment if it exists
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    Write-Host "Activating virtual environment..."
    & $VenvActivate
} else {
    Write-Host "No .venv found — using system Python"
}

# Run the CLI module
python -m wildlife_classifier.cli @Arguments
$ExitCode = $LASTEXITCODE

exit $ExitCode