param(
    [string]$root,
    [string]$exiftool
)
# Load config
$configPath = Join-Path $PSScriptRoot "config.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Apply config defaults only if parameters were not passed
if (-not $root)     { $root     = $config.photoRoot }
if (-not $exiftool) { $exiftool = $config.exiftoolPath }

Write-Host "Extracting JPEG previews into jpg subfolders under $root"

# Find all CR3 files recursively
$cr3Files = Get-ChildItem -Path $root -Recurse -Filter *.CR3

foreach ($cr3 in $cr3Files) {

    $folder = $cr3.DirectoryName
    $jpgFolder = Join-Path $folder "jpg"

    # Create jpg folder if missing
    if (-not (Test-Path $jpgFolder)) {
        New-Item -ItemType Directory -Path $jpgFolder | Out-Null
    }

    # Build output path
    $jpgOut = Join-Path $jpgFolder ($cr3.BaseName + ".jpg")

    # Extract preview using your ExifTool
    & $exiftool -b -PreviewImage $cr3.FullName > $jpgOut
}

Write-Host "Preview extraction complete."
