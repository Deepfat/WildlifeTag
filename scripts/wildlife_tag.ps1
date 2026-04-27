param(
    [Parameter(Mandatory = $false)]
    [string]$Root,
    [switch]$Test
)

Write-Host "========================================="
Write-Host " Wildlife Tagging Pipeline"
Write-Host "========================================="

# Project + scripts roots
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ScriptsRoot = $PSScriptRoot

# Python executable (prefer venv, fall back to system python)
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

# Resolve root folder
if (-not $Root) {
    $Root = Read-Host "Enter the root folder containing photos"
}

$Root = Resolve-Path $Root

if (-not (Test-Path $Root)) {
    throw "Root folder does not exist: $Root"
}

Write-Host "Using root folder:"
Write-Host "  $Root"

# -----------------------------
# Stage 1: Generate JPG previews
# -----------------------------
function Run-PreviewStage {
    param([string]$Root)

    Write-Host "Stage 1: Generating previews..."
    $previewScript = Join-Path $ScriptsRoot "extract_jpg_previews.ps1"

    if (-not (Test-Path $previewScript)) {
        throw "extract_jpg_previews.ps1 not found at $previewScript"
    }

    & $previewScript -Root $Root -Test:$Test

    if ($LASTEXITCODE -ne 0) {
        throw "Preview extraction failed with exit code $LASTEXITCODE"
    }
}

# -----------------------------
# Stage 2: Python pipeline
# -----------------------------
function Run-PythonPipeline {
    param([string]$Root)

    Write-Host "Stage 2: Running Python pipeline..."

    # Correct Python module invocation - positional args
    $modelDir = Join-Path $ProjectRoot "models"

    & $PythonExe -m wildlife_classifier.pipeline $Root $modelDir

    if ($LASTEXITCODE -ne 0) {
        throw "Python pipeline failed with exit code $LASTEXITCODE"
    }
}

# -----------------------------
# Orchestration
# -----------------------------
Run-PreviewStage   -Root $Root
Run-PythonPipeline -Root $Root
