param(
    [string]$root,
    [switch]$test
)

Write-Host "-----------------------------------------"
Write-Host " PREVIEW GENERATION"
Write-Host "-----------------------------------------"
Write-Host "Root folder: $root"

if ($test) {
    Write-Host "TEST MODE — limiting preview generation to test dataset"
}

# Validate root exists
if (-not (Test-Path $root)) {
    throw "Root folder does not exist: $root"
}

# ExifTool path is expected to be in PATH or set by the orchestrator's environment
$exiftool = "exiftool"

# Define preview output folder (inside root)
$previewRoot = Join-Path $root "_previews"

# Create preview folder if needed
if (-not (Test-Path $previewRoot)) {
    Write-Host "Creating preview folder: $previewRoot"
    New-Item -ItemType Directory -Path $previewRoot | Out-Null
}

# Get all image files (RAW + JPEG)
$files = Get-ChildItem -Path $root -Recurse -File -Include *.jpg, *.jpeg, *.cr3, *.cr2

Write-Host "Found $($files.Count) files to process"

foreach ($file in $files) {

    # Determine preview output path
    $relative = $file.FullName.Substring($root.Length).TrimStart('\')
    $previewPath = Join-Path $previewRoot ($relative + ".jpg")

    # Ensure preview subfolder exists
    $previewDir = Split-Path $previewPath -Parent
    if (-not (Test-Path $previewDir)) {
        New-Item -ItemType Directory -Path $previewDir | Out-Null
    }

    # Skip if preview already exists
    if (Test-Path $previewPath) {
        continue
    }

    Write-Host "Generating preview for: $relative"

    # Generate preview using ExifTool
    # -b = binary output
    # -PreviewImage = extract embedded preview
    # Redirect to file
    & $exiftool -b -PreviewImage $file.FullName > $previewPath

    # If no preview was extracted, ExifTool outputs nothing
    if ((Get-Item $previewPath).Length -eq 0) {
        Write-Host "No embedded preview found — deleting empty file"
        Remove-Item $previewPath
    }
}

Write-Host "Preview generation complete."
Write-Host "-----------------------------------------"
