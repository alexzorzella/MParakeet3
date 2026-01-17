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

# $FolderTrackCounts = @{}
# $TotalTrackCount = 0
# $TracksProcessed = 0

# $FolderSizes = @{}

# Get-ChildItem -Path $SourceFolder -Filter *.mp3 -Recurse | ForEach-Object {
#     $escapedPath = [Regex]::Escape($SourceFolder)
#     $RelativePath = $_.FullName -replace "^$escapedPath", ""
#     $RelativePath = $RelativePath.TrimStart("\")
	
# 	$RelativeDirectory = Split-Path $RelativePath -Parent
	
# 	if(-not $FolderTrackCounts.ContainsKey($RelativeDirectory)) {
# 		$FolderTrackCounts.Add($RelativeDirectory, 0)
# 	}
	
# 	$FolderTrackCounts[$RelativeDirectory]++
# 	$TotalTrackCount++
# }

$configFile = Join-Path $PSScriptRoot "config.ini"
$configData = Get-IniContent -Path $configFile

$SourceFolder = $configData["music"]["source"].Trim('"')
$OutputFolder = $configData["music"]["output"].Trim('"')
[int]$FolderTrackLimit = $configData["music"]["foldertracklimit"]
[int]$MaxThreads = $configData["music"]["maxthreads"]

$Continue = Read-Host -Prompt "Converting audio files in $SourceFolder to mp3. Outputting to $OutputFolder. Continue? (y/n)"

if ($Continue.ToLower() -ne "y") {
	return;
}

if (!(Test-Path $OutputFolder)) { New-Item -ItemType Directory -Path $OutputFolder }

Get-ChildItem -Path $SourceFolder -Include *.m4a, *.opus, *.mp3, *.flac, *.wav -Recurse | ForEach-Object -Parallel {
	$Shell = New-Object -ComObject Shell.Application
    $originalName = $_.BaseName

    $RelativePath = $_.FullName.Replace($using:SourceFolder, "").TrimStart("\")
    $TargetFilePath = Join-Path $using:OutputFolder $RelativePath

	if (-not $TargetFilePath -contains ".mp3") {
		$TargetFilePath = [System.IO.Path]::ChangeExtension($TargetFilePath, ".mp3")
	}

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

    # Write-Host "Converting $($_.Name) to $TargetFilePath" -ForegroundColor Cyan

    # ffmpeg -i $_.FullName `
    #     -codec:a libmp3lame -q:a 0 `
    #     -map_metadata 0 `
    #     -id3v2_version 3 `
    #     -y $TargetFilePath
} -ThrottleLimit $MaxThreads

Write-Host "`nAll files converted!" -ForegroundColor Green