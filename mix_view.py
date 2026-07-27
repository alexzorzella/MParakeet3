from difflib import SequenceMatcher
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QListWidget, QWidget
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QAbstractItemView, QListView, QListWidgetItem, QMessageBox

from baklava import create_button, create_line_edit, BaklavaLineEdit
from export_handler import ThreadedMixExporter
from globals import DEFAULT_BREAK_DURATION, BREAK_SAVE_STR, AUTOSCROLL_MARGIN
from mix_utility import MixUtility
from song_entry import SongEntry
from tracklist import Tracklist

HEADER_FONT_SIZE: int = 20

class MixView:
    name: str
    mix_util: MixUtility

    current_tracklist: Tracklist
    mix_name_line_edit: BaklavaLineEdit

    list_widget: QListWidget

    tab_index = -1

    is_queue: bool = False
    is_search: bool = False

    def __init__(self, mix_util, mix_path: Path | None = None, parent=None, is_queue: bool = False, is_search: bool=True):
        self.is_queue = is_queue
        self.is_search = is_search
        self.mix_util = mix_util
        self.update_name(self.mix_util.get_first_available_default_mix_name() if mix_path is None else mix_path.stem)
        self.initialize_gui(parent=parent)
        self.current_tracklist = Tracklist(list_widget=self.list_widget)

        if mix_path is not None and mix_path.is_file():
            mix_path = Path(mix_path)
            self.load_mix(loaded_mix_path=mix_path)

    def load_songs(self, song_names):
        for line in song_names:
            if line.split(" ")[0] == BREAK_SAVE_STR:
                duration = int(line.split(" ")[1])
                self.add_break(duration=duration)
            else:
                processed_line = line.strip()

                closest_track_filepath = None
                best_match = 0

                for track_name, mp3 in self.mix_util.music_library.items():
                    match_ratio = SequenceMatcher(None, track_name, processed_line).ratio()

                    if match_ratio > best_match:
                        best_match = match_ratio
                        closest_track_filepath = mp3.filename

                if closest_track_filepath is not None:
                    self.add_song_to_mix(closest_track_filepath)

    def load_mix(self, loaded_mix_path: Path):
        if loaded_mix_path.is_file():
            with open(loaded_mix_path, 'r', encoding="utf-8") as file:
                self.load_songs(song_names=file)
        elif loaded_mix_path.is_dir():
            mix_tracks = list(loaded_mix_path.rglob("*.mp3"))

            for filepath in mix_tracks:
                self.add_song_to_mix(filepath)

    def initialize_gui(self, parent=None):
        if parent is None:
            parent_widget = QWidget()
            vertical_layout = QVBoxLayout(parent_widget)

            self.mix_util.parent_tab_widget.addTab(parent_widget, self.name)
            self.tab_index = self.mix_util.parent_tab_widget.count() - 1

            self.mix_name_line_edit = (
                create_line_edit(
                    container=vertical_layout,
                    placeholder_text="Title",
                    default_value=self.name,
                    height=40,
                    font_size=HEADER_FONT_SIZE,
                    connect_to_method=self.update_name))
        else:
            vertical_layout = QVBoxLayout(parent)

        list_widget = QListWidget()
        list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        list_widget.setAutoScroll(True)
        list_widget.autoScrollMargin = AUTOSCROLL_MARGIN
        list_widget.setFlow(QListView.TopToBottom)
        list_widget.setWrapping(False)
        list_widget.setResizeMode(QListView.Adjust)
        list_widget.setMovement(QListView.Snap)
        list_widget.setIconSize(QSize(200,200))
        list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        list_model = list_widget.model()

        list_model.rowsMoved.connect(self.update_cumulative_times)

        vertical_layout.addWidget(list_widget)
        self.list_widget = list_widget

        if parent is None:
            hotbar = QHBoxLayout()
            height = 40

            create_button(container=hotbar, text="Add Song(s)", height=height, tooltip="Add one or more audio files", connect_to_method=lambda: self.add_song_to_mix())
            create_button(container=hotbar, text="Add Break", height=height, tooltip="Add a break (good for cassettes, CDs)", connect_to_method=self.add_break)

            vertical_layout.addLayout(hotbar)

    def update_name(self, new_name, set_line_edit_text: bool = False):
        self.name = new_name

        if set_line_edit_text:
            self.mix_name_line_edit.setText(new_name)

        if self.tab_index >= 0:
            self.mix_util.parent_tab_widget.setTabText(self.tab_index, new_name)

    def get_filename(self):
        return f"{self.name}.txt"

    def get_output_dir(self):
        return self.mix_util.mix_path / self.name

    def get_output_path(self):
        return self.mix_util.mix_path / self.get_filename()

    def add_song_to_mix(self, passed_path=None, index: int=-1):
        if passed_path is None:
            paths = self.mix_util.add_song_file_load_action.load_files(parent=self.mix_util.parent_window, caption="Select track(s)", directory=self.mix_util.search_path.as_posix(), file_filter="File (*.mp3);;")
        else:
            paths = [passed_path]

        if paths is None or len(paths) <= 0:
            return

        for path in paths:
            if Path(path).suffix != ".mp3":
                continue

            song_entry = (
                SongEntry(
                    filepath=Path(path),
                    mix_util=self.mix_util,
                    preview_transition_func=self.preview_transition_from,
                    delete_selected_items_and=self.delete_selected_items_and,
                    queue_method=self.queue_selected_songs_and,
                    queue_next_method=self.queue_selected_songs_next_and,
                    in_queue=self.is_queue,
                    in_search=self.is_search)
            )

            if index < 0 or index >= self.current_tracklist.length():
                self.list_widget.addItem(song_entry.list_widget_item)
            else:
                self.list_widget.insertItem(index, song_entry.list_widget_item)

            self.current_tracklist.widgets_to_song_entries[song_entry.widget] = song_entry

            self.list_widget.setItemWidget(song_entry.list_widget_item, song_entry.widget)

        self.update_cumulative_times()

    def queue_selected_songs_and(self, append_filepath):
        selected_filepaths_and_this = self.get_selected_filepaths_and(append_filepath)
        self.mix_util.song_queue.queue_song(selected_filepaths_and_this)

    def queue_selected_songs_next_and(self, append_filepath):
        selected_filepaths_and_this = self.get_selected_filepaths_and(append_filepath)
        self.mix_util.song_queue.queue_song_next(selected_filepaths_and_this)

    def delete_selected_items_and(self, append_item: QListWidgetItem | None=None):
        items_to_delete = self.get_selected_list_widget_items(append_item=append_item)

        for list_widget_item in items_to_delete:
            self.current_tracklist.delete_list_widget_item_entry(list_widget_item)

        self.update_cumulative_times()

    def add_break(self, duration: int=DEFAULT_BREAK_DURATION):
        song_entry = SongEntry(filepath=None, mix_util=self.mix_util, break_duration=duration, delete_selected_items_and=self.delete_selected_items_and)
        self.current_tracklist.widgets_to_song_entries[song_entry.widget] = song_entry
        self.list_widget.addItem(song_entry.list_widget_item)
        self.list_widget.setItemWidget(song_entry.list_widget_item, song_entry.widget)

        self.update_cumulative_times()

    def update_cumulative_times(self):
        current_runtime: int = 0

        for i in range(self.list_widget.count()):
            song_entry = self.current_tracklist.get_song_entry_at_index(i)

            if song_entry is None:
                continue

            current_runtime += song_entry.length()
            song_entry.update_time_label(time=current_runtime)

    def preview_transition_from(self, list_widget_item: QListWidgetItem):
        index = self.list_widget.row(list_widget_item)

        from_track = self.current_tracklist.get_song_entry_at_index(index - 1) if index > 0 else None
        to_track = self.current_tracklist.get_song_entry_by_list_widget_item(list_widget_item)

        if from_track is None:
            return

        from_path = from_track.filepath
        to_path = to_track.filepath

        if not Path(from_path).exists():
            self.mix_util.show_status_bar_message(f"{from_path} doesn't exist")
        elif not Path(to_path).exists():
            self.mix_util.show_status_bar_message(f"{to_path} doesn't exist")

        self.mix_util.song_queue.preview(from_path, to_path)

    def save(self):
        if self.do_cancel_operation_via_duplicate_dialog():
            return

        output_mix_filepath = self.get_output_path()

        with open(output_mix_filepath, "w", encoding="utf-8") as file:
            for song_entry in self.current_tracklist.get_tracklist_as_list_of_song_entry():
                file.write(f"{song_entry.save_format()}\n")

        self.mix_util.show_status_bar_message(f"Saved {self.name} to {output_mix_filepath}")

    def export(self):
        if self.do_cancel_operation_via_duplicate_dialog():
            return

        ThreadedMixExporter(mix_view=self)

    def do_cancel_operation_via_duplicate_dialog(self):
        if self.name in self.mix_util.get_duplicate_mix_names():
            choice = QMessageBox.question(
                self.mix_util.parent_window,
                f"Export {self.name}",
                f"There is more than one mix named '{self.name}'. Are you sure you want to export this mix?",
                QMessageBox.Yes | QMessageBox.No)

            if choice == QMessageBox.Yes:
                return False
            else:
                return True

        return False

    def get_selected_list_widget_items(self, append_item: QListWidgetItem | None = None):
        selected_items = []
        selected_items.extend(self.list_widget.selectedItems())

        if append_item is not None and append_item not in selected_items:
            selected_items.append(append_item)

        return selected_items

    def get_selected_filepaths_and(self, append_filepath: Path | None = None):
        selected_items = self.get_selected_list_widget_items()

        selected_filepaths = []

        for list_widget_item in selected_items:
            song_entry = self.current_tracklist.get_song_entry_by_list_widget_item(list_widget_item)

            try:
                selected_filepaths.append(song_entry.filepath)
            except:
                pass

        if append_filepath not in selected_filepaths:
            selected_filepaths.append(append_filepath)

        return selected_filepaths

    def filter(self, search_terms, min_duration, max_duration, album, artist):
        tracklist = self.current_tracklist

        for list_widget_item in tracklist.get_list_of_list_widget_items():
            song_entry = tracklist.get_song_entry_by_list_widget_item(list_widget_item)

            hidden = False

            if song_entry.length() > max_duration or song_entry.length() < min_duration:
                hidden = True

            if not hidden:
                for term in search_terms:
                    if term.lower() not in song_entry.name().lower():
                        hidden = True
                        break

            if not hidden and album is not None:
                if song_entry.album is None:
                    hidden = True
                else:
                    hidden = album.lower() not in song_entry.album.lower()

            if not hidden and artist is not None:
                if song_entry.artist is None:
                    hidden = True
                else:
                    hidden = artist.lower() not in song_entry.artist.lower()

            list_widget_item.setHidden(hidden)

    def __str__(self):
        return f"MixView '{self.name}' tracklist: {self.current_tracklist}"