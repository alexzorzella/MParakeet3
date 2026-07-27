import random
from pathlib import Path

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QTabWidget, QInputDialog, QVBoxLayout

from baklava import set_tooltip, create_line_edit, time_int_to_str
from example_values import get_random_album_and_artist
from import_playlist import get_playlist_title_and_song_names
from mix_utility import MixUtility
from mix_view import MixView
from search_view import SearchView
from song_queue import SongQueue
from threaded_vlc_player import ThreadedVlcPlayer

class MixWindow(QMainWindow):
    mix_util: MixUtility

    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)

        self.mix_util = MixUtility(parent_window=self, show_status_bar_message=self.show_status_bar_message)

        self.create_window()
        self.load_mixes()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())

            if path.is_file():
                self.mix_util.currently_selected_mix_view().add_song_to_mix(passed_path=path)

    def create_window(self):
        self.setWindowTitle("Parakeet")
        self.resize(880, 660)

        self.populate_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        horizontal_layout = QHBoxLayout(central_widget)

        self.mix_util.parent_tab_widget = QTabWidget()
        self.mix_util.parent_tab_widget.setMovable(True)
        horizontal_layout.addWidget(self.mix_util.parent_tab_widget)
        self.mix_util.parent_tab_widget.currentChanged.connect(self.on_tab_changed)

        self.mix_util.player = ThreadedVlcPlayer()

        self.mix_util.queue_search_tabs = QTabWidget()
        horizontal_layout.addWidget(self.mix_util.queue_search_tabs)

        self.mix_util.song_queue = SongQueue(mix_util=self.mix_util, create_new_mix=self.create_new_mix)

        self.initialize_search_view()

    def populate_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        export_menu = menu_bar.addMenu("Export")
        mix_menu = menu_bar.addMenu("Mix")

        file_menu.setToolTipsVisible(True)
        export_menu.setToolTipsVisible(True)
        mix_menu.setToolTipsVisible(True)

        export_mix_as_file = file_menu.addAction("&Save")
        new_mix_action = file_menu.addAction("&New Mix")
        new_mix_action.triggered.connect(lambda: self.create_new_mix())
        load_mix_action = file_menu.addAction("&Load Mix")
        load_mix_action.triggered.connect(self.load_mix)
        export_mix_as_file.triggered.connect(self.export_tracklist_to_txt)
        export_mix_as_tracks = export_menu.addAction("As Ordered &Tracks")
        export_mix_as_tracks.triggered.connect(self.copy_mix_to_dir_as_ordered_tracks)

        import_mix_action = mix_menu.addAction("&Import")
        import_mix_action.triggered.connect(self.import_mix)
        add_song_action = mix_menu.addAction("&Add Song(s)")
        add_song_action.triggered.connect(self.add_song_to_currently_selected_mix)

        load_mix_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        load_mix_shortcut.activated.connect(self.load_mix)
        export_mix_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        export_mix_shortcut.activated.connect(self.export_tracklist_to_txt)
        export_mix_as_tracks_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        add_song_shortcut = QShortcut(QKeySequence("Ctrl+="), self)
        add_song_shortcut.activated.connect(self.add_song_to_currently_selected_mix)

        set_tooltip(widget=load_mix_action, text="Load a mix from a .txt file (Ctrl+L)")
        set_tooltip(widget=export_mix_as_file, text="Export a mix from as a .txt file (Ctrl+S)")
        set_tooltip(widget=export_mix_as_tracks, text="Export a mix as ordered audio file (Ctrl+E)")
        set_tooltip(widget=add_song_action, text="Add one or more tracks to the mix (Ctrl+=)")

    def import_mix(self):
        inputted_link = QInputDialog.getText(self, "Parakeet", "Playlist link:")[0]

        try:
            title, song_names = get_playlist_title_and_song_names(playlist_url=inputted_link)
            new_mix = self.create_new_mix()
            new_mix.update_name(new_name=title, set_line_edit_text=True)
            new_mix.load_songs(song_names=song_names)
        except Exception as e:
            print(e)

    def load_mixes(self):
        mixes = list(self.mix_util.mix_path.rglob("*.txt"))

        if len(mixes) <= 0:
            self.create_new_mix()
        else:
            mixes.reverse()
            for mix in mixes:
                self.create_new_mix(path=mix)
            self.mix_util.parent_tab_widget.setCurrentIndex(0)

    def currently_selected_mix(self):
        return self.mix_util.currently_selected_mix_view()

    def on_tab_changed(self, new_index):
        self.mix_util.currently_selected_tab = new_index

    def add_song_to_currently_selected_mix(self):
        self.currently_selected_mix().add_song_to_mix()

    def create_new_mix(self, path: Path | None = None, parent = None, is_queue: bool = False, is_search: bool = False):
        mix_view = MixView(mix_util=self.mix_util, mix_path=path, parent=parent, is_queue=is_queue, is_search=is_search)

        if parent is None:
            self.mix_util.mix_tab_views.append(mix_view)
            self.mix_util.parent_tab_widget.setCurrentIndex(self.mix_util.parent_tab_widget.count() - 1)

        return mix_view

    def load_mix(self):
        path = self.mix_util.add_song_file_load_action.load_file(parent=self, caption="Select mix", directory=self.mix_util.mix_path.as_posix(), file_filter="File (*.txt);;")

        if path is not None and len(path) > 0:
            mix_path = path
            print(f"Loading mix from {mix_path}")
            self.create_new_mix(path=Path(mix_path))

    def show_status_bar_message(self, message, time=12000):
        self.statusBar().showMessage(message, time)

    def copy_mix_to_dir_as_ordered_tracks(self):
        self.currently_selected_mix().export()

    def export_tracklist_to_txt(self):
        self.currently_selected_mix().save()

    def initialize_search_view(self):
        parent_layout = QVBoxLayout()

        mix_view_parent = QWidget()

        random_time_str = time_int_to_str(random.randint(100, 500), do_truncate=True)

        random_sign_before = ""
        random_sign_after = ""

        if random.randint(0, 1) == 0:
            random_sign_before = [">", "<"][random.randint(0, 1)]
        else:
            random_sign_after = [">", "<"][random.randint(0, 1)]

        random_album, random_artist = get_random_album_and_artist()
        search_field = create_line_edit(container=parent_layout, placeholder_text=f'Search songs and/or filter by length:"{random_sign_before}{random_time_str}{random_sign_after}", album:"{random_album}", and/or artist:"{random_artist}"', height=40)

        parent_layout.addWidget(mix_view_parent)

        search_window_mix_view = MixView(mix_util=self.mix_util, parent=mix_view_parent, is_search=True)
        self.mix_util.search_view = SearchView(mix_view=search_window_mix_view, mix_util=self.mix_util, parent_layout=parent_layout, search_field=search_field)

def main():
    app = QApplication()
    window = MixWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()