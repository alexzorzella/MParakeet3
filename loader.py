from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

class Loader:
    audio_files: list[MP3] = []
    file_name_to_audio_file: defaultdict[str, MP3] = defaultdict()
    file_names: list[str] = []

    def __init__(self, search, output):
        output.mkdir(parents=True, exist_ok=True)

        files = list(search.rglob("*.mp3"))

        self.audio_files = [MP3(file, ID3=EasyID3) for file in files]

        for audio_file in self.audio_files:
            track_name = audio_file.get('Title', Path(audio_file.filename).stem)[0]

            self.file_names.append(track_name)
            self.file_name_to_audio_file[track_name] = audio_file

    def load_mix(self, loaded_mix_path, mix):
        if loaded_mix_path.is_file():
            mix_title = loaded_mix_path.stem

            with open(loaded_mix_path, 'r') as file:
                for line in file:
                    if line.split(" ")[0] == ".break":
                        mix.add_track_or_break(line)
                    else:
                        processed_line = line.strip()

                        track = None
                        best_match = 0

                        for audio_track in self.audio_files:
                            match_ratio = SequenceMatcher(None,
                                                          audio_track.get('Title', Path(audio_track.filename).stem)[0],
                                                          processed_line).ratio()

                            if match_ratio > best_match:
                                best_match = match_ratio
                                track = audio_track

                        if track is not None:
                            mix.add_track_or_break(track)
        elif loaded_mix_path.is_dir():
            mix_title = loaded_mix_path.stem

            mix_tracks = list(loaded_mix_path.rglob("*.mp3"))
            mix_audio_files = [MP3(file, ID3=EasyID3) for file in mix_tracks]

            for audio_file in mix_audio_files:
                audio_file_as_track = self.file_name_to_audio_file[audio_file.get('Title', Path(audio_file.filename).stem)[0]]
                mix.add_track_or_break(audio_file_as_track)
        else:
            print(f"Didn't find a file or directory to load a mix from at {loaded_mix_path}.\nPress enter to continue")

        input(f"Loaded {mix.track_count()} tracks from {mix_title}.\nPress enter to continue")

        mix.loader = self