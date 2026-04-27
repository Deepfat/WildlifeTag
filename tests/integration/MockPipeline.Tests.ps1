Describe "Mock pipeline integration" {

    BeforeAll {
        $script:ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
        $script:WildlifeTag = Join-Path $ProjectRoot "scripts\wildlife_tag.ps1"
        $script:TestRoot    = Join-Path $ProjectRoot "testdata\photos"
        . $WildlifeTag -Test
    }

    It "preview stage runs" {
        { Run-PreviewStage -Root $TestRoot } | Should -Not -Throw
    }

    It "classifier stage runs" {
        { Run-ClassifierStage -Root $TestRoot } | Should -Not -Throw
    }

    It "xmp stage runs" {
        { Run-XmpStage -Root $TestRoot } | Should -Not -Throw
    }
}

