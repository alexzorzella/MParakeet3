Param(
	[string]$SourceFolderName = "Retitled_Music",
	[string]$OutputFolderName = "Partitioned_Music"
)

$SourceFolder = Join-Path $PSScriptRoot $SourceFolderName
$OutputFolder = Join-Path $PSScriptRoot $OutputFolderName
$MaxTracks = 100

$FolderTrackCounts = @{}
$TotalTrackCount = 0
$TracksProcessed = 0

$FolderSizes = @{}

if (!(Test-Path $OutputFolder)) { New-Item -ItemType Directory -Path $OutputFolder }

Get-ChildItem -Path $SourceFolder -Filter *.mp3 -Recurse | ForEach-Object {
    $escapedPath = [Regex]::Escape($SourceFolder)
    $RelativePath = $_.FullName -replace "^$escapedPath", ""
    $RelativePath = $RelativePath.TrimStart("\")
	
	$RelativeDirectory = Split-Path $RelativePath -Parent
	
	if(-not $FolderTrackCounts.ContainsKey($RelativeDirectory)) {
		$FolderTrackCounts.Add($RelativeDirectory, 0)
	}
	
	$FolderTrackCounts[$RelativeDirectory]++
	$TotalTrackCount++
}

Get-ChildItem -Path $SourceFolder -Filter *.mp3 -Recurse | ForEach-Object {
    $escapedPath = [Regex]::Escape($SourceFolder)
    $RelativePath = $_.FullName -replace "^$escapedPath", ""
    $RelativePath = $RelativePath.TrimStart("\")
	
	$RelativeDirectory = Split-Path $RelativePath -Parent
	
	if(-not $FolderSizes.ContainsKey($RelativeDirectory)) {
		$FolderSizes.Add($RelativeDirectory, 0)
	}

	$TotalCopiedTracks = $FolderSizes[$RelativeDirectory]
	
	$RelativeTrackNum = $TotalCopiedTracks % $MaxTracks
	$FolderNum = ($TotalCopiedTracks - $RelativeTrackNum) / $MaxTracks

	$Min = $FolderNum * $MaxTracks + 1
	$Max = ($FolderNum + 1) * $MaxTracks

	$TotalTracks = $FolderTrackCounts[$RelativeDirectory]
	$Max = [Math]::Min($Max, $TotalTracks)

	$FormattedRange = "($Min-$Max)"

	$TargetDir = Join-Path $OutputFolder "$RelativeDirectory $FormattedRange"

	$TargetFilePath = Join-Path $TargetDir $_.Name
    if (!(Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }

	$FolderSizes[$RelativeDirectory]++
	$TracksProcessed++

	ffmpeg -i $_.FullName `
		-c copy `
		-map_metadata 0 `
		-id3v2_version 3 `
		-y $TargetFilePath 2>$null

	Write-Progress -Activity "Partitioning $SourceFolderName" `
				   -Status "($TracksProcessed/$TotalTrackCount) Complete, Copying $($_.Name)" `
				   -PercentComplete ([math]::Round($TracksProcessed / $TotalTrackCount * 100))
}