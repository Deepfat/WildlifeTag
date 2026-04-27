# =========================================
#  Wildlife Tagging Pipeline Installer
# =========================================

Write-Host "========================================="
Write-Host " Wildlife Tagging Pipeline Installer"
Write-Host "========================================="

# -----------------------------
# 1. Check Python 3.11
# -----------------------------
Write-Host "`nChecking Python 3.11..."

$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
    Write-Error "Python not found. Install Python 3.11 from https://www.python.org/downloads/release/python-3110/"
    exit 1
}

$version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"

if ($version -ne "3.11") {
    Write-Error "Python version $version detected. Python 3.11 is required."
    exit 1
}

Write-Host "Python 3.11 OK"

# -----------------------------
# 2. Check pip
# -----------------------------
Write-Host "`nChecking pip..."

$pip = python -m pip --version 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Error "pip not found. Ensure Python was installed with 'Add to PATH' enabled."
    exit 1
}

Write-Host "pip OK"

# -----------------------------
# 3. Install Python dependencies
# -----------------------------
Write-Host "`nInstalling Python dependencies..."

$reqPath = Join-Path $PSScriptRoot "requirements.txt"

if (-not (Test-Path $reqPath)) {
    Write-Error "requirements.txt not found at $reqPath"
    exit 1
}

python -m pip install -r $reqPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Python dependencies."
    exit 1
}

Write-Host "Python dependencies installed"

# -----------------------------
# 4. Check ImageMagick
# -----------------------------
Write-Host "`nChecking ImageMagick..."

$magick = Get-Command magick -ErrorAction SilentlyContinue

if (-not $magick) {
    Write-Error "ImageMagick not found. Install from https://imagemagick.org/script/download.php#windows"
    exit 1
}

Write-Host "ImageMagick OK"

# -----------------------------
# 5. Check ExifTool
# -----------------------------
Write-Host "`nChecking ExifTool..."

$exif = Get-Command exiftool -ErrorAction SilentlyContinue

if (-not $exif) {
    Write-Error "ExifTool not found. Install from https://exiftool.org/"
    exit 1
}

Write-Host "ExifTool OK"

# -----------------------------
# 6. Validate GPU availability
# -----------------------------
Write-Host "`nChecking GPU availability..."

python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

Write-Host "GPU check complete"

# -----------------------------
# 7. Download iNat 2021 model + metadata
# -----------------------------
Write-Host "`nDownloading iNat 2021 model + metadata..."

python -m wildlife_classifier.cli --download-inat2021

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to download iNat 2021 model or metadata."
    exit 1
}

Write-Host "iNat 2021 model + metadata downloaded"

# -----------------------------
# 8. Build iNat 2021 taxonomy
# -----------------------------
Write-Host "`nBuilding iNat 2021 taxonomy..."

python -m wildlife_classifier.cli --build-inat2021-taxonomy

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build iNat 2021 taxonomy."
    exit 1
}

Write-Host "iNat 2021 taxonomy built"

# -----------------------------
# 9. Final message
# -----------------------------
Write-Host "`n========================================="
Write-Host " Installation complete."
Write-Host " You can now run:"
Write-Host "   ./wildlifetag.ps1"
Write-Host "========================================="
