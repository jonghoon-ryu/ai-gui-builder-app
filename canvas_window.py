import json
import os

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFontDialog,
    QFrame,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QRubberBand,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from alarm_widget import AlarmClockPanel
from git_widget import GitPanel
from gvf_widget import FpgaAcquisitionPanel, FpgaLoadingPanel, GvfPanel
from window_status_widget import WindowStatusPanel
from behavior_dialog import BehaviorDialog
from code_binder import SIGNAL_BY_KIND, HandlerCompileError, bind_handler, compile_handler
from exporter import build_exe, export_to_file
from palette_window import WIDGET_KIND_MIME
from tab_bar import ColorTabBar

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "builder_state.json")
# Written every AUTOSAVE_INTERVAL_MS while the app runs, and deleted again on
# a clean shutdown (see CanvasWindow.closeEvent) - if this file is still
# around at the *next* startup, the previous run didn't exit cleanly (crash/
# force-kill), so its contents may be newer than the last real save.
AUTOSAVE_STATE_FILE = os.path.join(BASE_DIR, "builder_state.autosave.json")
AUTOSAVE_INTERVAL_MS = 90_000
EXECUTABLE_PY_DIR = os.path.join(BASE_DIR, "executable_py")
STANDALONE_DIR = os.path.join(BASE_DIR, "standalone")

# Module-level (not per-tab) so copy/paste also works across tabs.
_CLIPBOARD = []


def _widget_text(widget):
    """Reads the widget's *live* text (whatever the user actually typed,
    including leading/trailing spaces) rather than a separately tracked
    field that only updates via the rename dialog."""
    return widget.text() if hasattr(widget, "text") else None


def _apply_anchors(page):
    """Repositions (and, when both sides of an axis are anchored, resizes)
    widgets that declare an `anchor` (see the "anchor" key in a widget's
    saved JSON) so their left/right/top/bottom margin matches another
    widget's same-side margin - e.g. `{"right": "fpgaacq_1"}` keeps this
    widget's right margin equal to fpgaacq_1's right margin even after
    fpgaacq_1 is resized, instead of needing the x/y recomputed by hand every
    time (see md_files/future_work_for_poor_developer.md item 2). Only
    same-edge widget-to-widget anchors are supported (left-to-left,
    right-to-right, top-to-top, bottom-to-bottom) - this needs no knowledge
    of the page's own width/height, since that cancels out algebraically.
    If *both* "left" and "right" (or "top" and "bottom") are given, the
    widget's width (or height) is stretched to span exactly between the two
    referenced margins, rather than one side winning - this is the common
    case in this app (e.g. a bottom panel whose own left/right margins must
    match two different panels above it). Anchors are resolved in a single
    left-to-right pass over `page.entries` (dict insertion order, i.e. JSON
    declaration order) - if widget B anchors to widget A, A must be declared
    before B in the tab's widget list for B to see A's *anchor-resolved*
    position rather than its raw saved one (harmless in practice: A's raw
    and resolved position are the same unless A itself has an anchor)."""
    for widget_id, entry in page.entries.items():
        anchor = entry.get("anchor")
        if not anchor:
            continue
        widget = entry["widget"]
        x, y = widget.pos().x(), widget.pos().y()
        w, h = widget.width(), widget.height()

        left_ref = page.entries.get(anchor.get("left"))
        right_ref = page.entries.get(anchor.get("right"))
        if left_ref and right_ref:
            left_widget, right_widget = left_ref["widget"], right_ref["widget"]
            x = left_widget.pos().x()
            w = right_widget.pos().x() + right_widget.width() - x
        elif left_ref:
            x = left_ref["widget"].pos().x()
        elif right_ref:
            right_widget = right_ref["widget"]
            x = right_widget.pos().x() + right_widget.width() - w

        top_ref = page.entries.get(anchor.get("top"))
        bottom_ref = page.entries.get(anchor.get("bottom"))
        if top_ref and bottom_ref:
            top_widget, bottom_widget = top_ref["widget"], bottom_ref["widget"]
            y = top_widget.pos().y()
            h = bottom_widget.pos().y() + bottom_widget.height() - y
        elif top_ref:
            y = top_ref["widget"].pos().y()
        elif bottom_ref:
            bottom_widget = bottom_ref["widget"]
            y = bottom_widget.pos().y() + bottom_widget.height() - h

        widget.setGeometry(x, y, w, h)


def _apply_scoped_background(widget, color_hex):
    """Colors `widget`'s own background without leaking into any dialog a
    click handler might open on/under it. A bare `setStyleSheet("background-
    color: X")` is treated by Qt as `* { background-color: X }`, which
    cascades into descendants - including separate top-level windows like
    QDialog/QMessageBox, since Qt's stylesheet cascade follows the *widget*
    parent chain regardless of "is it its own window". Scoping by an
    id-selector (rather than a type-selector) additionally avoids the color
    leaking into same-type widgets nested *inside* such a dialog (e.g. a
    QPushButton "확인" button inside a popup opened from a colored
    QPushButton) - a type-selector rule would still match those."""
    object_name = widget.objectName() or f"w{id(widget)}"
    widget.setObjectName(object_name)
    widget.setStyleSheet(f"#{object_name} {{ background-color: {color_hex}; }}")


def _save_state(tabs_widget, window_size=None, target_file=None):
    target_file = target_file or STATE_FILE
    if window_size is None:
        # Preserve whatever window size was last saved instead of wiping it out.
        previous = _load_state()
        window_size = previous.get("window") if previous else None
    else:
        window_size = {"width": window_size[0], "height": window_size[1]}

    tab_bar = tabs_widget.tabBar()
    data = {
        "window": window_size,
        "tabs": [
            {
                "title": tabs_widget.tabText(i),
                "color": (
                    tab_bar.get_tab_color(i).name() if tab_bar.get_tab_color(i) else None
                ),
                "widgets": [
                    {
                        "id": widget_id,
                        "kind": entry["kind"],
                        "x": entry["widget"].pos().x(),
                        "y": entry["widget"].pos().y(),
                        "width": entry["widget"].width(),
                        "height": entry["widget"].height(),
                        "instruction": entry["instruction"],
                        "code": entry["code"],
                        "text": _widget_text(entry["widget"]),
                        "color": entry.get("color"),
                        "font_family": entry.get("font_family"),
                        "font_size": entry.get("font_size"),
                        "group": entry.get("group"),
                        "no_border": entry.get("no_border", False),
                        "anchor": entry.get("anchor"),
                        "checked": (
                            entry["widget"].isChecked() if entry["kind"] == "radiobutton" else None
                        ),
                    }
                    for widget_id, entry in tabs_widget.widget(i).entries.items()
                ],
            }
            for i in range(tabs_widget.count())
        ]
    }
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_state():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _check_and_offer_autosave_recovery():
    """Called once at startup, before the normal `_load_state()` restore
    path. A leftover autosave file means the previous run never reached
    `CanvasWindow.closeEvent` (crash / force-kill / power loss) - a clean
    exit always deletes it there. If it exists, ask whether to recover it;
    either way the stale file is removed afterward so this only ever fires
    once per unclean shutdown. Returns the recovered state dict, or None if
    there's nothing to recover (caller should fall back to `_load_state()`)."""
    if not os.path.exists(AUTOSAVE_STATE_FILE):
        return None

    try:
        with open(AUTOSAVE_STATE_FILE, "r", encoding="utf-8") as f:
            autosave_state = json.load(f)
    except (OSError, ValueError):
        autosave_state = None

    recovered = None
    if autosave_state and autosave_state.get("tabs"):
        reply = QMessageBox.question(
            None,
            "이전 작업 복구",
            "이전 실행이 정상적으로 종료되지 않았습니다.\n"
            "자동 저장된 마지막 작업 내용을 복구할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            recovered = autosave_state

    try:
        os.remove(AUTOSAVE_STATE_FILE)
    except OSError:
        pass
    return recovered


def get_saved_window_size():
    """Returns (width_px, height_px) last saved for the '나만의 tool' window,
    or None if nothing has been saved yet."""
    state = _load_state()
    window = state.get("window") if state else None
    if not window:
        return None
    return window.get("width"), window.get("height")


def _make_combobox(parent):
    combo = QComboBox(parent)
    combo.addItems(["옵션 1", "옵션 2", "옵션 3"])
    return combo


def _make_line(parent, shape):
    line = QFrame(parent)
    line.setFrameShape(shape)
    line.setFrameShadow(QFrame.Shadow.Plain)
    line.setLineWidth(2)
    line.setStyleSheet("color: #777777;")
    return line


def _make_placeholder_lineedit(parent, placeholder):
    edit = QLineEdit(parent)
    edit.setPlaceholderText(placeholder)
    return edit


def _browse_directory(line_edit):
    directory = QFileDialog.getExistingDirectory(
        line_edit, "디렉토리 선택", line_edit.text(),
    )
    if directory:
        line_edit.setText(directory)


def _make_dirbox(parent):
    """A text box with a clickable folder icon built into its trailing edge
    (Qt's native QLineEdit action mechanism) so choosing a directory is a
    literal one-button click, not buried in a right-click menu."""
    edit = _make_placeholder_lineedit(parent, DIR_PLACEHOLDER)
    icon = edit.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
    action = edit.addAction(icon, QLineEdit.ActionPosition.TrailingPosition)
    action.setToolTip("디렉토리 선택")
    action.triggered.connect(lambda: _browse_directory(edit))
    return edit


def _prompt_url(line_edit):
    text, ok = QInputDialog.getText(
        line_edit, "URL 입력", "URL:", QLineEdit.EchoMode.Normal, line_edit.text()
    )
    if ok and text:
        line_edit.setText(text)


def _make_urlbox(parent):
    """A text box with a clickable icon in its trailing edge that pops up a
    small dialog for typing the URL, in addition to typing directly into
    the box itself."""
    edit = _make_placeholder_lineedit(parent, URL_PLACEHOLDER)
    icon = edit.style().standardIcon(QStyle.StandardPixmap.SP_DirLinkIcon)
    action = edit.addAction(icon, QLineEdit.ActionPosition.TrailingPosition)
    action.setToolTip("URL 입력")
    action.triggered.connect(lambda: _prompt_url(edit))
    return edit


# Per-kind default size for widgets whose natural adjustSize() result isn't
# a good starting point (thin lines, the alarm clock panel).
LINE_DEFAULT_SIZE = {
    "hline": (100, 36),
    "vline": (36, 100),
    "alarmclock": (1000, 640),
    "windowstatus": (760, 400),
    "gitpanel": (800, 630),
    "gvfpanel": (460, 200),
    "fpgaacquisition": (360, 250),
    "fpgaloading": (630, 120),
}
URL_PLACEHOLDER = "URL 입력 (https://...)"
DIR_PLACEHOLDER = "디렉토리 경로 입력"

WIDGET_FACTORIES = {
    "combobox": _make_combobox,
    "button": lambda parent: QPushButton("버튼", parent),
    "lineedit": lambda parent: QLineEdit(parent),
    "hline": lambda parent: _make_line(parent, QFrame.Shape.HLine),
    "vline": lambda parent: _make_line(parent, QFrame.Shape.VLine),
    "urlbox": _make_urlbox,
    "dirbox": _make_dirbox,
    "radiobutton": lambda parent: QRadioButton("옵션", parent),
    "alarmclock": lambda parent: AlarmClockPanel(parent),
    "windowstatus": lambda parent: WindowStatusPanel(parent),
    "gitpanel": lambda parent: GitPanel(parent),
    "gvfpanel": lambda parent: GvfPanel(parent),
    "fpgaacquisition": lambda parent: FpgaAcquisitionPanel(parent),
    "fpgaloading": lambda parent: FpgaLoadingPanel(parent),
}

# Text-box-flavored kinds that share lineedit's behavior (font menu, etc.)
TEXTBOX_KINDS = ("lineedit", "urlbox", "dirbox")


class CanvasPage(QWidget):
    """Free-form drop surface. Dropped widgets are registered under a
    unique id (exposed both as a tooltip and as `self.<id>` on this page)
    so natural-language-generated handlers can reference each other."""

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        # Plain QWidget subclasses ignore stylesheet backgrounds unless this
        # is set, so the "바탕색" feature's background-color rule renders.
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._counters = {}
        self.entries = {}  # id -> {"widget", "kind", "instruction", "code", "handler"}
        self._drag_widget = None
        self._drag_start_global = None
        self._drag_start_widget_pos = None
        self._drag_moved = False
        self._resize_widget = None
        self._resize_mode = None
        self._resize_start_global = None
        self._resize_start_geom = None
        self._selected_ids = set()
        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self._rubber_band_origin = None
        self._radio_groups = {}  # group id -> QButtonGroup
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._selected_ids:
            return
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.blue)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)
        for widget_id in self._selected_ids:
            entry = self.entries.get(widget_id)
            if entry:
                painter.drawRect(entry["widget"].geometry().adjusted(-3, -3, 3, 3))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            self._selected_ids = set()
            self.update()
            self._rubber_band_origin = event.position().toPoint()
            self._rubber_band.setGeometry(QRect(self._rubber_band_origin, QSize()))
            self._rubber_band.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rubber_band_origin is not None:
            rect = QRect(self._rubber_band_origin, event.position().toPoint()).normalized()
            self._rubber_band.setGeometry(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._rubber_band_origin is not None:
            select_rect = self._rubber_band.geometry()
            self._rubber_band.hide()
            self._rubber_band_origin = None
            self._selected_ids = {
                widget_id
                for widget_id, entry in self.entries.items()
                if select_rect.intersects(entry["widget"].geometry())
            }
            self.update()
        super().mouseReleaseEvent(event)

    _ARROW_KEY_DELTAS = {
        Qt.Key.Key_Left: (-1, 0),
        Qt.Key.Key_Right: (1, 0),
        Qt.Key.Key_Up: (0, -1),
        Qt.Key.Key_Down: (0, 1),
    }
    _NUDGE_STEP = 1
    _NUDGE_STEP_SHIFT = 10

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and self._selected_ids:
            self._delete_selected_widgets()
            return
        if event.matches(QKeySequence.StandardKey.Copy):
            self._copy_selected_widgets()
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            self._paste_clipboard()
            return
        if event.key() in self._ARROW_KEY_DELTAS and self._selected_ids:
            self._nudge_selected_widgets(event.key(), event.modifiers())
            return
        super().keyPressEvent(event)

    def _nudge_selected_widgets(self, key, modifiers):
        """Moves every selected widget by 1px (Shift+arrow: 10px) - mouse
        drag alone can't reliably place a widget at an exact pixel, which
        kept forcing hand-edits of builder_state.json for precise layout
        work (see md_files/future_work_for_poor_developer.md item 4)."""
        dx, dy = self._ARROW_KEY_DELTAS[key]
        step = (
            self._NUDGE_STEP_SHIFT
            if modifiers & Qt.KeyboardModifier.ShiftModifier
            else self._NUDGE_STEP
        )
        for widget_id in self._selected_ids:
            entry = self.entries.get(widget_id)
            if entry is None:
                continue
            widget = entry["widget"]
            new_pos = widget.pos() + QPoint(dx * step, dy * step)
            max_x = max(0, self.width() - widget.width())
            max_y = max(0, self.height() - widget.height())
            new_pos.setX(min(max(0, new_pos.x()), max_x))
            new_pos.setY(min(max(0, new_pos.y()), max_y))
            widget.move(new_pos)
        self.update()

    def _delete_selected_widgets(self):
        for widget_id in list(self._selected_ids):
            self._remove_widget(widget_id)

    def _remove_widget(self, widget_id):
        entry = self.entries.pop(widget_id, None)
        if entry is None:
            return
        if entry["kind"] == "radiobutton":
            button_group = self._radio_groups.get(entry.get("group"))
            if button_group is not None:
                button_group.removeButton(entry["widget"])
        entry["widget"].deleteLater()
        if hasattr(self, widget_id):
            delattr(self, widget_id)
        self._selected_ids.discard(widget_id)
        self.update()

    def _copy_selected_widgets(self):
        global _CLIPBOARD
        if not self._selected_ids:
            return

        clipboard = []
        for widget_id in self._selected_ids:
            entry = self.entries.get(widget_id)
            if entry is None:
                continue
            widget = entry["widget"]
            clipboard.append(
                {
                    "kind": entry["kind"],
                    "x": widget.pos().x(),
                    "y": widget.pos().y(),
                    "width": widget.width(),
                    "height": widget.height(),
                    "instruction": entry["instruction"],
                    "code": entry["code"],
                    "text": _widget_text(widget),
                    "color": entry.get("color"),
                    "font_family": entry.get("font_family"),
                    "font_size": entry.get("font_size"),
                    "group": entry.get("group"),
                    "no_border": entry.get("no_border", False),
                    "checked": (widget.isChecked() if entry["kind"] == "radiobutton" else None),
                }
            )
        _CLIPBOARD = clipboard

    _PASTE_OFFSET = 20

    def _paste_clipboard(self):
        if not _CLIPBOARD:
            return

        pasted_ids = set()
        for data in _CLIPBOARD:
            widget_id = self._next_id(data["kind"])
            self._create_widget(
                data["kind"],
                widget_id,
                data["x"] + self._PASTE_OFFSET,
                data["y"] + self._PASTE_OFFSET,
                data["instruction"],
                data["code"],
                data["text"],
                data["color"],
                data["width"],
                data["height"],
                data.get("font_family"),
                data.get("font_size"),
                data.get("group"),
                data.get("no_border", False),
                data.get("checked"),
            )
            pasted_ids.add(widget_id)

        self._selected_ids = pasted_ids
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(WIDGET_KIND_MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(WIDGET_KIND_MIME):
            event.acceptProposedAction()

    def dropEvent(self, event):
        kind = bytes(event.mimeData().data(WIDGET_KIND_MIME)).decode()
        if kind not in WIDGET_FACTORIES:
            return

        widget_id = self._next_id(kind)
        pos = event.position().toPoint()
        self._create_widget(kind, widget_id, pos.x(), pos.y())
        event.acceptProposedAction()

    def _next_id(self, kind):
        self._counters[kind] = self._counters.get(kind, 0) + 1
        return f"{kind}_{self._counters[kind]}"

    def _create_widget(
        self, kind, widget_id, x, y, instruction="", code="", text=None, color=None,
        width=None, height=None, font_family=None, font_size=None, group=None,
        no_border=False, checked=None, anchor=None,
    ):
        widget = WIDGET_FACTORIES[kind](self)
        widget.setToolTip(widget_id)
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, wid=widget_id: self._open_widget_context_menu(wid, pos)
        )
        widget.setMouseTracking(True)
        widget.installEventFilter(self)

        if kind == "radiobutton":
            # Qt's default auto-exclusive behavior treats *every* radio
            # button under the same parent as one big group; explicit
            # QButtonGroups let multiple independent groups share a page.
            group = group or widget_id
            widget.setAutoExclusive(False)
            button_group = self._radio_groups.setdefault(group, QButtonGroup(self))
            button_group.addButton(widget)
            if checked is not None:
                # Explicit saved/copied selection state takes precedence.
                widget.setChecked(checked)
            elif len(button_group.buttons()) == 1:
                # First member of a brand-new group - make it the default
                # selection so the group never starts empty.
                widget.setChecked(True)

        setattr(self, widget_id, widget)
        self.entries[widget_id] = {
            "widget": widget,
            "kind": kind,
            "instruction": instruction,
            "code": code,
            "handler": None,
            "text": text,
            "color": color,
            "font_family": font_family,
            "font_size": font_size,
            "group": group,
            "no_border": no_border,
            "anchor": anchor,
        }

        if text is not None and hasattr(widget, "setText"):
            widget.setText(text)
        if color:
            widget.setAttribute(Qt.WA_StyledBackground, True)
            _apply_scoped_background(widget, color)
        if font_family or font_size:
            font = widget.font()
            if font_family:
                font.setFamily(font_family)
            if font_size:
                font.setPointSize(font_size)
            widget.setFont(font)
        if no_border and hasattr(widget, "setFrame"):
            widget.setFrame(False)

        widget.adjustSize()
        if width and height:
            widget.resize(width, height)
        elif kind in LINE_DEFAULT_SIZE:
            widget.resize(*LINE_DEFAULT_SIZE[kind])
        widget.move(x, y)
        widget.show()

        if code:
            try:
                bound_handler = compile_handler(code, self)
                bind_handler(widget, kind, bound_handler, None)
                self.entries[widget_id]["handler"] = bound_handler
            except HandlerCompileError:
                pass

        return widget

    def restore_widget(
        self, kind, widget_id, x, y, instruction, code, text=None, color=None,
        width=None, height=None, font_family=None, font_size=None, group=None,
        no_border=False, checked=None, anchor=None,
    ):
        """Recreates a widget saved by a previous session, keeping the id
        counter ahead of it so newly dropped widgets don't collide."""
        suffix = widget_id.rsplit("_", 1)[-1]
        if suffix.isdigit():
            self._counters[kind] = max(self._counters.get(kind, 0), int(suffix))
        self._create_widget(
            kind, widget_id, x, y, instruction, code, text, color, width, height,
            font_family, font_size, group, no_border, checked, anchor,
        )

    _DRAG_THRESHOLD = 4
    _RESIZE_MARGIN = 6
    _MIN_SIZE = 20

    def eventFilter(self, obj, event):
        """Lets a placed widget be repositioned by dragging its interior, or
        resized by dragging within a few pixels of one of its edges/corners
        - while still allowing a plain click/tap to reach the widget
        normally (button click, combobox open, text focus...)."""
        event_type = event.type()

        if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            mode = self._resize_mode_at(obj, event.position().toPoint())
            if mode:
                self._resize_widget = obj
                self._resize_mode = mode
                self._resize_start_global = event.globalPosition().toPoint()
                self._resize_start_geom = obj.geometry()
                return True

            self._drag_widget = obj
            self._drag_start_global = event.globalPosition().toPoint()
            self._drag_start_widget_pos = obj.pos()
            self._drag_moved = False
            return False

        if event_type == QEvent.Type.MouseMove:
            if obj is self._resize_widget:
                if not (event.buttons() & Qt.MouseButton.LeftButton):
                    return False
                self._apply_resize(obj, event.globalPosition().toPoint())
                return True

            if obj is self._drag_widget:
                if not (event.buttons() & Qt.MouseButton.LeftButton):
                    return False
                delta = event.globalPosition().toPoint() - self._drag_start_global
                if not self._drag_moved and delta.manhattanLength() < self._DRAG_THRESHOLD:
                    return False
                self._drag_moved = True

                new_pos = self._drag_start_widget_pos + delta
                max_x = max(0, self.width() - obj.width())
                max_y = max(0, self.height() - obj.height())
                new_pos.setX(min(max(0, new_pos.x()), max_x))
                new_pos.setY(min(max(0, new_pos.y()), max_y))
                obj.move(new_pos)
                return True

            if self._resize_widget is None and self._drag_widget is None:
                mode = self._resize_mode_at(obj, event.position().toPoint())
                obj.setCursor(self._cursor_for_mode(mode))
            return False

        if event_type == QEvent.Type.MouseButtonRelease:
            if obj is self._resize_widget:
                self._resize_widget = None
                self._resize_mode = None
                self._resize_start_global = None
                self._resize_start_geom = None
                return True

            if obj is self._drag_widget:
                was_dragged = self._drag_moved
                self._drag_widget = None
                self._drag_start_global = None
                self._drag_start_widget_pos = None
                self._drag_moved = False
                return was_dragged

        if event_type == QEvent.Type.Leave and obj is not self._resize_widget and obj is not self._drag_widget:
            obj.unsetCursor()

        return False

    def _resize_mode_at(self, widget, local_pos):
        margin = self._RESIZE_MARGIN
        w, h = widget.width(), widget.height()
        kind = self.entries.get(widget.toolTip(), {}).get("kind")

        # Lines are thin along one axis by design - only their length
        # (the other axis) should be resizable, not their thickness.
        left = right = top = bottom = False
        if kind != "vline":
            left = local_pos.x() <= margin
            right = local_pos.x() >= w - margin
        if kind != "hline":
            top = local_pos.y() <= margin
            bottom = local_pos.y() >= h - margin

        if not (left or right or top or bottom):
            return None

        vertical = "top" if top else "bottom" if bottom else ""
        horizontal = "left" if left else "right" if right else ""
        return "_".join(part for part in (vertical, horizontal) if part) or None

    def _cursor_for_mode(self, mode):
        return {
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top_left": Qt.CursorShape.SizeFDiagCursor,
            "bottom_right": Qt.CursorShape.SizeFDiagCursor,
            "top_right": Qt.CursorShape.SizeBDiagCursor,
            "bottom_left": Qt.CursorShape.SizeBDiagCursor,
        }.get(mode, Qt.CursorShape.ArrowCursor)

    def _apply_resize(self, widget, current_global):
        delta = current_global - self._resize_start_global
        geom = self._resize_start_geom
        mode = self._resize_mode

        new_x, new_y, new_w, new_h = geom.x(), geom.y(), geom.width(), geom.height()

        if "right" in mode:
            new_w = max(self._MIN_SIZE, geom.width() + delta.x())
        if "left" in mode:
            new_w = max(self._MIN_SIZE, geom.width() - delta.x())
            new_x = geom.x() + (geom.width() - new_w)
        if "bottom" in mode:
            new_h = max(self._MIN_SIZE, geom.height() + delta.y())
        if "top" in mode:
            new_h = max(self._MIN_SIZE, geom.height() - delta.y())
            new_y = geom.y() + (geom.height() - new_h)

        new_x = min(max(0, new_x), max(0, self.width() - self._MIN_SIZE))
        new_y = min(max(0, new_y), max(0, self.height() - self._MIN_SIZE))
        widget.setGeometry(new_x, new_y, new_w, new_h)

    def _open_behavior_dialog(self, widget_id):
        entry = self.entries.get(widget_id)
        if entry is None:
            return

        all_widgets = [(wid, e["kind"]) for wid, e in self.entries.items()]

        dialog = BehaviorDialog(
            widget_id=widget_id,
            widget_kind=entry["kind"],
            all_widgets=all_widgets,
            existing_instruction=entry["instruction"],
            existing_code=entry["code"],
            parent=self.window(),
        )
        if dialog.exec() != QDialog.Accepted:
            return

        try:
            bound_handler = compile_handler(dialog.result_code, self)
            bind_handler(entry["widget"], entry["kind"], bound_handler, entry["handler"])
        except HandlerCompileError as exc:
            QMessageBox.critical(self, "코드 오류", str(exc))
            return

        entry["instruction"] = dialog.instruction_text
        entry["code"] = dialog.result_code
        entry["handler"] = bound_handler

        QMessageBox.information(
            self, "연결됨", f"'{widget_id}'에 동작이 연결되었습니다. 이제 클릭하면 실행됩니다."
        )

    def _open_widget_context_menu(self, widget_id, pos):
        entry = self.entries.get(widget_id)
        if entry is None:
            return
        widget = entry["widget"]

        menu = QMenu(self)
        id_action = menu.addAction(f"ID: {widget_id}")
        id_action.setEnabled(False)
        menu.addSeparator()

        behavior_action = (
            menu.addAction("동작 설정...") if entry["kind"] in SIGNAL_BY_KIND else None
        )
        color_action = menu.addAction("색깔 변경")
        rename_action = menu.addAction("이름 변경") if hasattr(widget, "setText") else None
        font_action = menu.addAction("폰트 설정") if entry["kind"] in TEXTBOX_KINDS else None
        no_border_action = (
            menu.addAction("테두리 없애기") if entry["kind"] in TEXTBOX_KINDS else None
        )
        add_option_action = (
            menu.addAction("옵션 추가") if entry["kind"] == "radiobutton" else None
        )
        remove_option_action = (
            menu.addAction("옵션 제거") if entry["kind"] == "radiobutton" else None
        )

        chosen = menu.exec(widget.mapToGlobal(pos))
        if behavior_action is not None and chosen == behavior_action:
            self._open_behavior_dialog(widget_id)
        elif chosen == color_action:
            self._pick_widget_color(widget_id)
        elif rename_action is not None and chosen == rename_action:
            self._rename_widget(widget_id)
        elif font_action is not None and chosen == font_action:
            self._pick_widget_font(widget_id)
        elif no_border_action is not None and chosen == no_border_action:
            self._remove_widget_border(widget_id)
        elif add_option_action is not None and chosen == add_option_action:
            self._add_radio_option(widget_id)
        elif remove_option_action is not None and chosen == remove_option_action:
            self._remove_widget(widget_id)

    def _pick_widget_color(self, widget_id):
        entry = self.entries.get(widget_id)
        if entry is None:
            return
        widget = entry["widget"]

        color = QColorDialog.getColor(
            widget.palette().color(widget.backgroundRole()), self, "색깔 선택"
        )
        if not color.isValid():
            return

        widget.setAttribute(Qt.WA_StyledBackground, True)
        _apply_scoped_background(widget, color.name())
        entry["color"] = color.name()

    def _rename_widget(self, widget_id):
        entry = self.entries.get(widget_id)
        if entry is None:
            return
        widget = entry["widget"]

        dialog = QDialog(self)
        dialog.setWindowTitle("이름 변경")
        layout = QVBoxLayout(dialog)
        line_edit = QLineEdit(widget.text())
        layout.addWidget(line_edit)

        buttons = QDialogButtonBox()
        buttons.addButton("Yes", QDialogButtonBox.AcceptRole)
        buttons.addButton("No", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        new_text = line_edit.text()
        if new_text.strip():
            widget.setText(new_text)
            widget.adjustSize()
            entry["text"] = new_text

    def _pick_widget_font(self, widget_id):
        entry = self.entries.get(widget_id)
        if entry is None:
            return
        widget = entry["widget"]

        font, ok = QFontDialog.getFont(widget.font(), self, "폰트 선택")
        if not ok:
            return

        widget.setFont(font)
        widget.adjustSize()
        entry["font_family"] = font.family()
        entry["font_size"] = font.pointSize()

    def _remove_widget_border(self, widget_id):
        entry = self.entries.get(widget_id)
        if entry is None:
            return
        widget = entry["widget"]
        if hasattr(widget, "setFrame"):
            widget.setFrame(False)
            entry["no_border"] = True

    def _add_radio_option(self, widget_id):
        entry = self.entries.get(widget_id)
        if entry is None:
            return
        widget = entry["widget"]

        new_id = self._next_id("radiobutton")
        suffix = new_id.rsplit("_", 1)[-1]
        x = widget.pos().x()
        y = widget.pos().y() + widget.height() + 5
        self._create_widget(
            "radiobutton", new_id, x, y, text=f"옵션 {suffix}", group=entry.get("group")
        )


class CanvasTabs(QTabWidget):
    """Tab strip for the canvas. Right-clicking the empty space to the right
    of the tabs adds a new tab; right-clicking an existing tab offers to
    delete it (at least one tab is always kept)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_counter = 0
        self.setTabBar(ColorTabBar())
        self.setStyleSheet("QTabWidget::pane { border: 0; }")
        self.setMovable(True)
        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._on_tab_context_menu)

        state = _check_and_offer_autosave_recovery() or _load_state()
        if state and state.get("tabs"):
            self._restore_from_state(state)
        else:
            self.add_new_tab()

    def _restore_from_state(self, state):
        for tab_data in state["tabs"]:
            page = CanvasPage()
            for w in tab_data.get("widgets", []):
                page.restore_widget(
                    w["kind"],
                    w["id"],
                    w["x"],
                    w["y"],
                    w.get("instruction", ""),
                    w.get("code", ""),
                    w.get("text"),
                    w.get("color"),
                    w.get("width"),
                    w.get("height"),
                    w.get("font_family"),
                    w.get("font_size"),
                    w.get("group"),
                    w.get("no_border", False),
                    w.get("checked"),
                    w.get("anchor"),
                )
            _apply_anchors(page)

            index = self.addTab(page, tab_data.get("title") or "tab")
            color_hex = tab_data.get("color")
            if color_hex:
                _apply_scoped_background(page, color_hex)
                self.tabBar().set_tab_color(index, QColor(color_hex))

            self._tab_counter += 1

        self.setCurrentIndex(0)

    def add_new_tab(self):
        self._tab_counter += 1
        page = CanvasPage()
        index = self.addTab(page, f"tab {self._tab_counter}")
        self.setCurrentIndex(index)
        return page

    def contextMenuEvent(self, event):
        bar = self.tabBar()
        if event.pos().y() <= bar.geometry().bottom() and event.pos().x() > bar.geometry().right():
            self.add_new_tab()

    def _on_tab_context_menu(self, pos):
        index = self.tabBar().tabAt(pos)
        if index == -1:
            self.add_new_tab()
            return

        menu = QMenu(self)
        delete_action = menu.addAction("delete")
        edit_title_action = menu.addAction("탭 제목 편집")
        bg_color_action = menu.addAction("바탕색")

        chosen = menu.exec(self.tabBar().mapToGlobal(pos))
        if chosen == delete_action:
            self._delete_tab(index)
        elif chosen == edit_title_action:
            self._edit_tab_title(index)
        elif chosen == bg_color_action:
            self._pick_tab_bg_color(index)

    def _delete_tab(self, index):
        if self.count() <= 1:
            QMessageBox.information(self, "탭 삭제", "마지막 탭은 삭제할 수 없습니다.")
            return

        reply = QMessageBox.question(
            self, "탭 삭제", "이 탭을 지울까요?", QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        widget = self.widget(index)
        self.removeTab(index)
        widget.deleteLater()
        self.tabBar().remove_tab_color(index)

    def _edit_tab_title(self, index):
        dialog = QDialog(self)
        dialog.setWindowTitle("탭 제목 편집")
        layout = QVBoxLayout(dialog)
        line_edit = QLineEdit(self.tabText(index))
        layout.addWidget(line_edit)

        buttons = QDialogButtonBox()
        buttons.addButton("Yes", QDialogButtonBox.AcceptRole)
        buttons.addButton("No", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        new_title = line_edit.text().strip()
        if new_title:
            self.setTabText(index, new_title)

    def _pick_tab_bg_color(self, index):
        page = self.widget(index)
        color = QColorDialog.getColor(
            page.palette().color(page.backgroundRole()), self, "바탕색 선택"
        )
        if not color.isValid():
            return

        _apply_scoped_background(page, color.name())
        self.tabBar().set_tab_color(index, color)


class _ExeBuildWorker(QThread):
    """Runs build_exe() off the UI thread - a PyInstaller build takes
    roughly 1-2 minutes, far too long to block the app on."""

    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, tabs_data, width, height, dest_path, parent=None):
        super().__init__(parent)
        self._tabs_data = tabs_data
        self._width = width
        self._height = height
        self._dest_path = dest_path

    def run(self):
        try:
            build_exe(self._tabs_data, self._width, self._height, self._dest_path)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(self._dest_path)


class CanvasWindow(QMainWindow):
    def __init__(self, width_px, height_px):
        super().__init__()
        self.setWindowTitle("나만의 tool")
        self.resize(width_px, height_px)

        self.tabs = CanvasTabs()
        self.setCentralWidget(self.tabs)

        # Crash/force-kill safety net - a clean exit already saves via
        # closeEvent below, so this is only ever actually needed once the
        # app *doesn't* reach that (see _check_and_offer_autosave_recovery).
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(AUTOSAVE_INTERVAL_MS)
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start()

    def _autosave(self):
        _save_state(
            self.tabs, window_size=(self.width(), self.height()), target_file=AUTOSAVE_STATE_FILE
        )

    def save_template(self):
        _save_state(self.tabs, window_size=(self.width(), self.height()))
        QMessageBox.information(
            self, "틀 저장 완료", f"지금까지 만든 탭/위젯 구성을 저장했습니다.\n({STATE_FILE})"
        )

    def closeEvent(self, event):
        _save_state(self.tabs, window_size=(self.width(), self.height()))
        # A clean shutdown makes the autosave file redundant (and, if left
        # behind, would wrongly look like a crash on the next launch).
        try:
            os.remove(AUTOSAVE_STATE_FILE)
        except OSError:
            pass
        super().closeEvent(event)

    def export_dialog(self):
        os.makedirs(EXECUTABLE_PY_DIR, exist_ok=True)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "독립 실행 앱으로 내보내기",
            os.path.join(EXECUTABLE_PY_DIR, "app.py"),
            "Python Files (*.py)",
        )
        if not file_path:
            return

        tab_bar = self.tabs.tabBar()
        tabs_data = [
            {
                "title": self.tabs.tabText(i),
                "color": (tab_bar.get_tab_color(i).name() if tab_bar.get_tab_color(i) else None),
                "entries": self.tabs.widget(i).entries,
            }
            for i in range(self.tabs.count())
        ]

        try:
            export_to_file(tabs_data, self.width(), self.height(), file_path)
        except Exception as exc:  # surfaced to the user, not swallowed
            QMessageBox.critical(self, "내보내기 실패", str(exc))
            return

        QMessageBox.information(
            self,
            "내보내기 완료",
            f"{file_path} 로 저장했습니다.\n"
            f"이제 이 빌더나 claude CLI 없이 `python {file_path}` 만으로 실행할 수 있습니다.",
        )

    def export_exe_dialog(self, trigger_button=None):
        os.makedirs(STANDALONE_DIR, exist_ok=True)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "독립 실행 파일(.exe)로 내보내기",
            os.path.join(STANDALONE_DIR, "ai_tools.exe"),
            "Executable Files (*.exe)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".exe"):
            file_path += ".exe"

        tab_bar = self.tabs.tabBar()
        tabs_data = [
            {
                "title": self.tabs.tabText(i),
                "color": (tab_bar.get_tab_color(i).name() if tab_bar.get_tab_color(i) else None),
                "entries": self.tabs.widget(i).entries,
            }
            for i in range(self.tabs.count())
        ]

        if trigger_button is not None:
            trigger_button.setEnabled(False)
            trigger_button.setText("빌드 중...")

        QMessageBox.information(
            self,
            "빌드 시작",
            "실행 파일 빌드를 시작합니다. 1~2분 정도 걸릴 수 있습니다.\n완료되면 알려드립니다.",
        )

        self._exe_build_worker = _ExeBuildWorker(
            tabs_data, self.width(), self.height(), file_path, self
        )
        self._exe_build_worker.succeeded.connect(
            lambda dest: self._on_exe_build_finished(trigger_button, dest_path=dest)
        )
        self._exe_build_worker.failed.connect(
            lambda message: self._on_exe_build_finished(trigger_button, error=message)
        )
        self._exe_build_worker.start()

    def _on_exe_build_finished(self, trigger_button, dest_path=None, error=None):
        if trigger_button is not None:
            trigger_button.setEnabled(True)
            trigger_button.setText("standalone 실행 파일 저장")
        if error is not None:
            QMessageBox.critical(self, "빌드 실패", error)
            return
        QMessageBox.information(self, "빌드 완료", f"{dest_path} 로 저장했습니다.")
