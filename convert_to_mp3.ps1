function Get-IniContent ($Path) {
    $ini = @{}
    Get-Content -Path $Path | ForEach-Object {
        $_ = $_.Trim()
        if ($_ -notmatch '^(;|$|#)') {
            if ($_ -match '^\[.*\]$') {
                $section = $_ -replace '\[|\]'
                $ini[$section] = @{}
            } elseif ($section -and $_ -match '(.+?)=(.+)') {
                $key, $value = $_ -split '\s*=\s*', 2
                $ini[$section][$key] = $value
            }
        }
    }
    return $ini
}

$configFile = Join-Path $PSScriptRoot "config.ini"
$configData = Get-IniContent -Path $configFile

$SourceFolder = $configData["music"]["source"].Trim('"')
$OutputFolder = $configData["music"]["output"].Trim('"')
[int]$FolderTrackLimit = $configData["music"]["foldertracklimit"]
[int]$MaxThreads = $configData["music"]["maxthreads"]

Write-Host "Source: $SourceFolder, Output: $OutputFolder, FolderTrackLimit: $FolderTrackLimit, MaxThreads: $MaxThreads"

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