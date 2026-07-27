from PySide6.QtWidgets import QDialog, QProgressBar, QSizePolicy, QHBoxLayout

class ProgressBarWindow(QDialog):
    bar: QProgressBar

    def __init__(self, parent=None, mix_name: str = "", size: int = 0):
        super().__init__(parent)

        self.setWindowTitle(f"Exporting {mix_name}")
        self.setFixedSize(200, 40)

        horizontal_layout = QHBoxLayout(self)

        self.bar = QProgressBar()
        self.bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bar.setRange(0, size)

        horizontal_layout.addWidget(self.bar)

        self.show()

    def update_progress(self, i):
        self.bar.setValue(i)

    def finish(self):
        self.close()