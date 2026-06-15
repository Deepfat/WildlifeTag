Param(
    [Parameter(Mandatory = $false)]
    [string]$Root,
    [switch]$Test
)

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ScriptsRoot = $PSScriptRoot

function Get-SettingsPath {
    if ($global:settingsPath) {
        return $global:settingsPath
    }
    return Join-Path $ProjectRoot "config\settings.json"
}

function Load-Settings {
    $settingsPath = Get-SettingsPath
    if (-not (Test-Path $settingsPath)) {
        throw "settings.json not found at $settingsPath"
    }
    $raw = [System.IO.File]::ReadAllText($settingsPath)
    $settings = $raw | ConvertFrom-Json
    return [PSCustomObject]@{ Data = $settings }
}

function Resolve-Root {
    param([string]$root)

    if (-not $root) {
        throw "Root parameter is required."
    }

    $resolved = Resolve-Path $root -ErrorAction Stop
    if ($resolved -is [System.Management.Automation.PathInfo]) {
        $resolved = $resolved.Path
    }

    if (-not (Test-Path $resolved)) {
        throw "Root folder does not exist: $resolved"
    }

    return $resolved
}

function Build-Params {
    param(
        [Parameter(Mandatory = $true)] [string]$jpg,
        [Parameter(Mandatory = $true)] [string]$raw,
        [Parameter(Mandatory = $true)] [string]$model,
        [Parameter(Mandatory = $true)] [double]$conf,
        [Parameter(Mandatory = $true)] [bool]$verbose,
        [Parameter(Mandatory = $true)] [bool]$test
    )

    return [PSCustomObject]@{
        jpeg    = $jpg
        raw     = $raw
        model   = $model
        conf    = $conf
        verbose = $verboseFlag
        test    = $testFlag
    } | ConvertTo-Json
}

function Run-PreviewStage {
    param(
        [Parameter(Mandatory = $true)] [string]$Root,
        [switch]$test
    )

    Write-Host "Stage 1: Generating previews..."
    $previewScript = Join-Path $ScriptsRoot "extract_jpg_previews.ps1"

    if (-not (Test-Path $previewScript)) {
        throw "extract_jpg_previews.ps1 not found at $previewScript"
    }

    & $previewScript -Root $Root -Test:$test
    if (-not $?) {
        throw "Preview extraction failed"
    }
}

function Run-ClassifierStage {
    param(
        [Parameter(Mandatory = $true)] [string]$Root,
        [Parameter(Mandatory = $true)] [string]$Model,
        [Parameter(Mandatory = $true)] [double]$Conf,
        [Parameter(Mandatory = $true)] [bool]$verbose,
        [switch]$test
    )

    $files = Get-ChildItem -Path $Root -Recurse -File -Filter *.cr3

    foreach ($file in $files) {
        $jpgPath = Join-Path $file.DirectoryName ($file.BaseName + ".jpg")
        if (-not (Test-Path $jpgPath)) {
            continue
        }

        & python -m wildlife_classifier.pipeline $Root
        if (-not $?) {
            throw "Python pipeline failed for $($file.FullName)"
        }
    }
}

function Run-PythonPipeline {
    param([string]$Root)

    Write-Host "Stage 2: Running Python pipeline..."

    $pythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = "python"
    }

    & $pythonExe -m wildlife_classifier.pipeline $Root
    if (-not $?) {
        throw "Python pipeline failed"
    }
}


if (-not $MyInvocation.ScriptName) {
    Write-Host "========================================="
    Write-Host " Wildlife Tagging Pipeline"
    Write-Host "========================================="

    if (-not $Root) {
        $Root = Read-Host "Enter the root folder containing photos"
    }

    $Root = Resolve-Root $Root

    Write-Host "Using root folder:"
    Write-Host "  $Root"

    Run-PreviewStage -Root $Root -Test:$Test
    Run-PythonPipeline -Root $Root
}
