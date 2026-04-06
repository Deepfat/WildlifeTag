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
    throw "settings.json not found at $settingsPath"
}

$settings = Get-Content $settingsPath | ConvertFrom-Json

$model      = $settings.model_path
$confidence = $settings.confidence
$verbose    = $settings.verbose

Write-Host "Model:       $model"
Write-Host "Confidence:  $confidence"
Write-Host "Verbose:     $verbose"


# Prompt for root folder
$root = Read-Host "Enter the root folder containing photos"
$root = Resolve-Path $root

if (-not (Test-Path $root)) {
    throw "Root folder does not exist: $root"
}

Write-Host "Using root folder:"
Write-Host "  $root"


# Persist the photo path
$settings.photo_root = $root
$settings | ConvertTo-Json -Depth 5 | Set-Content $settingsPath


# -----------------------------
# Stage 1: Generate JPG previews
# -----------------------------
Write-Host "Stage 1: Generating previews..."

$previewScript = Join-Path $PSScriptRoot "extract_jpg_previews.ps1"

& $previewScript -root $root -test:$test


# -----------------------------
# Stage 2: tag each file in turn 
# -----------------------------
Write-Host "Stage 2: Running classifier (single-pass)..."

# Find all CR3 files
$rawFiles = Get-ChildItem -Path $root -Filter *.CR3 -Recurse

foreach ($raw in $rawFiles) {

    $jpg = Join-Path $raw.DirectoryName ($raw.BaseName + ".JPG")

    if (-not (Test-Path $jpg)) {
        Write-Warning "Preview missing for $($raw.FullName) — skipping"
        continue
    }

    # Build JSON params for Python
    $params = @{
        jpeg = $jpg
        raw  = $raw.FullName
        model = $model
        conf  = $confidence
        verbose = $verbose
        test = $test.IsPresent
    } | ConvertTo-Json -Compress

    Write-Host "Processing $($raw.Name)..."

    python run_classifier.py --params $params
}


Write-Host "========================================="
Write-Host " Pipeline complete"
Write-Host "========================================="
