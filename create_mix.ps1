Param(
	[string]$Search = "Retitled_Music",
	[string]$OutputFolder = "Mix",
	[switch]$WarnDupes,
	[string]$MixName = "My Mix"
)

$SearchFolder = Join-Path $PSScriptRoot $Search
$OutputPath = Join-Path $PSScriptRoot $OutputFolder

if (!(Test-Path $OutputPath)) { New-Item -ItemType Directory -Path $OutputPath }

Write-Host "You're creating this mix in $($PSStyle.Foreground.Yellow)$($OutputPath)$($PSStyle.Reset) searching $($PSStyle.Foreground.Yellow)$($SearchFolder)$($PSStyle.Reset)"
Write-Host "Loading files..."

$fileMap = New-Object 'System.Collections.Concurrent.ConcurrentDictionary[string, string]'

Get-ChildItem -Path $SearchFolder -Filter *.mp3 -Recurse | ForEach-Object -Parallel {
    $Shell = New-Object -ComObject Shell.Application
    
    $FolderObj = $Shell.NameSpace($_.DirectoryName)
    $FileObj = $FolderObj.ParseName($_.Name)
    $currentTitle = $FolderObj.GetDetailsOf($FileObj, 21)

    $key = if (![string]::IsNullOrWhiteSpace($currentTitle)) { $currentTitle } else { $_.Name }

    if (-not ($using:fileMap).TryAdd($key, $_.FullName)) {
		if($using:WarnDupes) {
			Write-Warning "Duplicate title or write-clash: '$key'. Skipping path: $($_.FullName)"
		}
    }
} -ThrottleLimit 30

Write-Host "Loaded $($fileMap.Count) files"

$userInput = ""

$trackCount = 1

while ($userInput -ne "done") {
	$userInput = Read-Host -Prompt "`nSearch for a song (exit with 'done')"
	$userInput = $userInput.ToLower()
	$escapedInput = [regex]::Escape($userInput)

	$searchResults = New-Object System.Collections.Generic.List[object]

	foreach ($entry in $fileMap.GetEnumerator()) {
		$title = $entry.Key.ToLower()

		if ($title -match $escapedInput) {
			$searchResults.Add($entry)
		}
	}

	$filesFound = $searchResults.Count

	if ($filesFound -le 0) {
		Write-Host "$($PSStyle.Foreground.Red)No results.$($PSStyle.Reset)"
	} else {
		Write-Host "`n$($PSStyle.Foreground.Green)$($filesFound) Results:$($PSStyle.Reset)"

		$index = 0
		foreach ($item in $searchResults) {
			Write-Host "$($index + 1). $($item.Key)"
			$index++
		}

		Write-Host "$($index + 1). $($PSStyle.Foreground.Red)Select none$($PSStyle.Reset)"
		
		$choiceIndex = -1

		while ($choiceIndex -lt 0 -or $choiceIndex -gt ($index)) {
			$choice = Read-Host -Prompt "Select a track"
			$choiceIndex = [int]$choice - 1
		}

		if ($choiceIndex -lt ($index + 1)) {
			$selectedTrackName = $searchResults[$choiceIndex].Key
			$selectedTrackFilepath = $searchResults[$choiceIndex].Value

			$cleanFilename = $selectedTrackName -replace '[\\\/:*?"<>|]', ''

			$savePath = Join-Path -Path $OutputFolder -ChildPath "$cleanFilename.mp3"

			ffmpeg -i "$selectedTrackFilepath" `
				-c copy `
				-map_metadata -1 `
				-metadata title="$selectedTrackName" `
				-metadata album="$MixName" `
				-metadata track=$trackCount `
				-id3v2_version 3 `
				-y $savePath 2>$null

			Write-Host "Saved track [$trackCount] $($PSStyle.Foreground.Green)$($selectedTrackName)$($PSStyle.Reset) to $savePath"

			$trackCount++
		}
	}
}