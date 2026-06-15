# FullIntegration.Tests.ps1 — v31
# REQUIREMENTS: ImageMagick (magick command) must be installed
# This test downloads large models (~150MB) and processes actual image files

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

        # Capture timestamp of the known existing XMP file
        $script:ExistingXmp = Get-ChildItem -Path $WorkRoot -Recurse -Include *.xmp | Select-Object -First 1
        if ($script:ExistingXmp) {
            $script:ExistingXmpTime = (Get-Item $script:ExistingXmp.FullName).LastWriteTimeUtc
        }
    }

    It "runs the full pipeline and produces XMP sidecars" -Skip:(-not (Get-Command magick -ErrorAction SilentlyContinue)) {

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

        $xmpCount | Should -BeGreaterThan 0 -Because "Pipeline should create XMP sidecar files"
    }

    It "updates the existing XMP file with new metadata" -Skip:(-not (Get-Command magick -ErrorAction SilentlyContinue)) {

        if ($script:ExistingXmp) {
            $updatedTime = (Get-Item $script:ExistingXmp.FullName).LastWriteTimeUtc
            $updatedTime | Should -BeGreaterThan $script:ExistingXmpTime -Because "Existing XMP should be updated"
        }
    }

    It "produces a taxonomy CSV with correct structure" -Skip:(-not (Get-Command magick -ErrorAction SilentlyContinue)) {

        # FIX 1 — CSV path now comes from settings.json and is under project root
        $csvPath = Join-Path $ProjectRoot "_taxonomy\taxonomy.csv"
        Test-Path $csvPath | Should -BeTrue -Because "Pipeline must produce taxonomy CSV"

        $lines = Get-Content $csvPath
        $lines.Count | Should -BeGreaterThan 1 -Because "CSV must contain header + rows"

        # FIX 2 — Updated header includes date_processed
        $header = $lines[0].Trim()
        $expectedHeader = "raw_path,date_processed,kingdom,phylum,class,order,family,genus,species,confidence"
        $header | Should -Be $expectedHeader -Because "CSV header must match expected taxonomy fields"

        # FIX 3 — Row count must match number of RAW files
        $rawFiles = Get-ChildItem -Path $WorkRoot -Recurse -Include *.cr3, *.cr2, *.nef, *.arw, *.orf, *.rw2
        ($lines.Count - 1) | Should -Be $rawFiles.Count -Because "CSV must contain one row per RAW file"
    }

    It "does not leak files into project root" -Skip:(-not (Get-Command magick -ErrorAction SilentlyContinue)) {

        $forbidden = @(
            "yolov9.pt",
            "yolov9-c.pt",
            "wildlife_tags.csv",
            "wildlife_metadata.csv"
        )

        foreach ($f in $forbidden) {
            $path = Join-Path $ProjectRoot $f
            Test-Path $path | Should -BeFalse -Because "$f must not appear in project root"
        }
    }
}
