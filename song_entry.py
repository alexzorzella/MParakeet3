from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from baklava import create_label, create_button, create_line_edit, time_int_to_str, BaklavaLineEdit, time_int_str_to_int, resource_path
from globals import AQtAlignCenterLeft, AQtAlignCenterRight, ICON_SIDE_LENGTH, ICON_SIZE, BREAK_SAVE_STR
from mix_utility import MixUtility

class SongEntry:
    filepath: Path
    mp3: MP3

    song_name: str | None = None
    artist: str | None = None
    album: str | None = None

    list_widget_item: QListWidgetItem
    widget: QWidget

    time_label: QLabel

    mix_util = None

    is_break: bool = False
    break_duration: int = 75 * 60
    last_cached_cumulative_duration: int = 0
    duration_input: BaklavaLineEdit

    in_queue: bool = False
    in_search: bool = False

    def __init__(
            self,
            filepath: Path | None,
            mix_util: MixUtility,
            preview_transition_func: Callable | None = None,
            delete_selected_items_and: Callable | None = None,
            queue_method: Callable | None = None,
            queue_next_method: Callable | None = None,
            break_duration: int | None = None,
            in_queue: bool = False,
            in_search: bool = False):
        self.mix_util = mix_util

        if filepath is not None:
            self.filepath = filepath
            self.mp3 = MP3(filepath)

            mp3_data = EasyID3(filepath)

            self.song_name = mp3_data.get("title", [self.filepath.stem])[0]
            self.album = mp3_data.get("album", [None])[0]
            self.artist = mp3_data.get("artist", [None])[0]

        list_widget_item = QListWidgetItem()
        self.list_widget_item = list_widget_item

        parent_widget = QWidget()
        vertical_layout = QVBoxLayout(parent_widget)
        horizontal_layout = QHBoxLayout()

        vertical_layout.addLayout(horizontal_layout)

        if break_duration is not None:
            self.is_break = True
            self.break_duration = break_duration

        name_label = create_label(container=horizontal_layout, text=self.list_entry_format(), alignment=AQtAlignCenterLeft, tooltip=self.tooltip_format())

        name_label.setFixedHeight(35)

        song_utility_layout = QHBoxLayout()
        horizontal_layout.addLayout(song_utility_layout)

        length_as_string: str = time_int_to_str(self.absolute_length())

        if not self.is_break:
            create_label(container=song_utility_layout, text=length_as_string, img_width=30, alignment=AQtAlignCenterRight)
        else:
            create_label(container=song_utility_layout, text="Section Duration:", alignment=AQtAlignCenterRight)
            self.duration_input = create_line_edit(container=song_utility_layout,
                                                   placeholder_text="Length",
                                                   default_value=length_as_string,
                                                   width=70,
                                                   height=35,
                                                   alignment=Qt.AlignCenter,
                                                   connect_to_method=self.update_break_duration,
                                                   on_deselected=self.format_duration_input)

        container = song_utility_layout
        length = ICON_SIDE_LENGTH
        color = "white"
        size = ICON_SIZE

        song_queue = self.mix_util.song_queue

        if not in_queue:
            play_method = lambda: song_queue.queue_song_force_play(filepath)
            delete_method = lambda: delete_selected_items_and(self.list_widget_item)
            preview_method = lambda: preview_transition_func(list_widget_item)
        else:
            play_method = lambda: song_queue.set_head_to_list_widget_item_entry(list_widget_item)
            delete_method = lambda: song_queue.delete_entry_by_list_widget_item(list_widget_item)
            preview_method = lambda: song_queue.preview_list_widget_item(list_widget_item)

        if not self.is_break:
            create_button(container=container, height=length, width=length, icon_path=resource_path("img/play.svg"), icon_color=color, icon_size=size, tooltip="Play",
                          connect_to_method=play_method)

            if not in_queue:
                create_button(container=container, height=length, width=length, icon_path=resource_path("img/list_end.svg"), icon_color=color, icon_size=size, tooltip="Queue Track",
                              connect_to_method=lambda: queue_method(filepath))
                create_button(container=container, height=length, width=length, icon_path=resource_path("img/list_start.svg"), icon_color=color, icon_size=size, tooltip="Play Next",
                              connect_to_method=lambda: queue_next_method(filepath))

            if not in_search:
                create_button(container=container, height=length, width=length, icon_path=resource_path("img/ear.svg"), icon_color=color, icon_size=size, tooltip="Play Transition",
                              connect_to_method=preview_method)
            else:
                create_button(container=container, height=length, width=length, icon_path=resource_path("img/list_plus.svg"), icon_color=color, icon_size=size, tooltip="Add To Mix",
                              connect_to_method=lambda: self.mix_util.add_track_to_selected_mix(filepath))

        if not in_search:
            create_button(container=container, height=length, width=length, icon_path=resource_path("img/delete.svg"), icon_color=color, icon_size=size, tooltip="Delete",
                          connect_to_method=delete_method)

        self.time_label = create_label(container=container, text="00:00:00", alignment=Qt.AlignCenter)

        if in_search:
            self.time_label.hide()

        self.time_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        list_widget_item.setSizeHint(parent_widget.sizeHint())

        self.widget = parent_widget

    def update_break_duration(self, new_duration):
        self.break_duration = time_int_str_to_int(new_duration)
        self.update_time_label(time=self.last_cached_cumulative_duration)

    def format_duration_input(self):
        self.duration_input.setText(time_int_to_str(self.break_duration))

    def update_time_label(self, time: int):
        if not self.is_break:
            time_label_text = time_int_to_str(total_seconds=time)
        else:
            self.last_cached_cumulative_duration = time
            time_diff = self.break_duration - time

            time_label_text = ""

            color = "white"

            if time_diff > 0:
                color = "green"
                time_label_text += "-"
            elif time_diff < 0:
                color = "red"
                time_label_text += "+"

            time_label_text += time_int_to_str(abs(time_diff))

            self.time_label.setStyleSheet(f"color: {color};")

        self.time_label.setText(time_label_text)

    def name(self) -> str:
        return self.song_name if self.song_name is not None else ""

    def absolute_length(self):
        result = self.mp3.info.length if not self.is_break else self.break_duration
        return result

    def length(self) -> int:
        result = self.mp3.info.length if not self.is_break else 0
        return int(result)

    def save_format(self) -> str:
        return self.name() if not self.is_break else f"{BREAK_SAVE_STR} {self.break_duration}"

    def list_entry_format(self) -> str:
        if self.is_break:
            return "Break"

        result = self.name()

        if self.artist is not None:
            result += f"\n{self.artist}"

        if self.album is not None:
            result += f" - {self.album}"

        return result

    def tooltip_format(self) -> str:
        return self.list_entry_format()

    def __str__(self):
        return f"{self.name()}, abs. len: {self.absolute_length()}, len: {self.length()}, filepath: {self.filepath}"