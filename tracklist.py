from collections import defaultdict
from PySide6.QtWidgets import QListWidgetItem, QWidget

from song_entry import SongEntry

class Tracklist:
    widgets_to_song_entries: defaultdict[QWidget, SongEntry]
    list_widget = None

    def __init__(self, list_widget):
        self.widgets_to_song_entries = defaultdict()
        self.list_widget = list_widget

    def get_song_entry_by_list_widget_item(self, list_widget_item: QListWidgetItem) -> SongEntry | None:
        widget = self.list_widget.itemWidget(list_widget_item)

        if self.widgets_to_song_entries.__contains__(widget):
            song_entry = self.widgets_to_song_entries[widget]
        else:
            return None

        return song_entry

    def get_song_entry_at_index(self, index: int) -> SongEntry | None:
        widget = self.get_widget_at_index(index)
        return self.get_song_entry_by_list_widget_item(widget) if widget is not None else None

    def get_widget_at_index(self, index: int) -> QListWidgetItem | None:
        if index >= self.length():
            return None

        list_widget_item = self.list_widget.item(index)
        return list_widget_item

    def get_index_of_widget(self, widget: QListWidgetItem) -> int:
        return self.list_widget.row(widget)

    def get_widget_after(self, widget: QListWidgetItem, offset: int = 1, loop: bool = False) -> QListWidgetItem | None:
        index = self.get_index_of_widget(widget)
        index += offset

        if (index >= self.length() or index < 0) and not loop:
            return None

        if loop:
            index = index % self.length()

        return self.get_widget_at_index(index)

    def delete_list_widget_item_entry(self, list_widget_item: QListWidgetItem):
        widget = self.list_widget.itemWidget(list_widget_item)
        self.widgets_to_song_entries.__delitem__(widget)
        row = self.get_index_of_widget(list_widget_item)
        self.list_widget.takeItem(row)

    def length(self) -> int:
        return len(self.widgets_to_song_entries.items())

    def get_list_of_list_widget_items(self):
        return [ self.list_widget.item(i) for i in range(0, self.list_widget.count()) ]

    def get_tracklist_as_list_of_song_entry(self):
        list_of_list_widget_item = self.get_list_of_list_widget_items()
        return [ self.widgets_to_song_entries[self.list_widget.itemWidget(list_widget_item)] for list_widget_item in list_of_list_widget_item]

    def get_tracklist_as_list_of_path(self):
        return [ song_entry.filepath for song_entry in self.get_tracklist_as_list_of_song_entry() ]

    def __str__(self):
        return ", ".join([song_entry.name() for song_entry in self.get_tracklist_as_list_of_song_entry()])