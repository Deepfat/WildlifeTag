param(
    [Parameter(Mandatory = $true)]
    [string]$root,

    [switch]$test
)

Write-Host "-----------------------------------------" -ForegroundColor Cyan
Write-Host " PREVIEW GENERATION using ImageMagick" -ForegroundColor Cyan
Write-Host "-----------------------------------------" -ForegroundColor Cyan
Write-Host "Root folder: $root"

# -----------------------------------------
# Logging
# -----------------------------------------
$logDir = Join-Path $root "output"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$logPath = Join-Path $logDir "preview_$timestamp.csv"

"file,relative_path,status,message" |
    Out-File -FilePath $logPath -Encoding UTF8

# -----------------------------------------
# Process CR3 files
# -----------------------------------------
$files = Get-ChildItem -Path $root -Recurse -Include *.cr3

foreach ($file in $files) {

    # Relative path for logging
    $relative = $file.FullName.Replace((Resolve-Path $root).Path, "").TrimStart("\","/")

    # Preview folder beside source
    $sourceDir = Split-Path $file.FullName -Parent
    $previewDir = Join-Path $sourceDir "_preview"

    if (-not (Test-Path $previewDir)) {
        New-Item -ItemType Directory -Path $previewDir | Out-Null
    }

    # Clean filename: strip .cr3 → .jpg
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $previewPath = Join-Path $previewDir ($baseName + ".jpg")

    $status = "skipped"
    $msg = ""

    # -----------------------------------------
    # Generate preview (ImageMagick)
    # -----------------------------------------
try {
    if (-not $test) {
        magick $file.FullName -resize 2048x $previewPath
        $status = "created"
    }
    else {
        $status = "skipped (test mode)"
    }
}
catch {
    $status = "failed"
    $msg = $_.Exception.Message
}

    # -----------------------------------------
    # Log result
    # -----------------------------------------
    $line = "$($file.Name),$relative,$status,$msg"
    Add-Content -Path $logPath -Value $line
}

Write-Host "Preview generation complete."
