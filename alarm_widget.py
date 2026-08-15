import json
import os
import re
import shutil
import subprocess
import sys
import uuid

from PySide6.QtCore import QDate, QDateTime, Qt, QThread, QTime, QTimer, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

WEEKDAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
DEFAULT_ALARM_MESSAGE = "시간이 됐어요 !!"
CM_PER_INCH = 2.54
DEFAULT_DPI = 96

_CLAUDE_BIN = "claude"
_ALARM_PARSE_TIMEOUT_SECONDS = 60
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|```\s*$", re.MULTILINE)

# PyInstaller onefile builds unpack __file__ into a temp dir that's wiped
# after exit, so state saved there wouldn't survive a restart - save next to
# the actual .exe instead when frozen.
_STATE_DIR = (
    os.path.dirname(os.path.abspath(sys.executable))
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
# Saved data lives under an `appData/` subdirectory instead of directly next
# to the app, so a real install's own files don't get mixed in with its data.
_APP_DATA_DIR = os.path.join(_STATE_DIR, "appData")
ALARM_STATE_FILE = os.path.join(_APP_DATA_DIR, "alarm_state.json")
_LEGACY_ALARM_STATE_FILE = os.path.join(_STATE_DIR, "alarm_state.json")


def _migrate_legacy_alarm_state():
    """One-time move of a pre-appData/ alarm_state.json into appData/, so
    upgrading to this layout doesn't silently lose already-saved alarms."""
    if os.path.exists(ALARM_STATE_FILE) or not os.path.exists(_LEGACY_ALARM_STATE_FILE):
        return
    try:
        os.makedirs(_APP_DATA_DIR, exist_ok=True)
        shutil.move(_LEGACY_ALARM_STATE_FILE, ALARM_STATE_FILE)
    except OSError:
        pass


_migrate_legacy_alarm_state()


def _serialize_alarms(alarms):
    """Only alarms that can still fire in the future are worth persisting -
    a fired one-time alarm or a recurring alarm whose end date has already
    passed would just be dead weight in the save file."""
    today = QDate.currentDate()
    serialized = []
    for alarm in alarms:
        if alarm["type"] == "once":
            if alarm.get("fired"):
                continue
            serialized.append(
                {
                    "id": alarm["id"],
                    "type": "once",
                    "datetime": alarm["datetime"].toString(Qt.DateFormat.ISODate),
                    "message": alarm.get("message") or DEFAULT_ALARM_MESSAGE,
                    "enabled": alarm.get("enabled", True),
                }
            )
        else:
            if alarm["end_date"] < today:
                continue
            serialized.append(
                {
                    "id": alarm["id"],
                    "type": "recurring",
                    "start_date": alarm["start_date"].toString(Qt.DateFormat.ISODate),
                    "end_date": alarm["end_date"].toString(Qt.DateFormat.ISODate),
                    "weekdays": sorted(alarm["weekdays"]),
                    "time": alarm["time"].toString("HH:mm"),
                    "fired_dates": sorted(alarm["fired_dates"]),
                    "message": alarm.get("message") or DEFAULT_ALARM_MESSAGE,
                    "enabled": alarm.get("enabled", True),
                }
            )
    return serialized


def _deserialize_alarms(data):
    alarms = []
    for item in data:
        try:
            if item["type"] == "once":
                dt = QDateTime.fromString(item["datetime"], Qt.DateFormat.ISODate)
                if not dt.isValid():
                    continue
                alarms.append(
                    {
                        "id": item.get("id") or str(uuid.uuid4()),
                        "type": "once",
                        "datetime": dt,
                        "fired": False,
                        "message": item.get("message") or DEFAULT_ALARM_MESSAGE,
                        "enabled": item.get("enabled", True),
                    }
                )
            elif item["type"] == "recurring":
                start_date = QDate.fromString(item["start_date"], Qt.DateFormat.ISODate)
                end_date = QDate.fromString(item["end_date"], Qt.DateFormat.ISODate)
                time = QTime.fromString(item["time"], "HH:mm")
                if not (start_date.isValid() and end_date.isValid() and time.isValid()):
                    continue
                weekdays = [
                    d for d in item.get("weekdays", []) if isinstance(d, int) and 0 <= d <= 6
                ]
                if not weekdays:
                    continue
                alarms.append(
                    {
                        "id": item.get("id") or str(uuid.uuid4()),
                        "type": "recurring",
                        "start_date": start_date,
                        "end_date": end_date,
                        "weekdays": weekdays,
                        "time": time,
                        "fired_dates": set(item.get("fired_dates", [])),
                        "message": item.get("message") or DEFAULT_ALARM_MESSAGE,
                        "enabled": item.get("enabled", True),
                    }
                )
        except (KeyError, TypeError):
            continue
    return alarms


def _load_alarm_state():
    if not os.path.exists(ALARM_STATE_FILE):
        return []
    try:
        with open(ALARM_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return _deserialize_alarms(data)


def _save_alarm_state(alarms):
    try:
        os.makedirs(_APP_DATA_DIR, exist_ok=True)
        with open(ALARM_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(_serialize_alarms(alarms), f, ensure_ascii=False, indent=2)
    except OSError:
        pass

_ALARM_PARSE_SYSTEM_PROMPT = """\
당신은 사용자의 자연어 알람 설명을 구조화된 JSON으로 변환하는 어시스턴트입니다.
아래 두 형식 중 하나로만 응답하세요. 설명, 마크다운 코드펜스(```), 그 외 텍스트 없이 순수 JSON \
객체 하나만 출력하세요.

일회성 알람:
{"type": "once", "date": "YYYY-MM-DD", "time": "HH:MM", "message": "알람 메시지"}

주기적 알람:
{"type": "recurring", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "weekdays": [0, 2, 4], "time": "HH:MM", "message": "알람 메시지"}

규칙:
- weekdays는 0=월요일 ... 6=일요일 정수 목록입니다.
- "오늘", "내일", "다음 주 월요일", "매주 화/목" 등 상대적 표현은 함께 제공되는 현재 날짜/요일을 \
기준으로 계산하세요.
- 반복 종료일이 언급되지 않으면 시작일로부터 3개월 뒤를 end_date로 사용하세요.
- 알람 메시지가 명시되지 않으면 알람 내용에 어울리는 짧은 메시지를 직접 만들어 채우세요.
- 반드시 위 두 형식 중 하나에 맞는 JSON 객체 하나만 출력하세요.
"""


def _cm_to_px(cm):
    screen = QApplication.primaryScreen()
    dpi = screen.physicalDotsPerInchX() if screen else DEFAULT_DPI
    return round(cm * dpi / CM_PER_INCH)


CLAUDE_NOT_FOUND_MESSAGE = (
    "claude 명령을 찾을 수 없습니다.\n\n"
    "이 기능을 쓰려면 Claude Code(claude CLI)를 설치하고 로그인해야 합니다:\n\n"
    "  npm install -g @anthropic-ai/claude-code\n"
    "  claude login\n\n"
    "설치·로그인 후 claude를 실행할 수 있는 상태로 만들고 다시 시도하세요."
)


def _parse_alarm_with_claude(text, now):
    """Calls the locally installed `claude` CLI to turn a free-form alarm
    description into structured JSON (see _ALARM_PARSE_SYSTEM_PROMPT)."""
    weekday_name = WEEKDAY_NAMES[now.date().dayOfWeek() - 1]
    prompt = (
        f"현재 날짜/시각: {now.toString(Qt.DateFormat.ISODate)} ({weekday_name}요일)\n\n"
        f"사용자의 알람 설명: {text}"
    )
    try:
        result = subprocess.run(
            [
                _CLAUDE_BIN,
                "-p",
                "--output-format",
                "text",
                "--system-prompt",
                _ALARM_PARSE_SYSTEM_PROMPT,
                prompt,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_ALARM_PARSE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(CLAUDE_NOT_FOUND_MESSAGE) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("claude 응답이 시간 내에 오지 않았습니다.") from exc

    if result.returncode != 0:
        raise RuntimeError(f"claude 실행 오류:\n{result.stderr.strip()}")

    raw = _JSON_FENCE_RE.sub("", result.stdout).strip()
    if not raw:
        raise RuntimeError("claude가 빈 응답을 반환했습니다.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"claude 응답을 해석할 수 없습니다:\n{raw}") from exc


class _AlarmParseWorker(QThread):
    """Runs _parse_alarm_with_claude off the UI thread so the claude CLI
    round-trip doesn't freeze the window."""

    succeeded = Signal(dict)
    failed = Signal(str)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._text = text

    def run(self):
        try:
            data = _parse_alarm_with_claude(self._text, QDateTime.currentDateTime())
        except Exception as exc:  # surfaced via signal; UI stays responsive
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(data)


class _MultilineAlarmEdit(QTextEdit):
    """Multi-line box for the natural-language alarm description; Return
    inserts a newline as usual, Ctrl+Return submits."""

    submitted = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.submitted.emit()
            return
        super().keyPressEvent(event)


class AnalogClock(QWidget):
    """A live analog clock face, redrawn every second."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(1000)

    def paintEvent(self, event):
        side = min(self.width(), self.height())
        now = QTime.currentTime()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)

        painter.setPen(QPen(Qt.GlobalColor.darkGray, 3))
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(-95, -95, 190, 190)

        painter.setPen(QPen(Qt.GlobalColor.darkGray, 2))
        for i in range(12):
            painter.save()
            painter.rotate(i * 30.0)
            painter.drawLine(0, -85, 0, -95)
            painter.restore()

        hour_pen = QPen(Qt.GlobalColor.black, 5)
        hour_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.save()
        painter.rotate(30.0 * ((now.hour() % 12) + now.minute() / 60.0))
        painter.setPen(hour_pen)
        painter.drawLine(0, 8, 0, -45)
        painter.restore()

        minute_pen = QPen(Qt.GlobalColor.black, 3)
        minute_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.save()
        painter.rotate(6.0 * (now.minute() + now.second() / 60.0))
        painter.setPen(minute_pen)
        painter.drawLine(0, 10, 0, -68)
        painter.restore()

        second_pen = QPen(Qt.GlobalColor.red, 1)
        second_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.save()
        painter.rotate(6.0 * now.second())
        painter.setPen(second_pen)
        painter.drawLine(0, 12, 0, -78)
        painter.restore()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Qt.GlobalColor.darkGray)
        painter.drawEllipse(-4, -4, 8, 8)


class _AlarmPopup(QDialog):
    """A 20cm x 20cm square notification window shown when an alarm fires,
    displaying the message set when the alarm was created."""

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"⏰ {message}")
        side = _cm_to_px(20)
        self.setFixedSize(side, side)

        layout = QVBoxLayout(self)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_font = self.time_label.font()
        time_font.setPointSize(18)
        self.time_label.setFont(time_font)
        layout.addWidget(self.time_label)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(24)
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label, 1)

        close_button = QPushButton("확인")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self._update_time()
        self._time_timer = QTimer(self)
        self._time_timer.timeout.connect(self._update_time)
        self._time_timer.start(1000)

    def _update_time(self):
        self.time_label.setText(QTime.currentTime().toString("HH:mm:ss"))


class _DatePickerDialog(QDialog):
    def __init__(self, parent=None, title="날짜 선택"):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_date(self):
        return self.calendar.selectedDate()


class _TimePickerDialog(QDialog):
    """Picks the alarm time and, last in the flow, its popup message."""

    def __init__(self, parent=None, title="시간 선택"):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        self.time_edit = QTimeEdit(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        layout.addWidget(self.time_edit)

        layout.addWidget(QLabel("알람 메시지"))
        self.message_edit = QLineEdit(DEFAULT_ALARM_MESSAGE)
        layout.addWidget(self.message_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_time(self):
        return self.time_edit.time()

    def selected_message(self):
        text = self.message_edit.text().strip()
        return text if text else DEFAULT_ALARM_MESSAGE


class _RecurringRangeDialog(QDialog):
    """Picks the start/end date and which weekdays the alarm repeats on."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("주기적 알람 - 기간/요일 선택")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("시작 날짜"))
        self.start_edit = QDateEdit(QDate.currentDate())
        self.start_edit.setCalendarPopup(True)
        layout.addWidget(self.start_edit)

        layout.addWidget(QLabel("끝 날짜"))
        self.end_edit = QDateEdit(QDate.currentDate().addMonths(1))
        self.end_edit.setCalendarPopup(True)
        layout.addWidget(self.end_edit)

        layout.addWidget(QLabel("반복 요일"))
        day_row = QHBoxLayout()
        self.day_checks = []
        for name in WEEKDAY_NAMES:
            cb = QCheckBox(name)
            self.day_checks.append(cb)
            day_row.addWidget(cb)
        layout.addLayout(day_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_ok(self):
        if not any(cb.isChecked() for cb in self.day_checks):
            QMessageBox.information(self, "알림", "반복할 요일을 하나 이상 선택하세요.")
            return
        if self.end_edit.date() < self.start_edit.date():
            QMessageBox.information(self, "알림", "끝 날짜가 시작 날짜보다 빠릅니다.")
            return
        self.accept()

    def selected_range(self):
        weekdays = [i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
        return self.start_edit.date(), self.end_edit.date(), weekdays


class AlarmClockPanel(QWidget):
    """Self-contained alarm clock: add one-time/recurring alarms, see them
    listed with a live countdown, and an analog clock in the corner."""

    def __init__(self, parent=None, initial_alarms=None):
        super().__init__(parent)
        # `initial_alarms` (same shape as the JSON state file) lets the
        # standalone exporter seed this panel with whatever alarms existed
        # in the builder at export time. But once alarm_state.json actually
        # exists (created either by the builder or by a previous run of the
        # exported app), it is the source of truth - otherwise every restart
        # of the exported app would revert to the export-time snapshot baked
        # into its source, undoing anything added/removed since then.
        if os.path.exists(ALARM_STATE_FILE):
            self._alarms = _load_alarm_state()
        elif initial_alarms is not None:
            self._alarms = _deserialize_alarms(initial_alarms)
            _save_alarm_state(self._alarms)
        else:
            self._alarms = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(4)

        top_row = QHBoxLayout()
        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(6)
        self.add_once_button = QPushButton("일회성 알람 추가")
        self.add_once_button.clicked.connect(self._add_once_alarm)
        self.add_once_button.setMinimumHeight(44)
        self.add_recurring_button = QPushButton("주기적 알람 추가")
        self.add_recurring_button.clicked.connect(self._add_recurring_alarm)
        self.add_recurring_button.setMinimumHeight(44)
        buttons_col.addWidget(self.add_once_button)
        buttons_col.addSpacing(12)
        buttons_col.addWidget(self.add_recurring_button)
        buttons_col.addSpacing(12)

        self.nl_edit = _MultilineAlarmEdit()
        self.nl_edit.setPlaceholderText(
            "예: 내일 오전 9시에 회의 알람\n매주 화목 저녁 8시에 운동\n\n(Ctrl+Enter로 설정)"
        )
        self.nl_edit.setFixedWidth(190 + _cm_to_px(3) + 60)
        self.nl_edit.setFixedHeight(80)
        self.nl_edit.submitted.connect(self._add_alarm_from_text)
        buttons_col.addWidget(self.nl_edit)

        self.nl_add_button = QPushButton("자연어로 알람 설정")
        self.nl_add_button.clicked.connect(self._add_alarm_from_text)
        self.nl_add_button.setMinimumHeight(44)
        buttons_col.addWidget(self.nl_add_button)

        self.nl_status_label = QLabel("")
        buttons_col.addWidget(self.nl_status_label)

        self._nl_worker = None

        top_row.addLayout(buttons_col)
        top_row.addStretch(1)
        top_row.addSpacing(_cm_to_px(4))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setMaximumWidth(300)
        self.calendar.setMaximumHeight(190)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self._refresh_list)
        top_row.addWidget(self.calendar, 0, Qt.AlignTop)
        top_row.addStretch(1)
        self.clock = AnalogClock()
        top_row.addWidget(self.clock, 0, Qt.AlignTop)
        top_row.addSpacing(_cm_to_px(0.5))
        outer.addLayout(top_row)

        list_title_row = QHBoxLayout()
        self.list_title = QLabel("알람 목록")
        title_font = self.list_title.font()
        title_font.setBold(True)
        self.list_title.setFont(title_font)
        list_title_row.addWidget(self.list_title)
        list_title_row.addStretch(1)
        self.delete_all_button = QPushButton("알람 모두 삭제")
        self.delete_all_button.clicked.connect(self._delete_all_alarms)
        self.delete_all_button.setMinimumHeight(44)
        list_title_row.addWidget(self.delete_all_button)
        outer.addLayout(list_title_row)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(90)
        outer.addWidget(self.list_widget)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_list)
        self._timer.start(1000)
        self._refresh_list()

    def _add_once_alarm(self):
        date_dialog = _DatePickerDialog(self, "알람 날짜 선택")
        if date_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        date = date_dialog.selected_date()

        time_dialog = _TimePickerDialog(self, "알람 시간 선택")
        if time_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        time = time_dialog.selected_time()
        message = time_dialog.selected_message()

        self._alarms.append(
            {
                "id": str(uuid.uuid4()),
                "type": "once",
                "datetime": QDateTime(date, time),
                "fired": False,
                "message": message,
                "enabled": True,
            }
        )
        _save_alarm_state(self._alarms)
        self._refresh_list()

    def _add_recurring_alarm(self):
        range_dialog = _RecurringRangeDialog(self)
        if range_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        start_date, end_date, weekdays = range_dialog.selected_range()

        time_dialog = _TimePickerDialog(self, "알람 시간 선택")
        if time_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        time = time_dialog.selected_time()
        message = time_dialog.selected_message()

        self._alarms.append(
            {
                "id": str(uuid.uuid4()),
                "type": "recurring",
                "start_date": start_date,
                "end_date": end_date,
                "weekdays": weekdays,  # 0=Mon .. 6=Sun
                "time": time,
                "fired_dates": set(),
                "message": message,
                "enabled": True,
            }
        )
        _save_alarm_state(self._alarms)
        self._refresh_list()

    def _add_alarm_from_text(self):
        text = self.nl_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "알림", "자연어로 알람 내용을 입력하세요.")
            return

        self.nl_add_button.setEnabled(False)
        self.nl_status_label.setText("알람 설정 중...")

        self._nl_worker = _AlarmParseWorker(text, self)
        self._nl_worker.succeeded.connect(self._on_nl_parse_succeeded)
        self._nl_worker.failed.connect(self._on_nl_parse_failed)
        self._nl_worker.start()

    def _on_nl_parse_succeeded(self, data):
        self.nl_add_button.setEnabled(True)
        self.nl_status_label.setText("")
        try:
            alarm = self._alarm_from_parsed(data)
        except ValueError as exc:
            QMessageBox.critical(self, "알람 설정 실패", str(exc))
            return
        self._alarms.append(alarm)
        _save_alarm_state(self._alarms)
        self._refresh_list()
        self.nl_edit.clear()

    def _on_nl_parse_failed(self, message):
        self.nl_add_button.setEnabled(True)
        self.nl_status_label.setText("")
        if message == CLAUDE_NOT_FOUND_MESSAGE:
            QMessageBox.critical(self, "Claude Code 필요", message)
        else:
            QMessageBox.critical(self, "알람 설정 실패", message)

    def _alarm_from_parsed(self, data):
        message = str(data.get("message") or "").strip() or DEFAULT_ALARM_MESSAGE
        alarm_type = data.get("type")

        time = QTime.fromString(str(data.get("time", "")), "HH:mm")
        if not time.isValid():
            raise ValueError(f"시간을 해석할 수 없습니다: {data.get('time')!r}")

        if alarm_type == "once":
            date = QDate.fromString(str(data.get("date", "")), Qt.DateFormat.ISODate)
            if not date.isValid():
                raise ValueError(f"날짜를 해석할 수 없습니다: {data.get('date')!r}")
            return {
                "id": str(uuid.uuid4()),
                "type": "once",
                "datetime": QDateTime(date, time),
                "fired": False,
                "message": message,
                "enabled": True,
            }

        if alarm_type == "recurring":
            start_date = QDate.fromString(str(data.get("start_date", "")), Qt.DateFormat.ISODate)
            end_date = QDate.fromString(str(data.get("end_date", "")), Qt.DateFormat.ISODate)
            weekdays = [d for d in data.get("weekdays", []) if isinstance(d, int) and 0 <= d <= 6]
            if not start_date.isValid() or not end_date.isValid():
                raise ValueError("반복 알람의 날짜를 해석할 수 없습니다.")
            if not weekdays:
                raise ValueError("반복할 요일을 해석할 수 없습니다.")
            return {
                "id": str(uuid.uuid4()),
                "type": "recurring",
                "start_date": start_date,
                "end_date": end_date,
                "weekdays": weekdays,  # 0=Mon .. 6=Sun
                "time": time,
                "fired_dates": set(),
                "message": message,
                "enabled": True,
            }

        raise ValueError(f"알 수 없는 알람 유형입니다: {alarm_type!r}")

    def _delete_alarm(self, alarm_id):
        self._alarms = [a for a in self._alarms if a["id"] != alarm_id]
        _save_alarm_state(self._alarms)
        self._refresh_list()

    def _delete_all_alarms(self):
        if not self._alarms:
            return
        reply = QMessageBox.question(
            self,
            "모두 삭제 확인",
            f"등록된 알람 {len(self._alarms)}개를 모두 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._alarms = []
        _save_alarm_state(self._alarms)
        self._refresh_list()

    def _toggle_alarm(self, alarm_id):
        for alarm in self._alarms:
            if alarm["id"] == alarm_id:
                alarm["enabled"] = not alarm.get("enabled", True)
                break
        _save_alarm_state(self._alarms)
        self._refresh_list()

    def _next_occurrence(self, alarm, now):
        if alarm["type"] == "once":
            if alarm["fired"]:
                return None
            return alarm["datetime"]

        candidate_date = max(now.date(), alarm["start_date"])
        for _ in range(400):
            if candidate_date > alarm["end_date"]:
                return None
            if (candidate_date.dayOfWeek() - 1) in alarm["weekdays"]:
                candidate_dt = QDateTime(candidate_date, alarm["time"])
                date_key = candidate_date.toString(Qt.DateFormat.ISODate)
                if candidate_dt >= now and date_key not in alarm["fired_dates"]:
                    return candidate_dt
            candidate_date = candidate_date.addDays(1)
        return None

    def _occurs_on_date(self, alarm, date):
        if alarm["type"] == "once":
            return alarm["datetime"].date() == date
        return (
            alarm["start_date"] <= date <= alarm["end_date"]
            and (date.dayOfWeek() - 1) in alarm["weekdays"]
        )

    def _format_alarm_label(self, alarm):
        message = alarm.get("message") or DEFAULT_ALARM_MESSAGE
        if alarm["type"] == "once":
            when = "일회성: " + alarm["datetime"].toString("yyyy-MM-dd HH:mm")
        else:
            days = "".join(WEEKDAY_NAMES[d] for d in sorted(alarm["weekdays"]))
            when = (
                f"주기적({days}) {alarm['time'].toString('HH:mm')} "
                f"[~{alarm['end_date'].toString('yyyy-MM-dd')}]"
            )
        return f'{when} — "{message}"'

    def _format_remaining(self, secs):
        secs = max(0, secs)
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}시간 {m}분"
        if m > 0:
            return f"{m}분 {s}초"
        return f"{s}초"

    def _fire_alarm(self, alarm, occurrence):
        if alarm["type"] == "once":
            alarm["fired"] = True
        else:
            alarm["fired_dates"].add(occurrence.date().toString(Qt.DateFormat.ISODate))
        _save_alarm_state(self._alarms)
        popup = _AlarmPopup(alarm.get("message") or DEFAULT_ALARM_MESSAGE, self)
        popup.exec()

    def _refresh_list(self):
        now = QDateTime.currentDateTime()
        selected_date = self.calendar.selectedDate()
        self.list_title.setText(f"알람 목록 ({selected_date.toString('yyyy-MM-dd')})")
        self.list_widget.clear()

        for alarm in self._alarms:
            enabled = alarm.get("enabled", True)

            if enabled:
                occurrence = self._next_occurrence(alarm, now)
                if occurrence is None:
                    continue
                if now.secsTo(occurrence) <= 0:
                    self._fire_alarm(alarm, occurrence)
                    occurrence = self._next_occurrence(alarm, QDateTime.currentDateTime())
                    if occurrence is None:
                        continue
                status_text = f"남은 시간: {self._format_remaining(now.secsTo(occurrence))}"
            else:
                status_text = "꺼짐"

            # Firing above must run regardless of the calendar's selected
            # date - only whether a row gets drawn depends on it.
            if not self._occurs_on_date(alarm, selected_date):
                continue

            label_text = self._format_alarm_label(alarm)

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(6)
            label = QLabel(f"{label_text}    {status_text}")
            if not enabled:
                label.setStyleSheet("color: #999999;")
            row_layout.addWidget(label, 1)

            toggle_button = QPushButton("끄기" if enabled else "켜기")
            toggle_button.setFixedSize(52, 28)
            toggle_button.setToolTip("이 알람 비활성화" if enabled else "이 알람 활성화")
            toggle_button.clicked.connect(
                lambda _checked=False, alarm_id=alarm["id"]: self._toggle_alarm(alarm_id)
            )
            row_layout.addWidget(toggle_button)

            delete_button = QPushButton("×")
            delete_button.setFixedSize(28, 28)
            delete_button.setToolTip("이 알람 삭제")
            delete_button.setStyleSheet(
                "QPushButton {"
                "  border: 1px solid #cccccc;"
                "  border-radius: 14px;"
                "  background-color: #f5f5f5;"
                "  color: #666666;"
                "  font-size: 15px;"
                "  font-weight: bold;"
                "}"
                "QPushButton:hover {"
                "  background-color: #e53935;"
                "  border-color: #e53935;"
                "  color: white;"
                "}"
            )
            delete_button.clicked.connect(
                lambda _checked=False, alarm_id=alarm["id"]: self._delete_alarm(alarm_id)
            )
            row_layout.addWidget(delete_button)

            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)
