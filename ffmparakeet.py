import re
import subprocess
from pathlib import Path

def run_ffmpeg(
        source: Path,
        destination: Path,
        codec: str = "libmp3lame",
        replace_title: bool = False,
        quiet: bool = True,
        copy: bool = False,
        album: str = "",
        track_num: int = -1):
    destination.parent.mkdir(parents=True, exist_ok=True)

    clean_title = re.sub(r"\s\([a-z0-9]+_(?:Opus|AAC)\)$", '', source.stem)

    command = [ "ffmpeg" ]

    if replace_title:
        destination = str(destination.parent / f"{clean_title}{destination.suffix}")
    else:
        destination = str(destination)

    if quiet:
        command.extend(["-loglevel", "error"])

    command.extend(["-i", source])

    if not copy:
        command.extend(["-codec:a", codec])
    else:
        command.extend(["-c", "copy"])

    command.extend(["-q:a", "0"])
    command.extend(["-map_metadata", "0"])
    command.extend(["-metadata", f"title={clean_title}"])

    if track_num >= 0:
        command.extend(["-metadata", f"track={track_num}"])

    if album.strip() != "":
        command.extend(["-metadata", f"album={album}"])

    command.extend(["-id3v2_version", "3"])
    command.append("-y")
    command.append(str(destination))

    subprocess.run(command, check=True) # shell=True works on Windows

ffmpeg_encoders = {
    "mp3": "libmp3lame",
    "aac": "aac",
    "m4a": "aac",
    "mp4": "aac",
    "flac": "flac",
    "alac": "alac",
    "wav": "pcm_s16le",
    "wav64": "pcm_s24le",
    "aiff": "pcm_s16be",
    "ogg": "libvorbis",
    "oga": "libvorbis",
    "opus": "libopus",
    "ac3": "ac3",
    "eac3": "eac3",
    "mp2": "mp2",
    "ra": "cook",
    "wma": "wmav2",
    "wmav1": "wmav1",
    "tta": "tta",
    "tak": "tak",
    "wv": "wavpack",
    "webm": "libopus",
    "raw": "pcm_s16le"
}

import sys

def get_os():
    platform = sys.platform

    if platform == "win32":
        return "windows"
    elif platform == "darwin":
        return "macos"

    return "linux"