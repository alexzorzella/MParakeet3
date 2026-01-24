import re
import time
from pathlib import Path

from colorama import Fore, Style
from mutagen.mp3 import MP3
from pyfzf import FzfPrompt


class Mix:
    mix_title = ""
    tracks = []

    def __init__(self, mix_title):
        self.mix_title = mix_title

    def add_track_or_break(self, new_track):
        self.tracks.append(new_track)

    def display(self):
        longest_title = max(
            len(song.get('Title', Path(song.filename).stem)[0]) for song in self.tracks if isinstance(song, MP3)) + 20
        section_num = 0
        section_length: float = 0
        total_length: float = 0

        index_format, padding = self.get_formatting()

        title_a = "Song Title"
        title_b = "Length"
        print(
            f"{padding}{Fore.GREEN}{self.mix_title}\n\n{Style.RESET_ALL}{Fore.YELLOW}{padding}{title_a.ljust(longest_title)} {title_b}{Style.RESET_ALL}")

        for i, song in enumerate(self.tracks):
            index_str = f"{i + 1:{index_format}}."

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

                print(
                    f"{Fore.YELLOW}{index_str} {part_name.ljust(longest_title, '.')}{Style.RESET_ALL} {color}{difference_sign}{section_length_as_str}{Style.RESET_ALL} ")

                section_num += 1
                section_length = 0
            else:
                song_title = song.get('Title', Path(song.filename).stem)[0]
                song_length = song.info.length
                time_struct = time.gmtime(song_length)
                song_length_as_str = time.strftime("%H:%M:%S", time_struct)

                section_length += song_length
                total_length += song_length

                print(
                    f"{index_str} {song_title.replace("： ", ": ").ljust(longest_title, '.')} ({song_length_as_str})")

        time_struct = time.gmtime(total_length)
        total_length_as_str = time.strftime("%H:%M:%S", time_struct)

        length_prompt = "Total"
        print(f"{padding}{length_prompt.ljust(longest_title, '.')} ({total_length_as_str})\n")

    def get_formatting(self):
        index_format = "0"
        num_digits = len(str(len(self.tracks)))

        if num_digits > 1:
            index_format += str(num_digits)

        padding = re.sub('.', ' ', f"{len(self.tracks):{index_format}}. ")

        return index_format, padding

    def track_names(self, include_indices=False):
        result = []

        section_num = 0

        index_format, _ = self.get_formatting()

        for i, song in enumerate(self.tracks):
            index_str = f"{i + 1:{index_format}}. " if include_indices else ""

            if not isinstance(song, MP3):
                part_name = f"{index_str}{alphabet[section_num].upper()} Side"
                result.append(part_name)

                section_num += 1
            else:
                song_title = song.get('Title', Path(song.filename).stem)[0]
                song_title_formatted = f"{index_str}{song_title}"
                result.append(song_title_formatted)

        return result

    def mix_length(self):
        return len(self.tracks)

    BACK_TO_MIX = ".back_to_mix"

    def prompt_selection(self, action_prompt=""):
        if action_prompt.strip() != "":
            action_prompt = f"{action_prompt.strip()} "

        mix_length = len(self.tracks)

        mix_choice = -1

        while mix_choice < 0 or mix_choice >= mix_length:
            mix_choice_input = input(
                f"Select a track or break {action_prompt}using 1-{mix_length}, [S]earch Mix, or [E]xit: ").lower()

            if mix_choice_input == "e":
                return
            elif mix_choice_input == "s":
                track_names = self.track_names(include_indices=True)
                options = [*track_names, Mix.BACK_TO_MIX]
                fzf = FzfPrompt()

                selected = fzf.prompt(options, fzf_options='--cycle')

                if len(selected) != 1 or selected == Mix.BACK_TO_MIX:
                    continue

                selected = selected[0]

                mix_choice = track_names.index(selected)
            else:
                try:
                    mix_choice = int(mix_choice_input)
                    mix_choice -= 1
                except:
                    pass

        selection = self.tracks[mix_choice]

        return selection, mix_choice

alphabet = "abcdefghijklknopqrstuvwxyz"
colors = [ Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA ]