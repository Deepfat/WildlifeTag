param(
    [switch]$test
)

Write-Host "========================================="
Write-Host " Wildlife Tagging Pipeline"
Write-Host "========================================="

# Load config
$configPath = Join-Path $PSScriptRoot "config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Resolve root
$root = $config.photoRoot

if ($test) {
    $root = Join-Path $PSScriptRoot "test"
    Write-Host "TEST MODE ENABLED — using test folder:"
    Write-Host "  $root"
} else {
    Write-Host "Using full photo root:"
    Write-Host "  $root"
}

Write-Host "-----------------------------------------"
Write-Host " Starting pipeline..."
Write-Host "-----------------------------------------"

# Stage 1 — Generate previews
Write-Host "[1/4] Generating previews..."
.\generate-previews.ps1 -root $root -test:$test

# Stage 2 — Classification
Write-Host "[2/4] Running classification..."
.\classify.ps1 -root $root -test:$test

# Stage 3 — Metadata tagging
Write-Host "[3/4] Tagging metadata..."
.\tag-metadata.ps1 -root $root -test:$test

# Stage 4 — Export
Write-Host "[4/4] Exporting results..."
.\export.ps1 -root $root -test:$test

Write-Host "-----------------------------------------"
Write-Host " Pipeline complete."
Write-Host "-----------------------------------------"
