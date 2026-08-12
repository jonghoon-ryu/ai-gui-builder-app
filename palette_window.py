from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

WIDGET_KIND_MIME = "application/x-widget-kind"

# Half the palette's previous item width, and shared with the save buttons
# on the right so both columns read as the same width.
ITEM_WIDTH = 194


class DraggableMixin:
    """Starts a drag carrying this widget's kind when left-clicked.

    The palette instance itself is never moved (no removal on drop) —
    only its kind is sent, so the canvas creates a fresh copy.
    """

    widget_kind = ""

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(WIDGET_KIND_MIME, self.widget_kind.encode())
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.setHotSpot(event.pos())
            drag.exec(Qt.CopyAction)
            return
        super().mousePressEvent(event)


class DraggableComboBox(DraggableMixin, QComboBox):
    widget_kind = "combobox"


class DraggableButton(DraggableMixin, QPushButton):
    widget_kind = "button"


class DraggableLineEdit(DraggableMixin, QLineEdit):
    widget_kind = "lineedit"


class DraggableHLine(DraggableMixin, QFrame):
    widget_kind = "hline"


class DraggableVLine(DraggableMixin, QFrame):
    widget_kind = "vline"


class DraggableUrlBox(DraggableMixin, QLineEdit):
    widget_kind = "urlbox"


class DraggableDirBox(DraggableMixin, QLineEdit):
    widget_kind = "dirbox"


class DraggableRadioButton(DraggableMixin, QRadioButton):
    widget_kind = "radiobutton"


class PaletteWindow(QWidget):
    def __init__(self, canvas_window=None):
        super().__init__()
        self.setWindowTitle("위젯 팔레트")
        self._canvas_window = canvas_window

        root = QHBoxLayout(self)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        root.addLayout(layout)

        combo = DraggableComboBox()
        combo.addItems(["옵션 1", "옵션 2", "옵션 3"])
        combo.setFixedWidth(ITEM_WIDTH)

        button = DraggableButton("버튼")
        button.setFixedWidth(ITEM_WIDTH)

        line_edit = DraggableLineEdit()
        line_edit.setPlaceholderText("텍스트 입력")
        line_edit.setFixedWidth(ITEM_WIDTH)

        # Thicker than the line drawn on canvas (that size is set separately
        # in canvas_window.LINE_DEFAULT_SIZE) purely so there's enough area
        # here to click and start the drag - a 2px sliver is nearly
        # impossible to grab with a mouse.
        hline = DraggableHLine()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Plain)
        hline.setLineWidth(2)
        hline.setStyleSheet("color: #777777;")
        hline.setFixedHeight(16)
        hline.setFixedWidth(ITEM_WIDTH)

        vline = DraggableVLine()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Plain)
        vline.setLineWidth(2)
        vline.setStyleSheet("color: #777777;")
        vline.setFixedHeight(30)
        vline.setFixedWidth(16)

        url_box = DraggableUrlBox()
        url_box.setPlaceholderText("URL 입력")
        url_box.setFixedWidth(ITEM_WIDTH)

        dir_box = DraggableDirBox()
        dir_box.setPlaceholderText("디렉토리 경로 입력")
        dir_box.setFixedWidth(ITEM_WIDTH)

        radio_button = DraggableRadioButton("옵션")

        for index, (label_text, widget) in enumerate(
            [
                ("드롭박스", combo),
                ("누름 버튼", button),
                ("텍스트 박스", line_edit),
                ("URL 입력창", url_box),
                ("디렉토리 입력창", dir_box),
                ("라디오 버튼", radio_button),
                ("가로선", hline),
                ("세로선", vline),
            ]
        ):
            if index > 0:
                divider = QFrame()
                divider.setFrameShape(QFrame.HLine)
                divider.setFrameShadow(QFrame.Sunken)
                layout.addWidget(divider)
            title_label = QLabel(label_text)
            title_font = title_label.font()
            title_font.setBold(True)
            title_label.setFont(title_font)
            layout.addWidget(title_label)
            if widget is vline:
                layout.addWidget(widget, alignment=Qt.AlignHCenter)
            else:
                layout.addWidget(widget)

        layout.addStretch()

        vertical_divider = QFrame()
        vertical_divider.setFrameShape(QFrame.VLine)
        vertical_divider.setFrameShadow(QFrame.Sunken)
        root.addWidget(vertical_divider)

        save_col = QVBoxLayout()
        root.addLayout(save_col)

        save_col.addStretch()

        template_save_button = QPushButton("틀 저장")
        template_save_button.clicked.connect(self._on_template_save_clicked)
        template_save_button.setFixedWidth(ITEM_WIDTH)
        save_col.addWidget(template_save_button)

        save_col.addSpacing(30)

        standalone_save_button = QPushButton("실행 py 저장")
        standalone_save_button.clicked.connect(self._on_standalone_save_clicked)
        standalone_save_button.setFixedWidth(ITEM_WIDTH)
        save_col.addWidget(standalone_save_button)

        save_col.addSpacing(30)

        exe_save_button = QPushButton("standalone 실행 파일 저장")
        exe_save_button.clicked.connect(self._on_exe_save_clicked)
        exe_save_button.setFixedWidth(ITEM_WIDTH)
        save_col.addWidget(exe_save_button)
        self._exe_save_button = exe_save_button

        save_col.addStretch()

    def _on_template_save_clicked(self):
        if self._canvas_window is None:
            return
        self._canvas_window.save_template()

    def _on_standalone_save_clicked(self):
        if self._canvas_window is None:
            return
        self._canvas_window.export_dialog()

    def _on_exe_save_clicked(self):
        if self._canvas_window is None:
            return
        self._canvas_window.export_exe_dialog(self._exe_save_button)
