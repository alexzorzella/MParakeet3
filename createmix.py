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
        selected = fzf.prompt(options, '--cycle')

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

def view(mix: Mix):
    print("\n" * 100)

    while True:
        mix.display()

        mix_length = mix.mix_length()

        selection, first_track_index = mix.prompt_track_selection()

        if selection == "e":
            return

        if not isinstance(selection, MP3):
            selected_track_title = "break"
        else:
            selected_track_title = selection.get('Title', Path(selection.filename).stem)[0]

        print(f"\nSelecting {Fore.GREEN}{selected_track_title}{Style.RESET_ALL}")

        song_action = ""

        options = ["m", "s", "g", "p", "t", "r", "e"] if isinstance(selection, MP3) else ["m", "s", "g", "r", "e"]

        while song_action not in options:
            try:
                if isinstance(selection, MP3):
                    song_action = input(f"[M]ove, [S]wap, [G]roup, [P]lay, Preview [T]ransition, [R]emove From Mix, or [E]xit: ").lower()
                else:
                    song_action = input("[M]ove, [S]wap, [G]roup, [R]emove From Mix, or [E]xit: ").lower()
            except:
                pass

        action_message = ""

        if song_action == "m" or song_action == "s":
            action_prompt = "Move" if song_action == "m" else "Swap"

            if song_action == "m":
                _, second_track_index = mix.prompt_track_selection(action_prompt=action_prompt, include_end=True)

                mix.tracks.remove(selection)
                mix.tracks.insert(second_track_index - 1, selection)
            elif song_action == "s":
                second_track, second_track_index = mix.prompt_track_selection(action_prompt=action_prompt)

                mix.tracks[first_track_index], mix.tracks[second_track_index] = mix.tracks[second_track_index], mix.tracks[first_track_index]

            if song_action == "m":
                action_message = f"Moved {selected_track_title} to {second_track_index + 1}"
            elif song_action == "s":
                if not isinstance(second_track, MP3):
                    second_track_title = "break"
                else:
                    second_track_title = second_track.get('Title', Path(second_track.filename).stem)[0]

                action_message = f"Swapped {selected_track_title} with {second_track_title}"

        elif song_action == "g":
            pass
        elif song_action == "p":
            play_song(selection.filename)
        elif song_action == "t":
            selected_song_path = selection.filename

            next_song_index = first_track_index + 1
            next_song = None

            while next_song_index < len(mix.tracks) and not isinstance(next_song, MP3):
                next_song = mix.tracks[next_song_index]
                next_song_index += 1

            if next_song is not None:
                next_song_path = next_song.filename
                preview_transition(selected_song_path, next_song_path, preview_length=10)
        elif song_action == "r":
            mix.tracks.remove(selection)
            action_message = f"Removed {selected_track_title} from the mix"

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

            if len(time_values) <= 3 and len(time_values) > 0:
                for value in time_values:
                    int(value)

                mix.add_track_or_break(f".break {limit}")
                break
        except:
            pass

def export_to_txt(output, mix_title, mix):
    output_mix_path = output
    output_mix_path.mkdir(parents=True, exist_ok=True)

    with open(output_mix_path / f"{mix_title}.txt", "w", encoding="utf-8") as file:
        for track in mix.tracks:
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
