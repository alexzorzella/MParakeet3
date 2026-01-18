import re
import time
import argparse
import subprocess
import configparser
import pathvalidate

from pathlib import Path
from collections import defaultdict

from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

from difflib import SequenceMatcher
from pyfzf.pyfzf import FzfPrompt

from ottlog import logger
from sconfig import parse_config

def run_ffmpeg(track_num: int, mix_title: str, input_path: Path, output_path: Path):
    command = [
        "ffmpeg",
        "-loglevel", "error",
        "-i", str(input_path),
        "-c", "copy",
        "-map_metadata", "0",
        "-metadata", f"track={track_num}",
        "-metadata", f"album={mix_title}",
        "-id3v2_version", "3",
        str(output_path),

    ]
    subprocess.run(command, shell=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--load-mix", type=str, help="Load a mix from a directory or file")

    args = parser.parse_args()

    config = parse_config(section="mix", params=[("search", str), ("mixout", str)])
    search, mix_out = config["search"], config["mixout"]

    search = Path(search)
    mix_out = Path(mix_out)

    if not search.exists() or not search.is_dir():
        logger.error(f"Search directory does not exist: {search}")
        return

    mix_out.mkdir(parents=True, exist_ok=True)


    files = list(search.rglob("*.mp3"))

    audio_files = [ MP3(file, ID3=EasyID3) for file in files ]
    file_names = []

    file_name_to_audio_file = defaultdict()

    for audio_file in audio_files:
        track_name = audio_file.get('Title', 'Unknown Title')[0]

        file_names.append(track_name)
        file_name_to_audio_file[track_name] = audio_file

    mix_title = ""
    mix = []

    ###########################################################################################

    if args.load_mix is not None:
        loaded_mix_path = Path(args.load_mix)

        if loaded_mix_path.is_file():
            mix_title = loaded_mix_path.stem

            with open(loaded_mix_path, 'r') as file:
                for line in file:
                    processed_line = line.strip()

                    tracks = (audio_track for audio_track in audio_files
                              if SequenceMatcher(None, audio_track.get('Title', 'Unknown Title')[0], processed_line).ratio() >= 0.8)
                    track = next(tracks, None)

                    if track is not None:
                        mix.append(track)

            input(f"Loaded {len(mix)} tracks from {mix_title}.\nPress enter to continue")
        elif loaded_mix_path.is_dir():
            mix_title = loaded_mix_path.stem

            mix_tracks = list(loaded_mix_path.rglob("*.mp3"))
            mix_audio_files = [MP3(file, ID3=EasyID3) for file in mix_tracks]

            for audio_file in mix_audio_files:
                mix.append(file_name_to_audio_file[audio_file.get('Title', 'Unknown Title')[0]])

            input(f"Loaded {len(mix)} tracks from {mix_title}")
        else:
            print(f"Didn't find a file or directory to load a mix from at {loaded_mix_path}.\nPress enter to continue")

    ###########################################################################################

    while mix_title.strip() == "":
        inp = input("Enter mix title :3 : ")
        mix_title = pathvalidate.sanitize_filename(inp).strip()

    EXIT = ".exit"
    SHOW = ".show"
    SAVE_AND_CLOSE = ".save"

    options = [*file_names, SHOW, SAVE_AND_CLOSE, EXIT ]
    fzf = FzfPrompt()

    while True:
        selected = fzf.prompt(options)
        if len(selected) != 1:
            continue
        selected = selected[0]

        if selected == SHOW:
            print()

            longest_title = max(len(song.get('Title', 'Unknown Title')[0]) for song in mix) + 10
            total_length: float = 0

            index_format = "02" if len(mix) >= 10 else "0"
            padding = re.sub('.', ' ', f"{len(mix):{index_format}}. ")

            title_a = "Song Title"
            title_b = "Length"
            print(f"{padding}{title_a.ljust(longest_title)} {title_b}")

            for i, song in enumerate(mix):
                song_title = song.get('Title', 'Unknown Title')[0]
                song_length = song.info.length
                time_struct = time.gmtime(song_length)
                song_length_as_str = time.strftime("%H:%M:%S", time_struct)

                total_length += song_length

                print(f"{i+1:{index_format}}. {song_title.ljust(longest_title, '.')} ({song_length_as_str})")

            time_struct = time.gmtime(total_length)
            total_length_as_str = time.strftime("%H:%M:%S", time_struct)

            length_prompt = "Total"
            print(f"{padding}{length_prompt.ljust(longest_title, '.')} ({total_length_as_str})\n")

            input("Press enter to continue...")
            continue
        elif selected == SAVE_AND_CLOSE:
            break
        elif selected == EXIT:
            return

        selected = file_name_to_audio_file[selected]
        mix.append(selected)

    output_mix_path = mix_out / mix_title
    output_mix_path.mkdir(parents=True, exist_ok=True)
    for i, file in enumerate(mix):
        filepath = Path(file.filename)
        output_path = output_mix_path / filepath.name
        run_ffmpeg(track_num=i + 1, mix_title=mix_title, input_path=filepath, output_path=output_path)


if __name__ == "__main__":
    main()