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
        logger.error(f"Search directory {Fore.YELLOW}{search}{Style.RESET_ALL} does not exist")
        return

    loader = Loader(search, output)

    mix_title = ""

    if args.name is not None:
        mix_title = args.name
    elif args.load_mix is not None:
        mix_title = Path(args.load_mix).stem

    mix = Mix(mix_title=mix_title, output=output)

    if args.load_mix is not None:
        loader.load_mix(Path(args.load_mix), mix)

    while mix_title.strip() == "":
        inp = input("Enter mix title :3 : ")
        mix_title = pathvalidate.sanitize_filename(inp).strip()

    ok = input(f"Searching {Fore.YELLOW}{search}{Style.RESET_ALL} and outputting to {Fore.YELLOW}{output / mix_title}{Style.RESET_ALL}. OK? (y/n): ")

    if ok.lower() != "y":
        return

    view(mix)

VIEW_OPTIONS = {
    "a" : "[A]dd song(s)",
    "e" : "[E]dit",
    "s" : "[S]ave",
    "x" : "E[x]port",
    "q" : "or [Q]uit"
}

ADD_BREAK = ".add_break"
DONE = ".done"

def add_songs(mix: Mix):
    options = [*mix.loader.file_names, ADD_BREAK, DONE]
    fzf = FzfPrompt()

    while True:
        selected = fzf.prompt(options, '--cycle')

        if len(selected) != 1:
            continue

        selected = selected[0]

        if selected == ADD_BREAK:
            add_break(mix)
            continue
        elif selected == DONE:
            return

        selected = mix.loader.file_name_to_audio_file[selected]
        mix.add_track_or_break(selected)

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

def save(mix: Mix):
    export_to_txt(mix)

def export(mix: Mix):
    export_mode = input("Export to .[t]xt, copy tracks to [f]older, or [E]xit: ")

    if export_mode == "t":
        export_to_txt(mix, only_titles=True)
    elif export_mode == "f":
        copy_files(mix)

def export_to_txt(mix, only_titles=False):
    output_mix_path = mix.output
    output_mix_path.mkdir(parents=True, exist_ok=True)

    note = " (Titles)" if only_titles else ""

    filepath = output_mix_path / f"{mix.mix_title}{note}.txt"

    with open(filepath, "w", encoding="utf-8") as file:
        for track in mix.get_tracks():
            if isinstance(track, MP3):
                track_title = track.get('Title', Path(track.filename).stem)[0]
                file.write(f"{track_title}\n")
            elif isinstance(track, str) and not only_titles:
                file.write(f"{track}")

    input(f"Wrote to {Fore.YELLOW}{filepath}{Style.RESET_ALL}, press enter to continue ")

def copy_files(mix):
    output_mix_path = mix.output / mix.mix_title
    output_mix_path.mkdir(parents=True, exist_ok=True)

    i = 0
    for file in mix.get_tracks():
        if isinstance(file, MP3):
            filepath = Path(file.filename)
            output_path = output_mix_path / filepath.name
            run_ffmpeg(track_num=i + 1, album=mix.mix_title, source=filepath, destination=output_path)
            i += 1

    input(f"Copied tracks to {Fore.YELLOW}{output_mix_path}{Style.RESET_ALL}, press enter to continue ")

def view(mix: Mix):
    print("\n" * 100)

    while True:
        mix.display()

        choice = ""

        options = [option for option in VIEW_OPTIONS.values()]

        while choice not in VIEW_OPTION_FUNCS.keys():
            choice = input(f"{", ".join(options)}: ").lower()

        if choice == "q":
            break

        VIEW_OPTION_FUNCS[choice](mix)

EDIT_OPTIONS = {
    "o" : "Switch M[o]de",
    "m" : "[M]ove",
    "s" : "[S]wap",
    "g" : "[G]roup",
    "p" : "[P]lay",
    "t" : "Preview [T]ransition",
    "r" : "[R]emove From Mix",
    "e" : "[E]xit"
}

def switch_mode(mix: Mix, selection, first_track_index, selected_track_title):
    mix.group_mode = not mix.group_mode

    return f"Switched to {mix.current_mode()}"

def move(mix: Mix, selection, first_track_index, selected_track_title):
    second_track, second_track_index = mix.prompt_track_selection(action_prompt="to move after", include_beginning=True)

    if second_track == "e":
        return None

    mix.move_track_or_group(from_index=first_track_index, to_index=second_track_index)

    return f"Moved {selected_track_title} to {second_track_index + 1}"

def swap(mix: Mix, selection, first_track_index, selected_track_title):
    second_track, second_track_index = mix.prompt_track_selection(action_prompt="to swap with")

    if second_track == "e":
        return None

    mix.swap_tracks_or_groups(first_track_index=first_track_index, second_track_index=second_track_index)

    if not isinstance(second_track, MP3):
        second_track_title = "break"
    else:
        second_track_title = second_track.get('Title', Path(second_track.filename).stem)[0]

    return f"Swapped {selected_track_title} with {second_track_title}"

def group(mix: Mix, selection, first_track_index, selected_track_title):
    second_track, second_track_index = mix.prompt_track_selection(action_prompt="to group with")

    if second_track == "e":
        return None

    mix.group_tracks_or_groups(first_track_index, second_track_index)

    if not isinstance(second_track, MP3):
        second_track_title = "break"
    else:
        second_track_title = second_track.get('Title', Path(second_track.filename).stem)[0]

    return f"Grouped {selected_track_title} with {second_track_title}"

def play(mix: Mix, selection, first_track_index, selected_track_title):
    play_song(selection.filename)

    return ""

def preview_transition(mix: Mix, selection, first_track_index, selected_track_title):
    selected_song_path = selection.filename

    next_song_index = first_track_index + 1
    next_song = None

    while next_song_index < mix.track_count() and not isinstance(next_song, MP3):
        next_song = mix.get_tracks()[next_song_index]
        next_song_index += 1

    if next_song is not None:
        next_song_path = next_song.filename
        preview_transition(selected_song_path, next_song_path, preview_length=10)

    return ""

def remove_from_mix(mix: Mix, selection, first_track_index, selected_track_title):
    mix.remove_track_or_group(first_track_index)
    return f"Removed {selected_track_title} from the mix"

EDIT_OPTION_FUNCS = {
    "o" : switch_mode,
    "m" : move,
    "s" : swap,
    "g" : group,
    "p" : play,
    "t" : preview_transition,
    "r" : remove_from_mix,
    "e" : None
}

PERSISTENT = [ "o", "g", "p", "t" ]

def edit(mix: Mix):
    print("\n" * 100)

    song_action = ""
    selection, first_track_index, selected_track_title = None, None, None

    while True:
        mix.display()

        if song_action not in PERSISTENT:
            selection, first_track_index = mix.prompt_track_selection()

            if selection == "e":
                return

            if not isinstance(selection, MP3):
                selected_track_title = "break"
            else:
                selected_track_title = selection.get('Title', Path(selection.filename).stem)[0]

        song_action = ""

        print(f"\nSelecting {Fore.GREEN}{selected_track_title}{Style.RESET_ALL}")

        mode = mix.current_mode()

        actions = [ "o", "m", "s", "g", "p", "t", "r", "e"] if isinstance(selection, MP3) else [ "o", "m", "s", "g", "r", "e"]
        options = ", ".join([EDIT_OPTIONS[key] for key in EDIT_OPTIONS.keys() if key in actions])
        options = f"{mode} {options}: "

        while song_action not in actions:
            song_action = input(options).lower()

        if song_action == "e":
            break

        action_message = EDIT_OPTION_FUNCS[song_action](mix, selection, first_track_index, selected_track_title)

        if action_message is None:
            continue

        print("\n" * 100)

        if action_message != "":
            _, padding = mix.get_formatting()
            print(f"{Fore.YELLOW}{padding}{action_message}{Style.RESET_ALL}\n")

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

VIEW_OPTION_FUNCS = {
    "a" : add_songs,
    "e" : edit,
    "s" : save,
    "x" : export,
    "q": None
}

if __name__ == "__main__":
    main()
