$SourceFolder = Join-Path $PSScriptRoot "Converted_Music"
$OutputFolder = Join-Path $PSScriptRoot "Retitled_Music"
$Shell = New-Object -ComObject Shell.Application

if (!(Test-Path $OutputFolder)) { New-Item -ItemType Directory -Path $OutputFolder }

Get-ChildItem -Path $SourceFolder -Filter *.mp3 -Recurse | ForEach-Object -Parallel {
    $Shell = New-Object -ComObject Shell.Application
    
    $originalName = $_.BaseName
    
    $escapedPath = [Regex]::Escape($using:SourceFolder)
    $RelativePath = $_.FullName -replace "^$escapedPath", ""
    $RelativePath = $RelativePath.TrimStart("\")

    $TargetFilePath = Join-Path $using:OutputFolder $RelativePath
    $TargetDir = Split-Path $TargetFilePath
    if (!(Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }

    $FolderObj = $Shell.NameSpace($_.DirectoryName)
    $FileObj = $FolderObj.ParseName($_.Name)
    $currentTitle = $FolderObj.GetDetailsOf($FileObj, 21)

    if ([string]::IsNullOrWhiteSpace($currentTitle)) {
        $cleanTitle = $originalName -replace '\s\([a-z0-9]+_(?:Opus|AAC)\)$', ''
        
        Write-Host "Metadata missing. Copying $cleanTitle with metadata..." -ForegroundColor Yellow
        
        ffmpeg -i $_.FullName `
            -c copy `
            -map_metadata 0 `
            -metadata title="$cleanTitle" `
            -id3v2_version 3 `
            -y $TargetFilePath 2>$null
    }
    else {
        Write-Host "Metadata already exists for $currentTitle. Copying..." -ForegroundColor Gray
        Copy-Item -Path $_.FullName -Destination $TargetFilePath -Force
    }
} -ThrottleLimit 30