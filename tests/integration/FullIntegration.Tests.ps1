# FullIntegration.Tests.ps1 — v29

Describe "Full pipeline integration" {

    BeforeAll {
        $script:ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
        $script:WildlifeTag = Join-Path $ProjectRoot "scripts\wildlife_tag.ps1"
        $script:SampleRoot  = Join-Path $ProjectRoot "test_images"

        # Stable workspace inside repo
        $script:WorkRoot = Join-Path $ProjectRoot "_test_workspace"

        if (Test-Path $WorkRoot) {
            Remove-Item -Path $WorkRoot -Recurse -Force -ErrorAction SilentlyContinue
        }

        New-Item -ItemType Directory -Path $WorkRoot | Out-Null

        # Copy sample images into workspace
        Copy-Item -Path (Join-Path $SampleRoot "*") -Destination $WorkRoot -Recurse -Force
    }

    It "runs the full pipeline and produces XMP sidecars" {

        # Allow pipeline to continue even if classifier recovery fails
        & $WildlifeTag -Root $WorkRoot -ErrorAction Continue

        # Assert XMPs exist next to RAWs
        $rawFiles = Get-ChildItem -Path $WorkRoot -Recurse -Include *.cr3, *.cr2, *.nef, *.arw, *.orf, *.rw2

        foreach ($raw in $rawFiles) {
            $xmp = [IO.Path]::ChangeExtension($raw.FullName, ".xmp")
            Test-Path $xmp | Should -BeTrue
        }
    }
}
