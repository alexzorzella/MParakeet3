import re
import time
from pathlib import Path

from colorama import Fore, Style
from mutagen.mp3 import MP3

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
                    f"{Fore.YELLOW}{i + 1:{index_format}}. {part_name.ljust(longest_title, '.')}{Style.RESET_ALL} {color}{difference_sign}{section_length_as_str}{Style.RESET_ALL} ")

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
                    f"{i + 1:{index_format}}. {song_title.replace("： ", ": ").ljust(longest_title, '.')} ({song_length_as_str})")

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

    def track_names(self):
        result = []

        section_num = 0

        for i, song in enumerate(self.tracks):
            if not isinstance(song, MP3):
                part_name = f"{alphabet[section_num].upper()} Side"
                result.append(part_name)

                section_num += 1
            else:
                song_title = song.get('Title', Path(song.filename).stem)[0]
                result.append(song_title)

        return result

alphabet = "abcdefghijklknopqrstuvwxyz"
colors = [ Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA ]