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

$FolderTrackCounts = [System.Collections.Concurrent.ConcurrentDictionary[string, int]]::new()

$TotalTrackCount = 0

$TotalTrackBag = [System.Collections.Concurrent.ConcurrentBag[int]]::new()
$ProcessedTracksBag = [System.Collections.Concurrent.ConcurrentBag[int]]::new()

$FolderSizes = [System.Collections.Concurrent.ConcurrentDictionary[string, int]]::new()

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

Write-Host "`n"

Get-ChildItem -Path $SourceFolder -Include *.m4a, *.opus, *.mp3, *.flac, *.wav -Recurse | ForEach-Object -Parallel {
    $escapedPath = [Regex]::Escape($using:SourceFolder)
    $RelativePath = $_.FullName -replace "^$escapedPath", ""
    $RelativePath = $RelativePath.TrimStart("\")
	
	$RelativeDirectory = Split-Path $RelativePath -Parent
	
	[void]($using:FolderTrackCounts).AddOrUpdate($RelativeDirectory, 1, { param($key, $old) $old + 1 })

	($using:TotalTrackBag).Add(1)
	
} -ThrottleLimit $MaxThreads

$TotalTrackCount = $TotalTrackBag.Count

foreach ($item in $FolderTrackCounts.GetEnumerator()) {
	Write-Host "$($item.Key): $($item.Value)"
}

$Continue = Read-Host -Prompt "$($FolderTrackCounts.Count) folders and $TotalTrackCount tracks found. Continue? (y/n)"

if ($Continue.ToLower() -ne "y") {
	return
}

if (!(Test-Path $OutputFolder)) { New-Item -ItemType Directory -Path $OutputFolder }

Get-ChildItem -Path $SourceFolder -Include *.m4a, *.opus, *.mp3, *.flac, *.wav -Recurse | ForEach-Object -Parallel {
	$Shell = New-Object -ComObject Shell.Application
    $originalName = $_.BaseName

    $RelativePath = $_.FullName.Replace($using:SourceFolder, "").TrimStart("\")
    # $TargetFilePath = Join-Path $using:OutputFolder $RelativePath

	##############################################################

	$RelativeDirectory = Split-Path $RelativePath -Parent
	
	[void]($using:FolderSizes).AddOrUpdate($RelativeDirectory, 0, { param($key, $old) $old + 1 })

	$TotalCopiedTracks = ($using:FolderSizes)[$RelativeDirectory]
	
	$RelativeTrackNum = $TotalCopiedTracks % $using:FolderTrackLimit
	$FolderNum = ($TotalCopiedTracks - $RelativeTrackNum) / $using:FolderTrackLimit

	$Min = $FolderNum * $using:FolderTrackLimit + 1
	$Max = ($FolderNum + 1) * $using:FolderTrackLimit

	$TotalTracks = ($using:FolderTrackCounts)[$RelativeDirectory]
	$Max = [Math]::Min($Max, $TotalTracks)

	$FormattedRange = "($Min-$Max)"

	$FinalFolderName = $RelativeDirectory

	if($TotalTracks -gt $using:FolderTrackLimit) {
		$FinalFolderName += " $FormattedRange"
	}

	$TargetDir = Join-Path $using:OutputFolder $FinalFolderName
	$TargetFilePath = Join-Path $TargetDir $_.Name

	##############################################################

	if (-not $TargetFilePath -contains ".mp3") {
		$TargetFilePath = [System.IO.Path]::ChangeExtension($TargetFilePath, ".mp3")
	}

    # $TargetDir = Split-Path $TargetFilePath
    if (!(Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force }

	##############################################################

	[void]($using:FolderSizes)[$RelativeDirectory]++
	($using:ProcessedTracksBag).Add(1)

	##############################################################

	$FolderObj = $Shell.NameSpace($_.DirectoryName)
    $FileObj = $FolderObj.ParseName($_.Name)
    $currentTitle = $FolderObj.GetDetailsOf($FileObj, 21)

	$cleanTitle = ""

    if ([string]::IsNullOrWhiteSpace($currentTitle)) {
        $cleanTitle = $originalName -replace '\s\([a-z0-9]+_(?:Opus|AAC)\)$', ''
        # Write-Host "Metadata missing for $cleanTitle. Copying with metadata..." -ForegroundColor Yellow
    } else {
		$cleanTitle = $currentTitle
        # Write-Host "Metadata already exists for $currentTitle. Copying..." -ForegroundColor Gray
    }

	Write-Host "Converting $cleanTitle ($($_.FullName)) to $TargetFilePath"

	ffmpeg -i $_.FullName `
		-codec:a libmp3lame -q:a 0 `
		-map_metadata 0 `
		-metadata title="$cleanTitle" `
		-id3v2_version 3 `
		-y $TargetFilePath

	Write-Progress -Activity "Partitioning $SourceFolderName" `
				   -Status "($($using:ProcessedTracksBag.Count)/$using:TotalTrackCount) Complete, Copying $($_.Name)" `
				   -PercentComplete ([math]::Round(($using:ProcessedTracksBag.Count) / $using:TotalTrackCount * 100))
} -ThrottleLimit $MaxThreads

Write-Host "`nAll files converted!" -ForegroundColor Green