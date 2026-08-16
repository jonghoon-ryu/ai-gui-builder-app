from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QColor, QDrag, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from layout_templates import TEMPLATE_SPECS

WIDGET_KIND_MIME = "application/x-widget-kind"
# Carries a `layout_templates.TEMPLATE_SPECS` entry's "key" (plain utf-8
# string, not JSON) - the canvas looks the spec back up by key on drop
# (see canvas_window.py's `_drop_template`), so the drag payload itself
# stays as simple as the existing single-kind one.
WIDGET_TEMPLATE_MIME = "application/x-widget-template"

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


class DraggableCheckBox(DraggableMixin, QCheckBox):
    widget_kind = "checkbox"


class DraggableTemplate(QWidget):
    """A small preview thumbnail for one `layout_templates.TEMPLATE_SPECS`
    entry - dragging it onto the canvas drops that template's `rect_group`
    boxes all at once (see canvas_window.py's `_drop_template`). Not a
    `DraggableMixin` subclass since it carries a template *key* on the new
    `WIDGET_TEMPLATE_MIME` format rather than a single widget kind."""

    PREVIEW_HEIGHT = 90

    def __init__(self, spec, parent=None):
        super().__init__(parent)
        self._spec = spec
        self.setFixedSize(ITEM_WIDTH, self.PREVIEW_HEIGHT)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#5b72e0"), 2))
        painter.setBrush(QColor("#eef0fb"))
        for rect in self._spec["rects"]:
            x = round(rect["rel_x"] * self.width())
            y = round(rect["rel_y"] * self.height())
            w = round(rect["rel_w"] * self.width())
            h = round(rect["rel_h"] * self.height())
            painter.drawRect(x, y, w, h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(WIDGET_TEMPLATE_MIME, self._spec["key"].encode())
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.setHotSpot(event.pos())
            drag.exec(Qt.CopyAction)
            return
        super().mousePressEvent(event)


class PaletteWindow(QWidget):
    def __init__(self, canvas_window=None):
        super().__init__()
        self.setWindowTitle("위젯 팔레트")
        self._canvas_window = canvas_window

        root = QHBoxLayout(self)

        screen = QApplication.primaryScreen()
        max_column_height = (
            max(400, screen.availableGeometry().height() - 120) if screen is not None else None
        )

        def make_scrollable_column():
            """A vertically-scrollable column (own QScrollArea) - with 7
            template previews or 9 other widgets stacked in a single
            column, either one alone can comfortably exceed a typical
            screen's height, and the window has no explicit size of its own
            (main.py just calls .show()), so without this the window itself
            would grow taller than the screen (confirmed via screenshot
            while building this)."""
            container = QWidget()
            column_layout = QVBoxLayout(container)
            column_layout.setSpacing(16)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(container)
            if max_column_height is not None:
                scroll.setMaximumHeight(max_column_height)
            return scroll, column_layout

        def add_items(column_layout, items):
            for index, (label_text, widget) in enumerate(items):
                if index > 0:
                    divider = QFrame()
                    divider.setFrameShape(QFrame.HLine)
                    divider.setFrameShadow(QFrame.Sunken)
                    column_layout.addWidget(divider)
                title_label = QLabel(label_text)
                title_font = title_label.font()
                title_font.setBold(True)
                title_label.setFont(title_font)
                # Long template labels (e.g. "템플릿: 작은 사각형 2개 + 큰
                # 사각형 1개 (작은 것들이 위)") are wider than ITEM_WIDTH
                # without this - unwrapped, the label forces the column
                # wider than the window and a needless horizontal scrollbar
                # appears.
                title_label.setWordWrap(True)
                title_label.setFixedWidth(ITEM_WIDTH)
                column_layout.addWidget(title_label)
                if widget is vline:
                    column_layout.addWidget(widget, alignment=Qt.AlignHCenter)
                else:
                    column_layout.addWidget(widget)
            column_layout.addStretch()

        # Leftmost column: templates only. Middle column: every other
        # draggable widget. Rightmost: the existing save buttons (added
        # further below, unchanged) - three side-by-side groups as requested.
        template_scroll, template_layout = make_scrollable_column()
        root.addWidget(template_scroll)

        left_right_divider = QFrame()
        left_right_divider.setFrameShape(QFrame.VLine)
        left_right_divider.setFrameShadow(QFrame.Sunken)
        root.addWidget(left_right_divider)

        items_scroll, layout = make_scrollable_column()
        root.addWidget(items_scroll)

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

        checkbox = DraggableCheckBox("옵션")

        add_items(
            layout,
            [
                ("드롭박스", combo),
                ("누름 버튼", button),
                ("텍스트 박스", line_edit),
                ("URL 입력창", url_box),
                ("디렉토리 입력창", dir_box),
                ("라디오 버튼", radio_button),
                ("체크 박스", checkbox),
                ("가로선", hline),
                ("세로선", vline),
            ],
        )

        template_items = [
            ("템플릿: " + spec["label"], DraggableTemplate(spec)) for spec in TEMPLATE_SPECS
        ]
        add_items(template_layout, template_items)

        middle_right_divider = QFrame()
        middle_right_divider.setFrameShape(QFrame.VLine)
        middle_right_divider.setFrameShadow(QFrame.Sunken)
        root.addWidget(middle_right_divider)

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
