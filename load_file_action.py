import os
from collections import deque
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMenu
from baklava import is_null_or_whitespace

class FileLoadAction():
    """File load actions with a history"""
    file_history: deque = None
    dropdown_menu: QMenu = None

    action = None
    parent = None

    def __init__(self, menu, name, action, parent=None):
        self.file_history = deque()
        self.action = action

        self.dropdown_menu = menu.addMenu(name)
        self.dropdown_menu.setToolTipsVisible(True)
        self.update_file_history()

        self.parent = parent

    def append_to_history(self, path):
        """Appends a filepath to the history"""

        if not isinstance(path, Path):
            try:
                path = Path(path)
            except:
                return

        if path in self.file_history:
            self.file_history.remove(path)

        self.file_history.appendleft(path)

        while len(self.file_history) > 10:
            self.file_history.pop()

        self.update_file_history()

    def update_file_history(self):
        """Repopulates the dropdown menu with the current file history"""

        self.dropdown_menu.clear()

        if len(self.file_history) > 0:
            for file in self.file_history:
                entry_action = self.dropdown_menu.addAction(file.stem)
                entry_action.triggered.connect(lambda _, f=file: self.action(f))
        else:
            self.dropdown_menu.addAction("None")

    def load_files(self, parent=None, caption="Select a file", directory: str=os.getcwd(), file_filter="File (*.*);;", limit_to_single_file=False):
        """Loads one or more files and appends them to the history"""

        if not parent:
            parent = parent

        if limit_to_single_file:
            paths = QFileDialog.getOpenFileName(parent=parent, caption=caption, dir=directory, filter=file_filter)[0]
        else:
            paths = QFileDialog.getOpenFileNames(parent=parent, caption=caption, dir=directory, filter=file_filter)[0]

        if not is_null_or_whitespace(paths):
            if isinstance(paths, list):
                for path in paths:
                    self.append_to_history(path=path)
            else:
                self.append_to_history(path=paths)

        return paths

    def load_file(self, parent=None, caption="Select a file", directory: str=os.getcwd(), file_filter="File (*.*);;"):
        """Loads a single file and appends it to the history"""

        paths = self.load_files(parent=parent, caption=caption, directory=directory, file_filter=file_filter, limit_to_single_file=True)
        return paths if paths is not None else None