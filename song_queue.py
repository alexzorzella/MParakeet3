from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QSlider, QVBoxLayout, QWidget, QHBoxLayout
from mutagen.mp3 import MP3

from baklava import create_label, create_button, resource_path, time_int_to_str, set_button_icon
from globals import ICON_SIDE_LENGTH, ICON_SIZE, NOTHING_PLAYING_MESSAGE, PREVIEW_LENGTH
from mix_utility import MixUtility
from mix_view import MixView
from threaded_vlc_player import ThreadedVlcPlayer

class SongQueue():
    player: ThreadedVlcPlayer

    mix_util: MixUtility
    mix_view: MixView

    current_head_index: int = -1

    currently_playing_label: QLabel

    song_progress_slider: QSlider
    song_progress_label: QLabel
    user_dragging: bool = False

    play_button = None

    def __init__(self, mix_util: MixUtility, create_new_mix: Callable):
        self.mix_util = mix_util
        self.player = mix_util.player

        self.populate_queue_gui(create_new_mix=create_new_mix)

        self.player.song_changed.connect(self.on_song_changed)

    def populate_queue_gui(self, create_new_mix: Callable):
        parent_widget = QWidget()
        queue_parent_layout = QVBoxLayout()
        parent_widget.setLayout(queue_parent_layout)
        self.mix_util.queue_search_tabs.addTab(parent_widget, "Queue")
        # create_label(container=queue_parent_layout, text="Queue", alignment=AQtAlignCenterTop, font_size=15)
        queue_mix_view_parent = QWidget()
        queue_parent_layout.addWidget(queue_mix_view_parent)

        queue_mix_view = create_new_mix(parent=queue_mix_view_parent, is_queue=True)
        queue_mix_view.name = "Queue"
        self.mix_view = queue_mix_view
        self.mix_util.queue_mix_view = queue_mix_view

        currently_playing_label = create_label(container=queue_parent_layout, text=NOTHING_PLAYING_MESSAGE, alignment=Qt.AlignCenter)

        self.currently_playing_label = currently_playing_label

        song_progress_layout = QHBoxLayout()
        queue_parent_layout.addLayout(song_progress_layout)

        song_progress_slider = QSlider(Qt.Orientation.Horizontal)

        song_progress_layout.addWidget(song_progress_slider)

        song_progress_slider.setRange(0, 1000)
        self.song_progress_slider = song_progress_slider

        self.song_progress_slider.sliderPressed.connect(lambda: self.on_progress_slider_pressed())
        self.song_progress_slider.sliderReleased.connect(lambda: self.on_progress_slider_released())

        self.song_progress_label = create_label(container=song_progress_layout, text="00:00/00:00")

        timer = QTimer(self.mix_util.parent_window)
        timer.setInterval(50)
        timer.timeout.connect(self.update_song_progress)
        timer.start()

        controls_layout = QHBoxLayout()
        queue_parent_layout.addLayout(controls_layout)

        length = ICON_SIDE_LENGTH
        size = ICON_SIZE
        color = "white"

        create_button(container=controls_layout, icon_path=resource_path("img/skip_left.svg"), height=length,
                      width=length, icon_size=size, icon_color=color,
                      connect_to_method=lambda: self.mix_util.player.queue_command(
                          self.mix_util.player.skip_backward, ()))
        self.play_button = create_button(container=controls_layout, icon_path=resource_path("img/play.svg"), height=length, width=length,
                                    icon_size=size, icon_color=color,
                                    connect_to_method=lambda: self.mix_util.player.queue_command(self.mix_util.player.toggle_play, ()))
        create_button(container=controls_layout, icon_path=resource_path("img/skip_right.svg"), height=length,
                      width=length, icon_size=size, icon_color=color,
                      connect_to_method=lambda: self.mix_util.player.queue_command(
                          self.mix_util.player.skip_forward, ()))

        self.player.playing_signal.connect(self.on_play_state_changed)

    def on_play_state_changed(self, playing):
        set_button_icon(button=self.play_button, icon_path=resource_path(f"img/{"pause" if playing else "play"}.svg"), color="white")

    def update_song_progress(self):
        if self.user_dragging:
            return

        player = self.mix_util.player.player

        if player.is_playing():
            length = player.get_length()
            time = player.get_time()

            self.song_progress_label.setText(
                f"{time_int_to_str(total_seconds=time / 1000, do_truncate=True)}/{time_int_to_str(total_seconds=length / 1000, do_truncate=True)}")

            if length > 0:
                self.song_progress_slider.setValue(int(time / length * 1000))

    def on_progress_slider_pressed(self):
        self.user_dragging = True

    def on_progress_slider_released(self):
        player = self.mix_util.player.player

        length = player.get_length()
        if length > 0:
            new_time = int(self.song_progress_slider.value() / 1000 * length)
            player.set_time(new_time)

        self.user_dragging = False

    def on_song_changed(self, new_list_widget_item):
        if new_list_widget_item is not None:
            new_song = self.mix_view.current_tracklist.get_song_entry_by_list_widget_item(new_list_widget_item)
            self.current_head_index = self.mix_view.current_tracklist.get_index_of_widget(new_list_widget_item)
            self.currently_playing_label.setText(new_song.name())
        else:
            self.currently_playing_label.setText(NOTHING_PLAYING_MESSAGE)

    def update_current_head_index(self, new_index):
        self.current_head_index = new_index

    def queue_song_force_play(self, path):
        print(f"Queueing {path.stem} and playing")
        self.queue_song_next(paths=path)
        self.player.queue_command(self.player.default_to_first_then_play_song_at_head, ())

    def queue_song(self, paths: Path | list[Path], index = -1):
        # print(f"Queuing {path.stem}")

        if not isinstance(paths, list):
            paths = [ paths ]

        for path in paths:
            self.mix_view.add_song_to_mix(passed_path=path, index=index)

        self.update_player_tracklist()

    def queue_song_next(self, paths: Path | list[Path]):
        index = self.current_head_index + 1
        self.queue_song(paths, index)
        # print(f"Queuing {path.stem} to {index}")
        # self.mix_view.add_song_to_mix(passed_path=path, index=index)
        # self.update_player_tracklist()

    def preview_list_widget_item(self, list_widget_item):
        list_widget_item_index = self.mix_view.current_tracklist.get_index_of_widget(list_widget_item)

        if list_widget_item_index > 0:
            song_entries = self.mix_view.current_tracklist.get_tracklist_as_list_of_song_entry()
            song_entry = song_entries[list_widget_item_index - 1]
            self.player.queue_command(self.player.set_head_to_widget_and_play, (song_entry.list_widget_item,))

            song_ending = MP3(song_entry.filepath)
            song_ending_length = song_ending.info.length
            start_song_ending_at = max(0, song_ending_length - PREVIEW_LENGTH)
            time = int(start_song_ending_at * 1000)

            self.player.queue_command(self.player.set_time, (time,))

    def preview(self, from_path, to_path):
        # print(f"Previewing from {from_path.stem} to {to_path.stem}")

        self.queue_song_next(paths=to_path)
        self.queue_song_next(paths=from_path)

        self.player.queue_command(self.player.skip_forward, ())

        song_ending = MP3(from_path)
        song_ending_length = song_ending.info.length
        start_song_ending_at = max(0, song_ending_length - PREVIEW_LENGTH)

        time = int(start_song_ending_at * 1000)

        self.player.queue_command(self.player.set_time, (time,))

    def set_head_to_list_widget_item_entry(self, list_widget_item):
        # print(f"Setting head to {list_widget_item}")
        self.player.queue_command(self.player.set_head_to_widget_and_play, (list_widget_item,))

    def delete_entry_by_list_widget_item(self, list_widget_item):
        # print(f"Deleting {list_widget_item}")
        self.mix_view.delete_selected_items_and(list_widget_item)

    def update_player_tracklist(self):
        tracklist = self.mix_view.current_tracklist
        self.player.queue_command(self.player.update_tracklist, (tracklist,))