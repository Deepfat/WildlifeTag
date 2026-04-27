param(
    [Parameter(Mandatory = $true)]
    [string]$Root,

    [switch]$Test
)

function Resolve-Root($root) {
    $resolved = Resolve-Path $root -ErrorAction Stop
    if (-not (Test-Path $resolved)) {
        throw "Root folder does not exist: $resolved"
    }
    return $resolved
}

function Initialize-Log($root) {
    $logDir = Join-Path $root "output"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir | Out-Null
    }

    $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $logPath = Join-Path $logDir "preview_$timestamp.csv"

    "file,relative_path,status,message" |
        Out-File -FilePath $logPath -Encoding UTF8

    return $logPath
}

function Get-PreviewPath($file) {
    $sourceDir = Split-Path $file.FullName -Parent
    $previewDir = Join-Path $sourceDir "_preview"

    if (-not (Test-Path $previewDir)) {
        New-Item -ItemType Directory -Path $previewDir | Out-Null
    }

    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    return Join-Path $previewDir ($baseName + ".jpg")
}

function New-Preview($file, $previewPath, $testMode) {
    if ($testMode) {
        return @{ status = "skipped (test mode)"; message = "" }
    }

    try {
        magick $file.FullName -resize 2048x $previewPath
        return @{ status = "created"; message = "" }
    }
    catch {
        return @{ status = "failed"; message = $_.Exception.Message }
    }
}

function Write-Log($logPath, $fileName, $relative, $status, $msg) {
    $line = "$fileName,$relative,$status,$msg"
    Add-Content -Path $logPath -Value $line
}

function Invoke-PreviewBuild($root, $logPath, $testMode) {
    $resolvedRoot = (Resolve-Path $root).Path
    $files = Get-ChildItem -Path $resolvedRoot -Recurse -File -Filter *.cr3

    foreach ($file in $files) {
        $relative = $file.FullName.Replace($resolvedRoot, "").TrimStart("\","/")
        $previewPath = Get-PreviewPath -file $file
        $result = New-Preview -file $file -previewPath $previewPath -testMode:$testMode

        Write-Log -logPath $logPath `
                  -fileName $file.Name `
                  -relative $relative `
                  -status $result.status `
                  -msg $result.message
    }
}

$resolvedRoot = Resolve-Root $Root
$logPath = Initialize-Log $resolvedRoot
Invoke-PreviewBuild -root $resolvedRoot -logPath $logPath -testMode:$Test
