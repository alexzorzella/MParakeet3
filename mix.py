import re
import time
from pathlib import Path

from colorama import Fore, Style
from mutagen.mp3 import MP3
from pyfzf import FzfPrompt

from loader import Loader

class Mix:
    mix_title = ""
    track_groups: list[list] = []

    output = None
    loader: Loader | None = None

    group_mode = False

    def __init__(self, mix_title, output=None):
        self.mix_title = mix_title
        self.output = output

    def current_mode(self):
        return f"{Fore.LIGHTGREEN_EX}(Group Mode){Style.RESET_ALL}" if self.group_mode else f"{Fore.LIGHTCYAN_EX}(Track Mode){Style.RESET_ALL}"

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

        return len(self.track_groups), 0

    def group_length(self, group_index):
        return len(self.track_groups[group_index])

    def move_track_or_group(self, from_index, to_index):
        if from_index == to_index:
            return

        group_index, local_index = self.track_location_by_abs_index(from_index)
        move = self.track_groups[group_index] if self.group_mode else self.track_groups[group_index][local_index]
        move_to_track = self.get_tracks()[to_index] if to_index < self.track_count() else None

        self.remove_track_or_group(from_index)

        if self.group_mode:
            to_index = self.get_tracks().index(move_to_track) if to_index < self.track_count() else self.track_count()
            move_to_group_index, _ = self.track_location_by_abs_index(to_index)
        else:
            if to_index <= 0:
                self.track_groups.insert(0, [move])
                return

            to_index = self.get_tracks().index(move_to_track) if to_index < self.track_count() else self.track_count()
            move_to_group_index, move_to_local_index = self.track_location_by_abs_index(to_index)

            if move_to_group_index >= len(self.track_groups):
                self.track_groups.append([])

            move_to_track_group = self.track_groups[move_to_group_index]

            if len(move_to_track_group) <= 1:
                self.track_groups.insert(move_to_group_index, [move])
            else:
                if move_to_local_index == len(move_to_track_group) - 1:
                    do_insert = input(
                        f"Do you want to insert {Fore.YELLOW}{self.get_track_title(move)}{Style.RESET_ALL} into "
                        f"{Fore.YELLOW}{self.get_track_title(move_to_track)}'s{Style.RESET_ALL} group? (y/n): ").lower()

                    if do_insert:
                        move_to_track_group.insert(move_to_local_index, move)
                    else:
                        self.track_groups.insert(move_to_group_index, [move])
                else:
                    self.track_groups.insert(move_to_group_index, [move])

    def group_tracks_or_groups(self, first_track_index, second_track_index):
        if first_track_index == second_track_index:
            return

        # self.move_track_or_group(from_index=first_track_index, to_index=second_track_index, force_group=True)

    def swap_tracks_or_groups(self, first_track_index, second_track_index):
        first_track_group_index, first_track_local_index = self.track_location_by_abs_index(first_track_index)
        second_track_group_index, second_track_local_index = self.track_location_by_abs_index(second_track_index)

        if self.group_mode:
            (self.track_groups[first_track_group_index],
             self.track_groups[second_track_group_index]) = (
                self.track_groups[second_track_group_index],
                self.track_groups[first_track_group_index])
        else:
            (self.track_groups[first_track_group_index][first_track_local_index],
             self.track_groups[second_track_group_index][second_track_local_index]) = (
                self.track_groups[second_track_group_index][second_track_local_index],
                self.track_groups[first_track_group_index][first_track_local_index])

    def remove_track_or_group(self, track_index):
        group_index, local_index = self.track_location_by_abs_index(track_index)

        if self.group_mode:
            del self.track_groups[group_index]
        else:
            del self.track_groups[group_index][local_index]

            if self.group_length(group_index) <= 0:
                del self.track_groups[group_index]

    def get_track_title(self, track):
        if isinstance(track, MP3):
            return track.get('Title', Path(track.filename).stem)[0]

        return track

    def display(self):
        if self.track_count() <= 0:
            print(f"{Fore.GREEN}{self.mix_title}{Style.RESET_ALL} is empty. Add breaks and tracks below!\n\n")
            return

        longest_title = max(
            len(song.get('Title', Path(song.filename).stem)[0]) for song in self.get_tracks() if isinstance(song, MP3)) + 20
        section_num = 0
        section_length: float = 0
        total_length: float = 0

        index_format, padding = self.get_formatting()

        title_a = "Song Title"
        title_b = "Length"
        print(
            f"{padding}{Fore.GREEN}{self.mix_title}{Style.RESET_ALL}\n\n{Fore.YELLOW}{padding}{title_a.ljust(longest_title)} {title_b}{Style.RESET_ALL}")

        index = 0
        group_number = 0
        for track_group in self.track_groups:
            is_group = len(track_group) > 1

            for track in track_group:
                index_str = f"{index + 1:{index_format}}."

                if not isinstance(track, MP3):
                    break_time_cutoff_raw = track.split(" ")[1]

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

                    if is_group:
                        print(f"{Fore.YELLOW}{index_str} {colors[group_number % len(colors)]}{part_name.ljust(longest_title, '.')}{Style.RESET_ALL} {color}{difference_sign}{section_length_as_str}{Style.RESET_ALL} ")
                    else:
                        print(f"{Fore.YELLOW}{index_str} {part_name.ljust(longest_title, '.')}{Style.RESET_ALL} {color}{difference_sign}{section_length_as_str}{Style.RESET_ALL} ")

                    section_num += 1
                    section_length = 0
                else:
                    song_title = track.get('Title', Path(track.filename).stem)[0]
                    song_length = track.info.length
                    time_struct = time.gmtime(song_length)
                    song_length_as_str = time.strftime("%H:%M:%S", time_struct)

                    section_length += song_length
                    total_length += song_length

                    if is_group:
                        print(f"{index_str} {colors[group_number % len(colors)]}{song_title.replace("： ", ": ").ljust(longest_title, '.')}{Style.RESET_ALL} ({song_length_as_str})")
                    else:
                        print(f"{index_str} {song_title.replace("： ", ": ").ljust(longest_title, '.')} ({song_length_as_str})")

                index += 1

            if is_group:
                group_number += 1

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
    BEGINNING_OF_MIX = ".beginning"
    END_OF_MIX = ".end"

    def prompt_track_selection(self, action_prompt="", include_beginning=False, include_end=False):
        if action_prompt.strip() != "":
            action_prompt = f"{action_prompt.strip()} "

        mix_length = self.track_count()

        choice_index = -2

        min_choice = 0 if include_beginning else 1

        if include_end:
            mix_length += 1

        while choice_index < (min_choice - 1) or choice_index > mix_length:
            mix_choice_input = input(
                f"Select a track or break {action_prompt}using {min_choice}-{mix_length}, [S]earch Mix, or [E]xit: ").lower()

            if mix_choice_input == "e":
                return "e", None
            elif mix_choice_input == "s":
                track_names = self.track_names(include_indices=True)

                options = [*track_names]

                if include_beginning:
                    options.append(Mix.BEGINNING_OF_MIX)

                if include_end:
                    options.append(Mix.END_OF_MIX)

                options.append(Mix.BACK_TO_MIX)

                fzf = FzfPrompt()

                selected = fzf.prompt(options, fzf_options='--cycle')

                if len(selected) != 1:
                    continue

                selected = selected[0]

                if selected == Mix.BACK_TO_MIX:
                    return "e", None
                elif selected == Mix.BEGINNING_OF_MIX:
                    return None, 0
                elif selected == Mix.END_OF_MIX:
                    return None, mix_length

                choice_index = options.index(selected)
            else:
                try:
                    choice_index = int(mix_choice_input)
                    choice_index -= 1
                except:
                    pass

        if choice_index >= 0 and choice_index < self.track_count():
            selection = self.get_tracks()[choice_index]
        else:
            selection = None

        return selection, choice_index

alphabet = "abcdefghijklknopqrstuvwxyz"
colors = [ Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTMAGENTA_EX ]