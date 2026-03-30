param(
    [switch]$test
)

Write-Host "========================================="
Write-Host " Wildlife Tagging Pipeline"
Write-Host "========================================="

# Prompt for root folder
$root = Read-Host "Enter the root folder containing photos"

# Expand relative paths
$root = Resolve-Path $root

# Validate
if (-not (Test-Path $root)) {
    throw "Root folder does not exist: $root"
}

Write-Host "Using root folder:"
Write-Host "  $root"

if ($test) {
    Write-Host "TEST MODE ENABLED — pipeline will run in safe mode"
}

Write-Host "-----------------------------------------"
Write-Host " Starting pipeline..."
Write-Host "-----------------------------------------"

# Stage 1 — Generate previews
Write-Host "[1/4] Generating previews..."
.\generate-previews.ps1 -root $root -test:$test

<#
# Stage 2 — Classification
Write-Host "[2/4] Running classification..."
.\classify.ps1 -root $root -test:$test

# Stage 3 — Metadata tagging
Write-Host "[3/4] Tagging metadata..."
.\tag-metadata.ps1 -root $root -test:$test

# Stage 4 — Export
Write-Host "[4/4] Exporting results..."
.\export.ps1 -root $root -test:$test
#>

Write-Host "-----------------------------------------"
Write-Host " Pipeline complete (preview stage only)."
Write-Host "-----------------------------------------"
