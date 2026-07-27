import shlex
import sys
from datetime import datetime
import time
from enum import Enum
from pathlib import Path

from PySide6.QtGui import QPixmap, QIcon, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QSizePolicy, QLabel, QPushButton, QLineEdit, QPlainTextEdit, QScrollArea, QWidget, \
    QHBoxLayout, QVBoxLayout, QCheckBox
from PySide6.QtCore import Qt, Signal, QSize


class SizePolicy(Enum):
    FIXED = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    BOTH = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    HORIZONTAL = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    VERTICAL = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

def clear_contents_of(layout):
    """Clears the content of the passed layout"""

    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # If the item is a layout, recursively call this method
                # to clear its contents
                clear_contents_of(item.layout())

def create_label(container=None, text="", font_size=10, alignment=Qt.AlignLeft, tooltip="", font="", img_path: str | None=None,
                 img_width=-1, img_height=-1, img_color: str | None = None, font_weight: str | None = None, link: str | None = None, color: str | None = None) -> QLabel:
    """Creates a label under the passed container with the passed specifications"""

    label = QLabel(text)

    style_sheet = f"font-size: {font_size}pt;"

    if font_weight is not None:
        style_sheet += f" font-weight: {font_weight};"

    if color is not None:
        style_sheet += f" color: {color};"

    label.setStyleSheet(style_sheet)
    label.setAlignment(alignment)

    if img_path is not None:
        icon = svg(str(img_path), img_color if img_color is not None else "currentColor")
        label.setPixmap(icon.pixmap(QSize(img_width, img_height)))

    if not is_null_or_whitespace(font):
        label.setFont(font)

    if not is_null_or_whitespace(tooltip):
        set_tooltip(widget=label, text=tooltip, font_size=font_size)

    if container is not None:
        container.addWidget(label)

    if link is not None:
        label.setText(f'<a href="{link}">{text}</a>')
        # label.setText(f'<a href="{link}" style="color: blue;">{text}</a>')
        label.setOpenExternalLinks(True)

    return label

def create_button(container=None, text="", font_size=10, text_align="center", width=-1, height=-1, horizontal_padding=0,
                  vertical_padding=0, connect_to_method=None, is_checkbox=False, icon_path=None, icon_color=None, icon_size: QSize | None = None, tooltip=""):
    """Creates a button under the passed container with the passed specifications"""

    if not is_checkbox:
        button = QPushButton(text)
    else:
        button = QCheckBox()

    if width >= 0:
        button.setFixedWidth(width)

    if height >= 0:
        button.setFixedHeight(height)

    if not is_checkbox:
        button.setStyleSheet(f"font: {font_size}pt; "
                             f"text-align: {text_align}; "
                             f"padding-left: {horizontal_padding / 2}px; "
                             f"padding-right: {horizontal_padding / 2}px; "
                             f"padding-top: {vertical_padding / 2}px; "
                             f"padding-bottom: {vertical_padding / 2}px;")

    if container is not None:
        if container.layout():
            container.addWidget(button)
        elif container.widget():
            container.setWidget(button)

    if connect_to_method is not None:
        button.clicked.connect(connect_to_method)

    if icon_path is not None:
        button.setIcon(svg(str(icon_path), icon_color if icon_color is not None else "currentColor"))
        button.setIconSize(icon_size if icon_size is not None else button.sizeHint())

    if not is_null_or_whitespace(tooltip):
        set_tooltip(widget=button, text=tooltip)

    return button

def set_button_icon(button: QPushButton, icon_path: Path, color=None):
    button.setIcon(svg(str(icon_path), color if color is not None else "currentColor"))

def svg(path, color) -> QIcon:
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(24, 24)

    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)

    painter.setCompositionMode(
        painter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()

    return QIcon(pixmap)

def create_checkbox(container=None, default_value: bool | int = False, font_size=10, text_align="center", width=-1,
                    height=-1, horizontal_padding=0, vertical_padding=0, connect_to_method=None):
    """Creates a checkbox under the passed container with the passed specifications"""

    checkbox = create_button(
        container=container,
        font_size=font_size,
        text_align=text_align,
        width=width, height=height,
        horizontal_padding=horizontal_padding,
        vertical_padding=vertical_padding,
        connect_to_method=connect_to_method,
        is_checkbox=True)

    if isinstance(default_value, bool):
        checkbox.setChecked(default_value)
    elif isinstance(default_value, int):
        checkbox.setChecked(default_value != 0)

    parent = QWidget()
    parent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    layout = QHBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignCenter)
    layout.addWidget(checkbox)

    return parent

def create_line_edit(container=None, placeholder_text="", default_value="", read_only=False,
                     size_policy=SizePolicy.BOTH, width=-1, height=-1, connect_to_method=None, on_deselected=None,
                     input_hidden=False, alignment=None, font_size=None):
    """Creates a line input under the passed container with the passed specifications"""

    line_edit = BaklavaLineEdit()

    if width >= 0:
        line_edit.setFixedWidth(width)

    if height >= 0:
        line_edit.setFixedHeight(height)

    line_edit.setSizePolicy(size_policy.value)

    line_edit.setReadOnly(read_only)

    if read_only:
        line_edit.setEnabled(False)

    if container is not None:
        if container.layout():
            container.addWidget(line_edit)
        elif container.widget():
            container.setWidget(line_edit)

    if input_hidden:
        line_edit.setEchoMode(QLineEdit.Password)

    line_edit.setPlaceholderText(placeholder_text)
    if default_value != "":
        line_edit.setText(default_value)

    if connect_to_method is not None:
        line_edit.textChanged.connect(connect_to_method)

    if on_deselected is not None:
        line_edit.deselected.connect(on_deselected)

    if alignment is not None:
        line_edit.setAlignment(alignment)

    if font_size is not None:
        line_edit.setStyleSheet(f"font-size: {font_size}px")

    return line_edit

def create_plain_text_block(container=None, read_only=False, undo_redo_enabled=True, placeholder_text="", font=""):
    """Creates a plain text edit block under the passed container with the passed specifications"""

    text_block = QPlainTextEdit()

    text_block.setReadOnly(read_only)
    text_block.setUndoRedoEnabled(undo_redo_enabled)
    text_block.setPlaceholderText(placeholder_text)

    if not is_null_or_whitespace(font):
        text_block.setFont(font)

    if container is not None:
        if container.layout():
            container.addWidget(text_block)
        elif container.widget():
            container.setWidget(text_block)

    return text_block

def create_scroll_area(container=None, resizable=True, horizontal_layout=True, width=-1, height=-1):
    """Creates a scroll area under the passed container with the passed specifications"""

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(resizable)

    if width >= 0:
        scroll_area.setFixedWidth(width)

    if height >= 0:
        scroll_area.setFixedHeight(height)

    if container is not None:
        if container.layout():
            container.addWidget(scroll_area)
        elif container.widget():
            container.setWidget(scroll_area)

    content_parent_widget = QWidget()

    if horizontal_layout:
        register_contents = QHBoxLayout(content_parent_widget)
    else:
        register_contents = QVBoxLayout(content_parent_widget)

    scroll_area.setWidget(content_parent_widget)

    return register_contents, scroll_area

def create_dropdown(container=None, options: list[str] = None, default_option=None, default_index: int | None = None,
                    connect_to_method=None, scrollable=True):
    """Creates a dropdown under the passed container with the passed specifications"""

    if scrollable:
        dropdown = QComboBox()
    else:
        dropdown = BaklavaComboBox()

    if container is not None:
        if container.layout():
            container.addWidget(dropdown)
        elif container.widget():
            container.setWidget(dropdown)

    if options is not None:
        for option in options:
            dropdown.addItem(option)

        if default_option is not None:
            options_as_strings = [str(option) for option in options]
            if str(default_option) in options_as_strings:
                default_index = options_as_strings.index(str(default_option))

        if default_index is not None:
            dropdown.setCurrentIndex(default_index)

        if connect_to_method is not None:
            dropdown.activated.connect(connect_to_method)

    return dropdown

def set_tooltip(widget, text, font_size=10):
    """Sets the passed widget's tooltip to contain the passed contents. If a font size greater than zero was passed, the tooltip is set to be that font size"""

    if widget is None or is_null_or_whitespace(text):
        return

    if font_size > 0:
        widget.setToolTip(f"<span style='font-size:{font_size}pt;'>{text}</span>")
    else:
        widget.setToolTip(text)

def formatted_date(separator: str="/"):
    """Returns the time formatted as H:M:S"""

    result = datetime.now()
    result = result.strftime(f"%Y{separator}%m{separator}%d")
    return result

def formatted_time(separator: str=":"):
    """Returns the date formatted as Y/M/D"""

    result = datetime.now()
    result = result.strftime(f"%H{separator}%M{separator}%S")
    return result

def iso_datetime():
    return datetime.now().isoformat()

def formatted_datetime():
    """Returns the datetime formatted as Y/M/D H:M:S"""

    return f"{formatted_date()} {formatted_time()}"

def file_formatted_datetime():
    """Returns the datetime formatted as Y_M_D-H_M_S"""

    return f"{formatted_date(separator="_")}-{formatted_time(separator="_")}"

def sanitize_snake_cased_string(string: str) -> str:
    result = string.replace("_", " ").replace("-", " ")

    if len(result) > 3:
        result = result.title()

    return result

def is_null_or_whitespace(string):
    """Returns whether a string is null or whitespace. If the passed object isn't a string, it returns false"""

    if string is None:
        return True

    if not isinstance(string, str):
        return False

    result = False

    if string is None:
        return True

    try:
        result = not string.strip()
    except TypeError:
        print(f"Passed object {string} isn't a string")

    return result

def time_int_str_to_int(value) -> int:
    sections = value.split(':')
    sections.reverse()

    result: int = 0

    for i, section in enumerate(sections):
        local_value = section.strip().lower()

        try:
            result += int(local_value) * (pow(60, i) if i > 0 else 1)
        except:
            pass

    return result

def time_int_to_str(total_seconds: int, do_truncate: bool = False) -> str:
    if total_seconds < 60 * 60 and do_truncate:
        format = '%M:%S'
    else:
        format = '%H:%M:%S'

    return time.strftime(format, time.gmtime(total_seconds))

def int_str_to_int(value) -> int:
    if isinstance(value, int):
        return value

    if is_null_or_whitespace(value):
        return 0

    value = value.strip().lower()

    try:
        return int(value)
    except:
        pass

    return -1

def string_to_float(string):
    if string == "":
        return 0

    try:
        result = float(string)
    except ValueError:
        result = 0

    return result

def string_to_int(string):
    if string == "":
        return 0

    try:
        result = int(string)
    except ValueError:
        result = 0

    return result

def split_string_by_space_treating_text_wrapped_in_double_quotes_as_single_units(input: str) -> list[str]:
    try:
        return shlex.split(input)
    except:
        pass

    return input.split(" ")

def get_token_value(input: str, token: str) -> str:
    return input.split(f"{token}:")[1]

from PySide6.QtWidgets import QComboBox

class BaklavaComboBox(QComboBox):
    """Baklava combo boxes do not change their selection when scrolled over"""

    def wheelEvent(self, event):
        event.ignore()

class BaklavaLineEdit(QLineEdit):
    """Baklava line edits emit a signal when deselected"""

    deselected = Signal()
    ctrl_c_callback = None

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.deselected.emit()

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key.Key_C
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and self.ctrl_c_callback is not None
        ):
            self.ctrl_c_callback()
            event.accept()
            return

        super().keyPressEvent(event)

def resource_path(relative_path: str):
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).parent / relative_path