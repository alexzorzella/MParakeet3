import re
import subprocess
from pathlib import Path

def run_ffmpeg(source: Path, destination: Path, quiet: bool = True, copy: bool = False, album: str = "", track_num: int = -1, codec: str = "libmp3lame"):
    destination.parent.mkdir(parents=True, exist_ok=True)

    clean_title = re.sub(r"\s\([a-z0-9]+_(?:Opus|AAC)\)$", '', source.stem)

    command = [ "ffmpeg" ]

    if quiet:
        command.extend(["-loglevel", "error"])

    command.extend(["-i", str(source)])

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

    subprocess.run(command, shell=True)