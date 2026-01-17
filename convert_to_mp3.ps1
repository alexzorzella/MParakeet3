$SourceFolder = Join-Path $PSScriptRoot "Music"
$OutputFolder = Join-Path $PSScriptRoot "Converted_Music"
$MaxThreads = 30

if (!(Test-Path $OutputFolder)) { New-Item -ItemType Directory -Path $OutputFolder }

Get-ChildItem -Path $SourceFolder -Include *.m4a, *.opus -Recurse | ForEach-Object -Parallel {
    $RelativePath = $_.FullName.Replace($using:SourceFolder, "").TrimStart("\")
    $TargetFilePath = Join-Path $using:OutputFolder $RelativePath
    $TargetFilePath = [System.IO.Path]::ChangeExtension($TargetFilePath, ".mp3")

    $TargetDir = Split-Path $TargetFilePath
    if (!(Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }

    Write-Host "Converting $($_.Name) to $TargetFilePath" -ForegroundColor Cyan

    ffmpeg -i $_.FullName `
        -codec:a libmp3lame -q:a 0 `
        -map_metadata 0 `
        -id3v2_version 3 `
        -y $TargetFilePath
} -ThrottleLimit $MaxThreads

Write-Host "`nAll files converted!" -ForegroundColor Green