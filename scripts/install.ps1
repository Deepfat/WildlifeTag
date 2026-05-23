# =========================================
#  Wildlife Tagging Pipeline Installer
# =========================================

Write-Host "========================================="
Write-Host " Wildlife Tagging Pipeline Installer"
Write-Host "========================================="

# -----------------------------
# Load settings.json
# -----------------------------
$settingsPath = Join-Path $PSScriptRoot "settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Error "settings.json not found at $settingsPath"
    exit 1
}

$settings = Get-Content $settingsPath | ConvertFrom-Json
$exiftoolPath = $settings.exiftool_path

if (-not $exiftoolPath) {
    Write-Error "exiftool_path missing in settings.json"
    exit 1
}

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

python -m pip --version 2>$null

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
# 5. Check ExifTool using settings.json
# -----------------------------
Write-Host "`nChecking ExifTool..."

if (-not (Test-Path $exiftoolPath)) {
    Write-Host "ExifTool not found at $exiftoolPath"
    Write-Host "Downloading ExifTool..."

    $zipUrl = "https://exiftool.org/exiftool-12.76.zip"
    $zipFile = Join-Path $env:TEMP "exiftool.zip"
    $extractDir = Split-Path $exiftoolPath -Parent

    Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to download ExifTool."
        exit 1
    }

    Expand-Archive -Path $zipFile -DestinationPath $extractDir -Force

    $downloaded = Get-ChildItem -Path $extractDir -Filter "exiftool*.exe" | Select-Object -First 1

    if (-not $downloaded) {
        Write-Error "Downloaded ExifTool archive did not contain an executable."
        exit 1
    }

    Rename-Item -Path $downloaded.FullName -NewName (Split-Path $exiftoolPath -Leaf) -Force

    if (-not (Test-Path $exiftoolPath)) {
        Write-Error "Failed to install ExifTool to $exiftoolPath"
        exit 1
    }

    Write-Host "ExifTool installed to $exiftoolPath"
}
else {
    Write-Host "ExifTool OK at $exiftoolPath"
}

# -----------------------------
# 6. Validate GPU availability
# -----------------------------
Write-Host "`nChecking GPU availability..."

python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

Write-Host "GPU check complete"

# -----------------------------
# 7. Download iNat 2021 model + taxonomy (handled by model_downloader)
# -----------------------------
Write-Host "`nDownloading models..."

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$SettingsPath = Join-Path $ProjectRoot "config\settings.json"

python -m wildlife_classifier.model_downloader $SettingsPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to download models."
    exit 1
}

Write-Host "Models downloaded successfully"
Write-Host "`nDownloading iNat 2021 model + taxonomy..."

python -m wildlife_classifier.cli --download-inat2021

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to download iNat 2021 model or taxonomy."
    exit 1
}

Write-Host "iNat 2021 model + taxonomy downloaded"

# -----------------------------
# 8. Final message
# -----------------------------
Write-Host "`n========================================="
Write-Host " Installation complete."
Write-Host " You can now run:"
Write-Host "   ./wildlifetag.ps1"
Write-Host "========================================="
