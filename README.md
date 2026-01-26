<div align="center">
<h1>MParakeet3</h1>  
</div>

## Requirements
- [FZF](https://github.com/junegunn/fzf)
- [ffmpeg](https://www.ffmpeg.org/download.html)
- [VLC](https://images.videolan.org/vlc/download-windows.html)

To install them on Windows, use `winget install fzf`, `winget install ffmpeg`, and `winget install VideoLAN.VLC`.<br>To install them on Mac, use [Homebrew](https://brew.sh/) to run `brew install fzf`, `brew install ffmpeg`, and `brew install vlc`.

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
Mixtape creation is the main event here. By using music in a specified search directory, mixtapes can be created from scratch, loaded from a `.txt` file, or loaded from a directory contianing music.<br><br>
Tracks can be added, removed, and re-ordered in the mix. To keep track of side lengths for formats with time restrictions like cassette tapes and CDs, breaks can be added containing a maximum time. Breaks display how much their section is over or under. Tracks and breaks can be grouped together to be moved as a unit.<br><br>
How each song flows into the next is important. Songs can be played when selected in the mix editor and, most importantly, the transition between a song and the song that comes after it can be previewed.<br><br>
The mix can be saved as a `.txt` file including its breaks. It can also be exported as a `.txt` file only containing its track titles, or copied into a directory with metadata including track numbers according to mix order and album name according to the mix title.

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
