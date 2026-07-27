import shutil
import threading
from pathlib import Path

from PySide6.QtCore import Signal, QObject

from ffmparakeet import run_ffmpeg
from progress_bar_window import ProgressBarWindow

class ThreadedMixExporter(QObject):
    progress_signal: Signal = Signal(int)
    finished_signal: Signal = Signal()

    def __init__(self, mix_view):
        super().__init__()
        self.mix_view = mix_view

        progress_bar_window = ProgressBarWindow(parent=self.mix_view.mix_util.parent_window, mix_name=self.mix_view.name, size=len(self.mix_view.current_tracklist.items()))

        self.progress_signal.connect(progress_bar_window.update_progress)
        self.finished_signal.connect(progress_bar_window.finish)

        self.thread = threading.Thread(target=self._export, daemon=True)
        self.thread.start()

    def _export(self):
        output_mix_directory = self.mix_view.get_output_dir()

        if output_mix_directory.exists() and output_mix_directory.is_dir():
            shutil.rmtree(output_mix_directory)

        output_mix_directory.mkdir(parents=True, exist_ok=True)

        tracklist_iterable = self.mix_view.current_tracklist.items()

        i = 0
        for _, song_entry in tracklist_iterable:
            filepath = Path(song_entry.filepath).resolve()
            destination = output_mix_directory / f"{song_entry.name()}.mp3"
            run_ffmpeg(track_num=i + 1, album=self.mix_view.name, source=filepath, destination=destination)
            i += 1
            self.progress_signal.emit(i)

        self.mix_view.mix_util.show_status_bar_message(f"Copied {i} tracks to {output_mix_directory}")

        self.finished_signal.emit()