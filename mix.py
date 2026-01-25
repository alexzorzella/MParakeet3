import re
import time
from pathlib import Path

from colorama import Fore, Style
from mutagen.mp3 import MP3
from pyfzf import FzfPrompt

class Mix:
    mix_title = ""
    track_groups: list[list] = []

    def __init__(self, mix_title):
        self.mix_title = mix_title

    def add_track_or_break(self, new_track):
        self.track_groups.append([new_track])

    def get_tracks(self):
        flattened_tracks = [item for sublist in self.track_groups for item in sublist]
        return flattened_tracks

        # return self.tracks

    def track_count(self):
        return len(self.get_tracks())

    def track_location_by_abs_index(self, track_index):
        index = 0
        for group_index, track_group in enumerate(self.track_groups):
            for local_index, _ in enumerate(track_group):
                if index == track_index:
                    return group_index, local_index

                index += 1

        return -1, -1

    def group_length(self, group_index):
        return len(self.track_groups[group_index])

    def move_track(self, from_index, to_index):
        group_index, local_index = self.track_location_by_abs_index(from_index)
        move_track = self.track_groups[group_index][local_index]

        self.remove_track(from_index)

        self.track_groups.insert(to_index, [move_track])

    def swap_tracks(self, first_track_index, second_track_index):
        first_track_group_index, first_track_local_index = self.track_location_by_abs_index(first_track_index)
        second_track_group_index, second_track_local_index = self.track_location_by_abs_index(second_track_index)

        (self.track_groups[first_track_group_index][first_track_local_index],
         self.track_groups[second_track_group_index][second_track_local_index]) = (
            self.track_groups[second_track_group_index][second_track_local_index],
            self.track_groups[first_track_group_index][first_track_local_index])

    def remove_track(self, track_index):
        group_index, local_index = self.track_location_by_abs_index(track_index)

        del self.track_groups[group_index][local_index]

        if self.group_length(group_index) <= 0:
            del self.track_groups[group_index]

    def display(self):
        longest_title = max(
            len(song.get('Title', Path(song.filename).stem)[0]) for song in self.get_tracks() if isinstance(song, MP3)) + 20
        section_num = 0
        section_length: float = 0
        total_length: float = 0

        index_format, padding = self.get_formatting()

        title_a = "Song Title"
        title_b = "Length"
        print(
            f"{padding}{Fore.GREEN}{self.mix_title}\n\n{Style.RESET_ALL}{Fore.YELLOW}{padding}{title_a.ljust(longest_title)} {title_b}{Style.RESET_ALL}")

        for i, song in enumerate(self.get_tracks()):
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
        num_digits = len(str(self.track_count()))

        if num_digits > 1:
            index_format += str(num_digits)

        padding = re.sub('.', ' ', f"{self.track_count():{index_format}}. ")

        return index_format, padding

    def track_names(self, include_indices=False):
        result = []

        section_num = 0

        index_format, _ = self.get_formatting()

        for i, song in enumerate(self.get_tracks()):
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

    BACK_TO_MIX = ".back_to_mix"
    END_OF_MIX = ".add_to_end"

    def prompt_track_selection(self, action_prompt="", include_end=False):
        if action_prompt.strip() != "":
            action_prompt = f"{action_prompt.strip()} "

        mix_length = self.track_count()

        if include_end:
            mix_length += 1

        mix_choice = -1

        while mix_choice < 0 or mix_choice >= mix_length:
            mix_choice_input = input(
                f"Select a track or break {action_prompt}using 1-{mix_length}, [S]earch Mix, or [E]xit: ").lower()

            if mix_choice_input == "e":
                return "e", None
            elif mix_choice_input == "s":
                track_names = self.track_names(include_indices=True)

                options = [*track_names]

                if include_end:
                    options.append(Mix.END_OF_MIX)

                options.append(Mix.BACK_TO_MIX)

                fzf = FzfPrompt()

                selected = fzf.prompt(options, fzf_options='--cycle')

                if len(selected) != 1 or selected == Mix.BACK_TO_MIX:
                    continue

                if selected == Mix.BACK_TO_MIX:
                    mix_choice = mix_length
                    continue

                selected = selected[0]

                mix_choice = options.index(selected)
            else:
                try:
                    mix_choice = int(mix_choice_input)
                    mix_choice -= 1
                except:
                    pass

        if mix_choice >= 0 and mix_choice < self.track_count():
            selection = self.get_tracks()[mix_choice]
        else:
            selection = None, None

        return selection, mix_choice

alphabet = "abcdefghijklknopqrstuvwxyz"
colors = [ Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA ]