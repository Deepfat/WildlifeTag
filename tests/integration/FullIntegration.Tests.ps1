# FullIntegration.Tests.ps1 — v29
# REQUIREMENTS: ImageMagick (magick command) must be installed
# This test downloads large models (~150MB) from the internet and processes actual image files
# It may be skipped if ImageMagick is not available or if network/model issues occur

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

    It "runs the full pipeline and produces XMP sidecars" -Skip:(-not (Get-Command magick -ErrorAction SilentlyContinue)) {
        # Allow pipeline to continue even if classifier recovery fails
        # This is an integration test that requires internet access for models
        { & $WildlifeTag -Root $WorkRoot -ErrorAction Stop } | Should -Not -Throw

        # Assert XMPs exist next to RAWs
        $rawFiles = Get-ChildItem -Path $WorkRoot -Recurse -Include *.cr3, *.cr2, *.nef, *.arw, *.orf, *.rw2

        $xmpCount = 0
        foreach ($raw in $rawFiles) {
            $xmp = [IO.Path]::ChangeExtension($raw.FullName, ".xmp")
            if (Test-Path $xmp) {
                $xmpCount++
            }
        }
        
        # At least some XMPs should have been created
        $xmpCount | Should -BeGreaterThan 0 -Because "Pipeline should create XMP sidecar files"
    }
}
