from collections import defaultdict
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QListWidget, QTabWidget, QApplication
from mutagen.mp3 import MP3

from baklava import is_null_or_whitespace
from load_file_action import FileLoadAction
from sconfig import parse_config_with_fallbacks

from globals import DEFAULT_MUSIC_DIR, DEFAULT_MIX_DIR, DEFAULT_MIX_NAME

class MixUtility:
    parent_window = None

    parent_tab_widget: QTabWidget
    currently_selected_tab = 0
    mix_tab_views = None            # This is the list[MixView], but a typehint can't be used with base python util as importing it will lead to a circular dependency

    queue_search_tabs: QTabWidget

    list_widget: QListWidget | None = None
    add_song_file_load_action: FileLoadAction | None = None

    search_path: Path
    mix_path: Path

    music_library: defaultdict[str, MP3]
    player = None

    show_status_bar_message: Callable

    song_queue = None

    def __init__(self, parent_window, show_status_bar_message: Callable):
        self.mix_tab_views = []
        self.parent_window = parent_window
        self.music_library = defaultdict()
        self.show_status_bar_message = show_status_bar_message
        self.parse_config_file()
        self.load_music()

    def parse_config_file(self):
        params = parse_config_with_fallbacks(config_path="config.ini", section="mix", params=[("search", str, ""), ("mixes", str, "")])

        self.search_path = Path(params["search"]) if not is_null_or_whitespace(params["search"]) else DEFAULT_MUSIC_DIR
        self.mix_path = Path(params["mixes"]) if not is_null_or_whitespace(params["mixes"]) else DEFAULT_MIX_DIR

        if not self.search_path.is_dir():
            self.search_path.mkdir(parents=True, exist_ok=False)

        if not self.mix_path.is_dir():
            self.mix_path.mkdir(parents=True, exist_ok=False)

        params = parse_config_with_fallbacks(config_path="config.ini", section="theme", params=[("style", str, "")])

        style = params["style"]

        if style != "":
            print(style)
            QApplication.setStyle(style)

    def load_music(self):
        files = list(self.search_path.rglob("*.mp3"))

        mp3s = [MP3(file) for file in files]

        for mp3 in mp3s:
            track_name = mp3.get('Title', Path(mp3.filename).stem)
            self.music_library[track_name] = mp3

        self.show_status_bar_message(f"Loaded {len(self.music_library)} mp3(s) from {self.search_path}", 8000)

    def currently_selected_mix_view(self):
        try:
            return self.mix_tab_views[self.currently_selected_tab]
        except IndexError:
            return None

    def get_mix_names(self):
        return [mix_view.name for mix_view in self.mix_tab_views]

    def get_first_available_default_mix_name(self):
        name = DEFAULT_MIX_NAME
        mix_names = self.get_mix_names()

        i = 1
        while name in mix_names:
            name = f"{DEFAULT_MIX_NAME} {i}"
            i += 1

        return name

    def get_duplicate_mix_names(self):
        names = []
        duplicate_names = []

        for mix_view_name in self.get_mix_names():
            if mix_view_name in names:
                duplicate_names.append(mix_view_name)
            else:
                names.append(mix_view_name)

        return duplicate_names

    def add_track_to_selected_mix(self, filepath):
        current_mix = self.currently_selected_mix_view()

        if current_mix is not None:
            current_mix.add_song_to_mix(filepath)