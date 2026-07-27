import math

from PySide6.QtWidgets import QWidget

from baklava import BaklavaLineEdit, time_int_str_to_int, get_token_value, \
    split_string_by_space_treating_text_wrapped_in_double_quotes_as_single_units
from mix_utility import MixUtility

class SearchView():
    search_field: BaklavaLineEdit
    mix_view = None
    mix_util: MixUtility

    def __init__(self, mix_view, mix_util: MixUtility, parent_layout, search_field):
        super().__init__()

        parent_widget = QWidget()
        parent_widget.setLayout(parent_layout)

        self.mix_util = mix_util
        self.mix_view = mix_view
        self.search_field = search_field

        self.mix_util.queue_search_tabs.addTab(parent_widget, "Search")

        self.search_field.textChanged.connect(self.on_search)

        for _, mp3 in self.mix_util.music_library.items():
            self.mix_view.add_song_to_mix(mp3.filename)

    def on_search(self, new_search):
        search_tokens = split_string_by_space_treating_text_wrapped_in_double_quotes_as_single_units(new_search)
        search_terms = []

        min_duration: int = 0
        max_duration: int = math.inf
        album: str | None = None
        artist: str | None = None

        for token in search_tokens:
            if "length:" in token:
                try:
                    length_value = get_token_value(token, "length")

                    is_ceiling: bool = length_value[0] == "<" or length_value[-1] == ">"
                    is_floor: bool = length_value[0] == ">" or length_value[-1] == "<"

                    length_value = length_value.replace("<", "").replace(">", "")

                    if is_ceiling != is_floor:
                        if is_ceiling:
                            max_duration = time_int_str_to_int(length_value)
                        elif is_floor:
                            min_duration = time_int_str_to_int(length_value)
                except:
                    pass
            elif "album:" in token:
                album = get_token_value(token, "album")
            elif "artist:" in token:
                artist = get_token_value(token, "artist")
                print(artist)
            else:
                search_terms.append(token)

        self.mix_view.filter(search_terms, min_duration, max_duration, album, artist)