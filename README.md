<div align="center">
<h1>MParakeet3</h1>  
</div>

## Setup
MParakeet3 requires [FZF](https://github.com/junegunn/fzf) and [ffmpeg](https://www.ffmpeg.org/download.html). To install them on Windows, use `winget install fzf` and `winget install ffmpeg`.<br>To install them on Mac, use [Homebrew](https://brew.sh/) to run `brew install fzf` and `brew install ffmpeg`.

## Download Playlist
`downloadplaylist.py` allows you to download a playlist from a link into a specified output encoded as a passed audio filetype using `yt-dlp`. If rate limited, it will wait and try again in increasing intervals.

```
downloadplaylist.py [-h] [-l LINK] [-o OUTPUT] [-f FILETYPE] [-q QUIET]

options:
  -h, --help            
  -l, --link LINK           Playlist link.                                 (Required)
  -o, --output OUTPUT       Output directory.                              (Required)
  -f, --filetype FILETYPE   The format of the output files.                (Defaults to mp3)
  -q, --quiet QUIET         Whether the downloader doesn't print logs.     (Defaults to True)
```

## Mass File Conversion
`encode.py` allows you to convert all files in a passed directory to a passed filetype. The folder track limit automatically partitions the music into numbered folders to support older MP3 players with limits on the maximum number of tracks a folder can contain. A folder named 'Socrates' Mix' with 250 songs and a 100 track limit will be partitioned into folders `Socrates' Mix (1-100)`, `Socrates' Mix (101-200)`, and `Socrates' Mix (201-250)`.

```
encode.py [-h] [-s SOURCE] [-o OUTPUT] [-t MAX_THREADS] [-l FOLDER_TRACK_LIMIT] [-f FILETYPE]

options:
  -h, --help            
  -s, --source SOURCE                           Music directory                                          (Required)
  -o, --output OUTPUT                           Output directory                                         (Required)
  -t, --max-threads MAX_THREADS                 The number of CPUs to use                                (Defaults to 1)
  -l, --folder-track-limit FOLDER_TRACK_LIMIT   The maximum number of tracks per folder                  (Defaults to infinity)
  -f, --filetype FILETYPE                       Output file type: i.e. mp3, aac, m4a, flac, wav, ogg     (Defaults to mp3)
```

## Create Mix
`createmix.py` allows for mix creation given a local directory containing music. While searching for music, use `.show` to view the current tracklist, `.save` to copy the tracks into the output directory with metadata so that they're ordered, and `.exit` to exit without saving. Mixes can be loaded by passing a directory or `.txt` file containing the track names into `-l` or `--load-mix`.

```
createmix.py [-h] [-l LOAD_MIX] [-s SEARCH] [-o OUTPUT] [-n NAME]

options:
  -h, --help
  -l, --load-mix LOAD_MIX           Load a mix from a directory or file      (Optional)
  -s, --search SEARCH               Search from directory                    (Required)
  -o, --output OUTPUT               Output to directory                      (Required)
  -n, --name NAME                   Mix name                                 (Optional)
```

## config.ini
MParakeet3 reads information from a local `config.ini` file if provided one. MParakeet3 will always use data from passed parameters over data parsed from the `config.ini` file. The `config.ini` file may have any combination of the following parameters:

```
[music]
source=path
output=path
maxthreads=int
foldertracklimit=int

[mix]
search=path
output=path
```
