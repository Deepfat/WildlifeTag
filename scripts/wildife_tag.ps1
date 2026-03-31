param(
    [switch]$test
)

Write-Host "========================================="
Write-Host " Wildlife Tagging Pipeline"
Write-Host "========================================="

# -----------------------------
# Stage 0: Setup
# -----------------------------

# Load settings.json
$settingsPath = Join-Path $PSScriptRoot "..\config\settings.json"
if (-not (Test-Path $settingsPath)) {
    throw "settings.json not found."
}

$settings = Get-Content $settingsPath | ConvertFrom-Json

$model      = $settings.model_path
$confidence = $settings.confidence
$verbose    = $settings.verbose

Write-Host "Model: $model"
Write-Host "Confidence: $confidence"
Write-Host "Verbose: $verbose"

# Prompt for root folder
$root = Read-Host "Enter the root folder containing photos"
$root = Resolve-Path $root

if (-not (Test-Path $root)) {
    throw "Root folder does not exist: $root"
}

Write-Host "Using root folder:"
Write-Host "  $root"

# -----------------------------
# Stage 1: Generate JPG previews
# -----------------------------
Write-Host "Stage 1: Generating previews..."

$previewScript = Join-Path $PSScriptRoot "extract_jpg_previews.ps1"

# Pass the test flag straight through
& $previewScript -root $root -test:$test
