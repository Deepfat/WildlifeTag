Import-Module "$PSScriptRoot/../../scripts/wildlife_tag.ps1" -Force

Describe "wildlife_tag.ps1" {

    BeforeEach {
        $global:settingsPath = "$PSScriptRoot/fake_settings.json"
        $global:settingsObj = @{
            model_path = "model.pt"
            confidence = 0.55
            verbose = $true
            photo_root = ""
        }

        $settingsObj | ConvertTo-Json -Depth 5 | Set-Content $settingsPath
    }

    AfterEach {
        Remove-Item $settingsPath -ErrorAction SilentlyContinue
    }

    Describe "Load-Settings" {
        It "loads settings.json successfully" {
            Mock Test-Path { $true }
            Mock Get-Content { Get-Content $settingsPath }

            $result = Load-Settings
            $result.Data.model_path | Should -Be "model.pt"
        }

        It "throws if settings.json missing" {
            Mock Test-Path { $false }
            { Load-Settings } | Should -Throw
        }
    }

    Describe "Resolve-Root" {
        It "throws when no root provided" {
            { Resolve-Root $null } | Should -Throw
        }

        It "resolves valid path" {
            Mock Resolve-Path { "C:\Photos" }
            Mock Test-Path { $true }
            Resolve-Root "C:\Photos" | Should -Be "C:\Photos"
        }

        It "throws when folder missing" {
            Mock Resolve-Path { "C:\Missing" }
            Mock Test-Path { $false }
            { Resolve-Root "C:\Missing" } | Should -Throw
        }
    }

    Describe "Build-Params" {
        It "produces correct JSON" {
            $json = Build-Params `
                -jpg "a.jpg" `
                -raw "a.CR3" `
                -model "m.pt" `
                -conf 0.5 `
                -verbose $true `
                -test $false

            $obj = $json | ConvertFrom-Json

            $obj.jpeg    | Should -Be "a.jpg"
            $obj.raw     | Should -Be "a.CR3"
            $obj.model   | Should -Be "m.pt"
            $obj.conf    | Should -Be 0.5
            $obj.verbose | Should -Be $true
            $obj.test    | Should -Be $false
        }
    }

    Describe "Run-PreviewStage" {
        It "calls preview script" {
            Mock Test-Path { $true }
            Mock -CommandName '&' { }   # correct mock for call operator
            { Run-PreviewStage -root "C:\Photos" -test:$false } | Should -Not -Throw
        }

        It "throws if preview script missing" {
            Mock Test-Path { $false }
            { Run-PreviewStage -root "C:\Photos" -test:$false } | Should -Throw
        }
    }

    Describe "Run-ClassifierStage" {

        It "skips files with missing JPG" {
            Mock Get-ChildItem { @(
                [pscustomobject]@{
                    FullName="A.CR3"
                    DirectoryName="C:\P"
                    BaseName="A"
                }
            )}

            Mock Test-Path { $false }
            Mock python {}

            Run-ClassifierStage -root "C:\P" -model "m" -conf 0.5 -verbose $true -test:$false
        }

        It "calls python for valid pairs" {
            Mock Get-ChildItem { @(
                [pscustomobject]@{
                    FullName="A.CR3"
                    DirectoryName="C:\P"
                    BaseName="A"
                }
            )}

            Mock Test-Path { $true }

            $called = $false
            Mock python { $called = $true }

            Run-ClassifierStage -root "C:\P" -model "m" -conf 0.5 -verbose $true -test:$false

            $called | Should -Be $true
        }
    }
}
