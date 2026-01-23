import re
import time
import argparse
import pathvalidate

from pathlib import Path
from collections import defaultdict

from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

from difflib import SequenceMatcher
from pyfzf.pyfzf import FzfPrompt

from ottlog import logger
from sconfig import parse_config_with_defaults
from ffmparakeet import run_ffmpeg

from colorama import Fore
from colorama import Style

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--load-mix", type=str, help="Load a mix from a directory or file")
    parser.add_argument("-s", "--search", type=str, help="Search from directory")
    parser.add_argument("-o", "--output", type=str, help="Output to directory")
    parser.add_argument("-n", "--name", type=str, help="Mix name")

    args = parser.parse_args()

    search = args.search
    output = args.output

    config = parse_config_with_defaults(section="mix", params=[("search", str, search), ("output", str, output)])
    search, output = config["search"], config["output"]

    while search is None or not Path(search).is_dir():
        search = input("Search: ").strip('"')

    while output is None:
        output = input("Output: ").strip('"')

    search = Path(search)
    output = Path(output)

    if not search.exists() or not search.is_dir():
        logger.error(f"Search directory does not exist: {search}")
        return

    output.mkdir(parents=True, exist_ok=True)

    files = list(search.rglob("*.mp3"))

    audio_files = [MP3(file, ID3=EasyID3) for file in files]
    file_names = []

    file_name_to_audio_file = defaultdict()

    for audio_file in audio_files:
        track_name = audio_file.get('Title', 'Unknown Title')[0]

        file_names.append(track_name)
        file_name_to_audio_file[track_name] = audio_file

    mix_title = "" if args.name is None else args.name
    mix = []

    ###########################################################################################

    if args.load_mix is not None:
        loaded_mix_path = Path(args.load_mix)

        if loaded_mix_path.is_file():
            mix_title = loaded_mix_path.stem

            with open(loaded_mix_path, 'r') as file:
                for line in file:
                    processed_line = line.strip()

                    track = None
                    best_match = 0

                    for audio_track in audio_files:
                        match_ratio = SequenceMatcher(None, audio_track.get('Title', 'Unknown Title')[0],
                                                      processed_line).ratio()

                        if match_ratio > best_match:
                            best_match = match_ratio
                            track = audio_track

                    if track is not None:
                        mix.append(track)

            print(f"Loaded {len(mix)} tracks from {mix_title}.\nPress enter to continue")
        elif loaded_mix_path.is_dir():
            mix_title = loaded_mix_path.stem

            mix_tracks = list(loaded_mix_path.rglob("*.mp3"))
            mix_audio_files = [MP3(file, ID3=EasyID3) for file in mix_tracks]

            for audio_file in mix_audio_files:
                mix.append(file_name_to_audio_file[audio_file.get('Title', 'Unknown Title')[0]])

            print(f"Loaded {len(mix)} tracks from {mix_title}")
        else:
            print(f"Didn't find a file or directory to load a mix from at {loaded_mix_path}.\nPress enter to continue")

    ###########################################################################################

    while mix_title.strip() == "":
        inp = input("Enter mix title :3 : ")
        mix_title = pathvalidate.sanitize_filename(inp).strip()

    ok = input(f"Searching {search} and outputting to {output / mix_title}. OK? (y/n): ")

    if ok.lower() != "y":
        return

    EXIT = ".exit"
    VIEW = ".mix"
    ADD_BREAK = ".add_break"
    SAVE_AND_CLOSE = ".save"

    options = [*file_names, VIEW, ADD_BREAK, SAVE_AND_CLOSE, EXIT]
    fzf = FzfPrompt()

    while True:
        selected = fzf.prompt(options)
        if len(selected) != 1:
            continue
        selected = selected[0]

        if selected == VIEW:
            view(mix)
            continue
        elif selected == ADD_BREAK:
            add_break(mix)
            continue
        elif selected == SAVE_AND_CLOSE:
            break
        elif selected == EXIT:
            return

        selected = file_name_to_audio_file[selected]
        mix.append(selected)

    output_mix_path = output / mix_title
    output_mix_path.mkdir(parents=True, exist_ok=True)
    for i, file in enumerate(mix):
        filepath = Path(file.filename)
        output_path = output_mix_path / filepath.name
        run_ffmpeg(track_num=i + 1, album=mix_title, source=filepath, destination=output_path)

def view(mix):
    print()

    longest_title = max(len(song.get('Title', 'Unknown Title')[0]) for song in mix if isinstance(song, MP3)) + 10
    section_num = 0
    section_length: float = 0
    total_length: float = 0

    index_format = "02" if len(mix) >= 10 else "0"
    padding = re.sub('.', ' ', f"{len(mix):{index_format}}. ")

    title_a = "Song Title"
    title_b = "Length"
    print(f"{padding}{title_a.ljust(longest_title)} {title_b}")

    for i, song in enumerate(mix):
        if not isinstance(song, MP3):
            break_time_cutoff_raw = song.split(" ")[1]

            time_values = break_time_cutoff_raw.split(":")

            break_time_cutoff: int = 0

            if len(time_values) == 1:
                break_time_cutoff = int(time_values[0])
            elif len(time_values) == 2:
                break_time_cutoff = int(time_values[0]) * 60 + int(time_values[0])
            elif len(time_values) == 3:
                break_time_cutoff = int(time_values[0]) * 60 * 60 + int(time_values[1]) * 60 + int(time_values[2])

            time_difference = abs(break_time_cutoff - section_length)
            section_length_ok = section_length <= break_time_cutoff
            difference_sign = "-" if section_length_ok else "+"

            color = Fore.GREEN if section_length_ok else Fore.RED

            time_struct = time.gmtime(time_difference)
            section_length_as_str = time.strftime("%H:%M:%S", time_struct)

            part_name = f"{alphabet[section_num].upper()} Side"

            print(f"{Fore.YELLOW}{i + 1:{index_format}}. {part_name.ljust(longest_title, '.')}{Style.RESET_ALL} {color}{difference_sign}{section_length_as_str}{Style.RESET_ALL} ")

            section_num += 1
            section_length = 0
        else:
            song_title = song.get('Title', 'Unknown Title')[0]
            song_length = song.info.length
            time_struct = time.gmtime(song_length)
            song_length_as_str = time.strftime("%H:%M:%S", time_struct)

            section_length += song_length
            total_length += song_length

            print(f"{i + 1:{index_format}}. {song_title.replace("： ", ": ").ljust(longest_title, '.')} ({song_length_as_str})")

    time_struct = time.gmtime(total_length)
    total_length_as_str = time.strftime("%H:%M:%S", time_struct)

    length_prompt = "Total"
    print(f"{padding}{length_prompt.ljust(longest_title, '.')} ({total_length_as_str})\n")

    input("Press enter to continue...")

def add_break(mix):
    limit = input("Section length (hh:mm:ss): ")

    mix.append(f".break {limit}")

alphabet = "abcdefghijklknopqrstuvwxyz"

if __name__ == "__main__":
    main()
