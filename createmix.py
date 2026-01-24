import time
import argparse
import pathvalidate

from pathlib import Path
from pyfzf.pyfzf import FzfPrompt

from mix import Mix
from loader import Loader
from ottlog import logger
from sconfig import parse_config_with_defaults
from ffmparakeet import run_ffmpeg

from colorama import Fore
from colorama import Style

EXIT = ".exit"
VIEW = ".mix"
ADD_BREAK = ".add_break"
EXPORT_TO_TXT = ".write_to_txt"
COPY_FILES = ".export_mix"

def main():
    ################################## Setup ##################################

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
        logger.error(f"Search directory {Fore.YELLOW}{search}{Style.RESET_ALL} does not exist")
        return

    loader = Loader(search, output)

    mix_title = ""

    if args.name is not None:
        mix_title = args.name
    elif args.load_mix is not None:
        mix_title = Path(args.load_mix).stem

    mix = Mix(mix_title=mix_title)

    if args.load_mix is not None:
        mix.tracks = loader.load_mix(Path(args.load_mix))

    while mix_title.strip() == "":
        inp = input("Enter mix title :3 : ")
        mix_title = pathvalidate.sanitize_filename(inp).strip()

    ok = input(f"Searching {Fore.YELLOW}{search}{Style.RESET_ALL} and outputting to {Fore.YELLOW}{output / mix_title}{Style.RESET_ALL}. OK? (y/n): ")

    if ok.lower() != "y":
        return

    ################################## Mix Editor ##################################

    options = [*loader.file_names, VIEW, ADD_BREAK, EXPORT_TO_TXT, COPY_FILES, EXIT]
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
        elif selected == EXPORT_TO_TXT:
            export_to_txt(output, mix_title, mix)
            continue
        elif selected == COPY_FILES:
            copy_files(output, mix_title, mix)
            break
        elif selected == EXIT:
            return

        selected = loader.file_name_to_audio_file[selected]
        mix.add_track_or_break(selected)

    ##############################################################################

BACK_TO_MIX = ".back_to_mix"

def view(mix: Mix):
    print("\n" * 100)

    while True:
        mix.display()
        total_tracks = len(mix.tracks)

        mix_choice = -1

        while mix_choice < 1 or mix_choice > total_tracks:
            mix_choice_input = input(f"Select a track or break using 1-{total_tracks}, [S]earch Mix, or [E]xit: ").lower()

            if mix_choice_input == "e":
                return
            elif mix_choice_input == "s":
                track_names = mix.track_names()
                options = [*track_names, BACK_TO_MIX]
                fzf = FzfPrompt()

                selected = fzf.prompt(options)[0]

                if selected == BACK_TO_MIX:
                    continue

                mix_choice = track_names.index(selected)

                pass
            else:
                try:
                    mix_choice = int(mix_choice_input)
                    mix_choice -= 1
                except:
                    pass

        selection = mix.tracks[mix_choice]

        if not isinstance(selection, MP3):
            selection_message = "break"
        else:
            selection_message = selection.get('Title', Path(selection.filename).stem)[0]

        print(f"\nSelecting {Fore.GREEN}{selection_message}{Style.RESET_ALL}")

        song_action = ""

        options = ["m", "g", "p", "t", "r", "e"] if isinstance(selection, MP3) else ["m", "g", "r", "e"]

        while song_action not in options:
            try:
                if isinstance(selection, MP3):
                    song_action = input(f"[M]ove, [G]roup, [P]lay, Preview [T]ransition, [R]emove From Mix, or [E]xit\n\n").lower()
                else:
                    song_action = input("[M]ove, [G]roup, [R]emove From Mix, or [E]xit\n\n").lower()
            except:
                pass

        action_message = ""

        if song_action == "m":
            insert_at = -1

            while insert_at < 1 or insert_at > total_tracks + 1:
                try:
                    insert_at = int(input(f"Move to [1]-[{total_tracks + 1}]: "))
                except:
                    pass

            mix.tracks.remove(selection)
            mix.tracks.insert(insert_at - 1, selection)

            action_message = f"Moved {selection_message} to {insert_at}"
        elif song_action == "g":
            pass
        elif song_action == "p":
            play_song(selection.filename)
        elif song_action == "t":
            selected_song_path = selection.filename

            next_song_index = mix_choice + 1
            next_song = None

            while next_song_index < len(mix.tracks) and not isinstance(next_song, MP3):
                next_song = mix.tracks[next_song_index]
                next_song_index += 1

            if next_song is not None:
                next_song_path = next_song.filename
                preview_transition(selected_song_path, next_song_path, preview_length=10)
        elif song_action == "r":
            mix.tracks.remove(selection)
            action_message = f"Removed {selection_message} from the mix"
        elif song_action == "e":
            pass

        print("\n" * 100)

        if action_message != "":
            _, padding = mix.get_formatting()
            print(f"{Fore.YELLOW}{padding}{action_message}{Style.RESET_ALL}\n")

def add_break(mix):
    while True:
        limit = input("Section length (hh:mm:ss) or [E]xit: ")

        if limit.strip().lower() == "e":
            break

        try:
            time_values = limit.split(":")

            if len(time_values) > 3 or len(time_values) <= 0:
                continue
            else:
                for i, value in enumerate(time_values):
                    int(value)

                mix.append(f".break {limit}")
                return
        except:
            pass

def export_to_txt(output, mix_title, mix):
    output_mix_path = output
    output_mix_path.mkdir(parents=True, exist_ok=True)

    with open(output_mix_path / f"{mix_title}.txt", "w", encoding="utf-8") as file:
        for i, track in enumerate(mix):
            if isinstance(track, MP3):
                track_title = track.get('Title', Path(track.filename).stem)[0]
                print(track_title)
                file.write(f"{track_title}\n")
            elif isinstance(track, str):
                file.write(f"{track}\n")

def copy_files(output, mix_title, mix):
    output_mix_path = output / mix_title
    output_mix_path.mkdir(parents=True, exist_ok=True)

    for i, file in enumerate(mix):
        filepath = Path(file.filename)
        output_path = output_mix_path / filepath.name
        run_ffmpeg(track_num=i + 1, album=mix_title, source=filepath, destination=output_path)

import vlc
from mutagen.mp3 import MP3

def play_song(song_path):
    player = vlc.MediaPlayer(song_path)

    print("Playing preview...")
    player.play()

    input("Press enter to stop playback ")
    player.stop()

def preview_transition(song_ending_path, song_starting_path, preview_length=1):
    song_ending = MP3(song_ending_path)
    song_ending_length = song_ending.info.length

    start_song_ending_at = max(0, song_ending_length - preview_length)

    song_ending_player = vlc.MediaPlayer(song_ending_path)
    song_starting_player = vlc.MediaPlayer(song_starting_path)

    print("Playing preview...")
    song_ending_player.play()

    time.sleep(0.1)

    song_ending_player.set_time(int(start_song_ending_at * 1000))

    time.sleep(preview_length + 0.1)

    song_starting_player.play()

    input("Press enter to stop playback ")
    song_starting_player.stop()

if __name__ == "__main__":
    main()
