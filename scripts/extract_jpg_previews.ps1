param(
    [string]$root,
    [switch]$test
)

Write-Host "-----------------------------------------"
Write-Host " PREVIEW GENERATION"
Write-Host "-----------------------------------------"
Write-Host "Root folder: $root"

if ($test) {
    Write-Host "TEST MODE — running on a limited dataset"
}

# Validate root exists
if (-not (Test-Path $root)) {
    throw "Root folder does not exist: $root"
}

# ExifTool must be available in PATH
$exiftool = "exiftool"

# Define preview output folder inside the chosen root
$previewRoot = Join-Path $root "_previews"

# Create preview folder if needed
if (-not (Test-Path $previewRoot)) {
    Write-Host "Creating preview folder: $previewRoot"
    New-Item -ItemType Directory -Path $previewRoot | Out-Null
}

# Collect image files
$files = Get-ChildItem -Path $root -Recurse -File -Include *.jpg, *.jpeg, *.cr3, *.cr2

Write-Host "Found $($files.Count) files to process"

foreach ($file in $files) {

    # Compute relative path
    $relative = $file.FullName.Substring($root.Length).TrimStart('\')

    # Compute preview output path
    $previewPath = Join-Path $previewRoot ($relative + ".jpg")
    $previewDir  = Split-Path $previewPath -Parent

    # Ensure preview directory exists
    if (-not (Test-Path $previewDir)) {
        New-Item -ItemType Directory -Path $previewDir | Out-Null
    }

    # Skip if preview already exists
    if (Test-Path $previewPath) {
        continue
    }

    Write-Host "Generating preview for: $relative"

    # Extract preview bytes from ExifTool
    $previewBytes = & $exiftool -b -PreviewImage "$($file.FullName)"

    # If ExifTool produced nothing, skip
    if (-not $previewBytes -or $previewBytes.Length -eq 0) {
        Write-Host "No embedded preview found — skipping"
        continue
    }

    # Write preview file safely
    Set-Content -Encoding Byte -Path "$previewPath" -Value $previewBytes
}

Write-Host "Preview generation complete."
Write-Host "-----------------------------------------"
