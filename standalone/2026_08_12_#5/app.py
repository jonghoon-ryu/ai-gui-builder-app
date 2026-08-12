import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as _html_to_markdown
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStyle,
    QTabWidget,
    QWidget,
)


def open_url(url):
    """Opens only http(s) links in the system's default browser."""
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 열 수 있습니다: {url!r}")
    QDesktopServices.openUrl(QUrl(url))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def delete_file(path):
    """Deletes a file only after the user confirms in a blocking dialog."""
    reply = QMessageBox.question(
        QApplication.activeWindow(),
        "삭제 확인",
        f"정말 삭제하시겠습니까?\n\n{path}",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return
    os.remove(path)


def list_dir(path):
    return sorted(os.listdir(path))


def make_dir(path):
    os.makedirs(path, exist_ok=True)


def move_file(src, dst):
    shutil.move(src, dst)


_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _urlopen_with_retry(request, timeout=15, retries=3):
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == retries - 1:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = float(retry_after) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt
            time.sleep(min(delay, 10))


def fetch_url(url):
    """Fetches an http(s) URL's body as text."""
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 가져올 수 있습니다: {url!r}")
    request = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})
    with _urlopen_with_retry(request) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_markdown(html):
    return _html_to_markdown(html)


def extract_images(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        images.append({"url": urljoin(base_url, src), "alt": img.get("alt") or ""})
    return images


def download_file(url, path):
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 다운로드할 수 있습니다: {url!r}")
    request = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})
    with _urlopen_with_retry(request) as response:
        data = response.read()
    with open(path, "wb") as f:
        f.write(data)


def classify_image_with_claude(path):
    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--output-format",
                "text",
                f"{path} 이 이미지를 보고 주제를 폴더 이름으로 쓸 수 있는 영문 소문자 한 단어로만 "
                "답하세요 (공백/특수문자/설명 없이 단어 하나만).",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "기타"
    if result.returncode != 0 or not result.stdout.strip():
        return "기타"
    word = "".join(ch for ch in result.stdout.strip().split()[0] if ch.isalnum() or ch in "-_")
    return word or "기타"


def _browse_directory(line_edit):
    directory = QFileDialog.getExistingDirectory(
        line_edit, "디렉토리 선택", line_edit.text(),
    )
    if directory:
        line_edit.setText(directory)


def _prompt_url(line_edit):
    text, ok = QInputDialog.getText(
        line_edit, "URL 입력", "URL:", QLineEdit.EchoMode.Normal, line_edit.text()
    )
    if ok and text:
        line_edit.setText(text)


import json
import os
import re
import subprocess
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

ALARM_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarm_state.json")


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alarms = _load_alarm_state()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(4)

        top_row = QHBoxLayout()
        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(6)
        self.add_once_button = QPushButton("일회성 알람 추가")
        self.add_once_button.clicked.connect(self._add_once_alarm)
        self.add_once_button.setMinimumHeight(36)
        self.add_recurring_button = QPushButton("주기적 알람 추가")
        self.add_recurring_button.clicked.connect(self._add_recurring_alarm)
        self.add_recurring_button.setMinimumHeight(36)
        buttons_col.addWidget(self.add_once_button)
        buttons_col.addSpacing(20)
        buttons_col.addWidget(self.add_recurring_button)
        buttons_col.addSpacing(20)

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
        self.nl_add_button.setMinimumHeight(36)
        buttons_col.addWidget(self.nl_add_button)

        self.nl_status_label = QLabel("")
        buttons_col.addWidget(self.nl_status_label)

        self._nl_worker = None

        buttons_col.addStretch()
        top_row.addLayout(buttons_col)
        top_row.addStretch(1)
        top_row.addSpacing(_cm_to_px(4))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setMaximumWidth(300)
        self.calendar.setMaximumHeight(190)
        self.calendar.setSelectedDate(QDate.currentDate())
        top_row.addWidget(self.calendar, 0, Qt.AlignTop)
        top_row.addStretch(1)
        self.clock = AnalogClock()
        top_row.addWidget(self.clock, 0, Qt.AlignTop)
        top_row.addSpacing(_cm_to_px(0.5))
        outer.addLayout(top_row)

        list_title = QLabel("알람 목록")
        title_font = list_title.font()
        title_font.setBold(True)
        list_title.setFont(title_font)
        outer.addWidget(list_title)

        self.list_widget = QListWidget()
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

"""'윈도우 현황' 위젯: Windows 버전/CPU/메모리/디스크 현황 + 휴지통 관리.

Uses only the standard library (ctypes calls into kernel32/shell32/psapi,
plus winreg/subprocess) instead of a package like psutil, so standalone-
exported apps that embed this widget still only need PySide6 to run (see
CLAUDE.md's export guarantee).
"""

import ctypes
import os
import platform
import string
import struct
import subprocess
import sys
import time
import winreg
from ctypes import wintypes
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

DRIVE_FIXED = 3
SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004
WARNING_PERCENT = 90
ALWAYS_SHOWN_DRIVES = ["C:\\", "D:\\", "E:\\"]


def get_windows_version():
    """Human-readable OS name + build number (e.g. 'Windows 11 (build 26100)')."""
    try:
        v = sys.getwindowsversion()
        if v.major == 10 and v.build >= 22000:
            name = "Windows 11"
        elif v.major == 10:
            name = "Windows 10"
        else:
            name = f"Windows {v.major}.{v.minor}"
        return f"{name} (build {v.build})"
    except AttributeError:
        return platform.platform()


def get_cpu_model():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        value, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        return " ".join(value.split())
    except OSError:
        return "확인 불가"


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


def _filetime_to_int(ft):
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


def _get_system_times():
    idle, kernel, user = _FILETIME(), _FILETIME(), _FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(
        ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
    )
    return _filetime_to_int(idle), _filetime_to_int(kernel), _filetime_to_int(user)


class CpuUsageTracker:
    """GetSystemTimes only reports cumulative counters, so usage % has to be
    derived from the delta between two samples - this keeps the previous
    sample around so callers can just poll cpu_percent() on a timer."""

    def __init__(self):
        self._prev = _get_system_times()

    def cpu_percent(self):
        idle, kernel, user = _get_system_times()
        p_idle, p_kernel, p_user = self._prev
        self._prev = (idle, kernel, user)
        # kernel time already includes idle time on Windows.
        total = (kernel - p_kernel) + (user - p_user)
        if total <= 0:
            return 0.0
        busy = total - (idle - p_idle)
        return max(0.0, min(100.0, busy / total * 100))


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


def get_memory_status():
    """Returns (percent_used, used_bytes, total_bytes)."""
    stat = _MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    used = stat.ullTotalPhys - stat.ullAvailPhys
    return stat.dwMemoryLoad, used, stat.ullTotalPhys


def list_fixed_drives():
    """Returns e.g. ['C:\\\\', 'D:\\\\'] for local fixed (hard) disks only -
    skips removable/optical/network drives so an empty CD-ROM slot etc.
    can't stall this."""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if not (bitmask & (1 << i)):
            continue
        drive = f"{letter}:\\"
        if ctypes.windll.kernel32.GetDriveTypeW(drive) == DRIVE_FIXED:
            drives.append(drive)
    return drives


def list_display_drives():
    """C/D/E always appear (even if absent, so the layout stays put), plus
    any other fixed drive actually present, appended in letter order."""
    fixed = list_fixed_drives()
    ordered = list(ALWAYS_SHOWN_DRIVES)
    for drive in fixed:
        if drive not in ordered:
            ordered.append(drive)
    return ordered, set(fixed)


def get_disk_usage(drive):
    """Returns (total, used, free) in bytes, or None if unreadable."""
    total = ctypes.c_uint64(0)
    free = ctypes.c_uint64(0)
    ok = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        drive, None, ctypes.byref(total), ctypes.byref(free)
    )
    if not ok:
        return None
    return total.value, total.value - free.value, free.value


class _SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]


def get_recycle_bin_summary():
    """Returns (total_size_bytes, item_count) across every fixed drive's
    recycle bin (passing a null root path queries all of them at once)."""
    info = _SHQUERYRBINFO()
    info.cbSize = ctypes.sizeof(_SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
    if result != 0:
        raise OSError(f"SHQueryRecycleBinW failed (code {result})")
    return info.i64Size, info.i64NumItems


def empty_recycle_bin():
    ctypes.windll.shell32.SHEmptyRecycleBinW(
        None, None, SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
    )


def _filetime_int_to_datetime(filetime_int):
    epoch_as_filetime = 116444736000000000  # 1970-01-01 expressed as FILETIME
    try:
        return datetime.fromtimestamp((filetime_int - epoch_as_filetime) / 10_000_000)
    except (OverflowError, OSError, ValueError):
        return None


def _parse_recycle_index_file(path):
    """Parses a `$I*` metadata file inside `$Recycle.Bin` (undocumented but
    stable since Windows Vista) into (original_path, size, deleted_at)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    if len(data) < 24:
        return None
    version = struct.unpack("<q", data[0:8])[0]
    size = struct.unpack("<q", data[8:16])[0]
    deleted_at = _filetime_int_to_datetime(struct.unpack("<q", data[16:24])[0])
    if version == 2 and len(data) >= 28:
        name_len = struct.unpack("<i", data[24:28])[0]
        raw = data[28 : 28 + name_len * 2]
    else:
        raw = data[24:]
    original_path = raw.decode("utf-16-le", errors="replace").split("\x00", 1)[0]
    return original_path, size, deleted_at


def list_recycle_bin_items():
    """Returns [{"name", "original_path", "size", "deleted_at"}, ...] by
    scanning every fixed drive's `$Recycle.Bin` folder directly (there is no
    public API for per-item enumeration without extra packages)."""
    items = []
    for drive in list_fixed_drives():
        bin_root = os.path.join(drive, "$Recycle.Bin")
        if not os.path.isdir(bin_root):
            continue
        try:
            sid_names = os.listdir(bin_root)
        except OSError:
            continue
        for sid in sid_names:
            sid_path = os.path.join(bin_root, sid)
            try:
                entry_names = os.listdir(sid_path)
            except OSError:
                continue
            for name in entry_names:
                if not name.startswith("$I"):
                    continue
                parsed = _parse_recycle_index_file(os.path.join(sid_path, name))
                if not parsed:
                    continue
                original_path, size, deleted_at = parsed
                items.append(
                    {
                        "name": os.path.basename(original_path) or name,
                        "original_path": original_path,
                        "size": size,
                        "deleted_at": deleted_at,
                    }
                )
    items.sort(key=lambda it: it["deleted_at"] or datetime.min, reverse=True)
    return items


def _format_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}{unit}"
        n /= 1024


# ---- Top-5 process list (button-triggered, one-shot sample) ---------------

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
TH32CS_SNAPPROCESS = 0x00000002


class _PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _list_processes():
    """Returns [(pid, name), ...] via a toolhelp snapshot."""
    snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == -1:
        return []
    entry = _PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(_PROCESSENTRY32)
    processes = []
    try:
        if ctypes.windll.kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            while True:
                processes.append((entry.th32ProcessID, entry.szExeFile))
                if not ctypes.windll.kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break
    finally:
        ctypes.windll.kernel32.CloseHandle(snapshot)
    return processes


def _process_cpu_time(pid):
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        creation, exit_t, kernel, user = _FILETIME(), _FILETIME(), _FILETIME(), _FILETIME()
        ok = ctypes.windll.kernel32.GetProcessTimes(
            handle, ctypes.byref(creation), ctypes.byref(exit_t),
            ctypes.byref(kernel), ctypes.byref(user),
        )
        if not ok:
            return None
        return _filetime_to_int(kernel) + _filetime_to_int(user)
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _process_memory_bytes(pid):
    handle = ctypes.windll.kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
    )
    if not handle:
        return None
    try:
        counters = _PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        if not ok:
            return None
        return counters.WorkingSetSize
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def get_top_processes(limit=5, sample_interval=0.3):
    """One-shot snapshot (not continuously tracked, since it's opened from a
    button rather than the periodic refresh - sampling every process on
    every tick would be wasteful). Returns (top_cpu, top_memory), each a
    list of {"pid", "name", ...} sorted descending."""
    processes = _list_processes()

    before = {}
    for pid, _name in processes:
        t = _process_cpu_time(pid)
        if t is not None:
            before[pid] = t
    time.sleep(sample_interval)

    cpu_count = os.cpu_count() or 1
    cpu_results = []
    mem_results = []
    for pid, name in processes:
        t_before = before.get(pid)
        if t_before is not None:
            t_after = _process_cpu_time(pid)
            if t_after is not None:
                delta_100ns = t_after - t_before
                percent = delta_100ns / (sample_interval * 10_000_000) / cpu_count * 100
                cpu_results.append({"pid": pid, "name": name, "cpu_percent": max(0.0, percent)})
        mem = _process_memory_bytes(pid)
        if mem is not None:
            mem_results.append({"pid": pid, "name": name, "memory": mem})

    cpu_results.sort(key=lambda p: p["cpu_percent"], reverse=True)
    mem_results.sort(key=lambda p: p["memory"], reverse=True)
    return cpu_results[:limit], mem_results[:limit]


# ---- Folder size breakdown --------------------------------------------

def get_folder_sizes():
    """Total size of a few well-known "grows silently" folders (Temp,
    Downloads). Walks the filesystem directly - can take a moment for very
    large folders, which is why this is button-triggered, not on a timer."""
    targets = [
        ("Temp", os.environ.get("TEMP") or os.environ.get("TMP") or ""),
        ("다운로드", os.path.join(os.path.expanduser("~"), "Downloads")),
    ]
    results = []
    for label, path in targets:
        if not path or not os.path.isdir(path):
            results.append({"label": label, "path": path, "size": None})
            continue
        total = 0
        for root, _dirs, files in os.walk(path):
            for name in files:
                try:
                    total += os.path.getsize(os.path.join(root, name))
                except OSError:
                    pass
        results.append({"label": label, "path": path, "size": total})
    return results


# ---- Startup programs ---------------------------------------------------

_RUN_KEYS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
]
_STARTUP_FOLDER_ENV_VARS = ["APPDATA", "PROGRAMDATA"]
_STARTUP_FOLDER_SUFFIX = r"Microsoft\Windows\Start Menu\Programs\Startup"


def list_startup_programs():
    """Returns [{"name", "command", "source"}, ...] from both the registry
    Run keys and the Startup shell folders (shortcut targets aren't resolved
    - that needs COM/pywin32 - so folder entries just show the filename)."""
    items = []
    for hive, subkey in _RUN_KEYS:
        try:
            key = winreg.OpenKey(hive, subkey)
        except OSError:
            continue
        try:
            i = 0
            while True:
                try:
                    name, value, _type = winreg.EnumValue(key, i)
                except OSError:
                    break
                items.append({"name": name, "command": value, "source": "레지스트리"})
                i += 1
        finally:
            winreg.CloseKey(key)

    for env_var in _STARTUP_FOLDER_ENV_VARS:
        base = os.environ.get(env_var)
        if not base:
            continue
        folder = os.path.join(base, _STARTUP_FOLDER_SUFFIX)
        if not os.path.isdir(folder):
            continue
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            items.append(
                {"name": name, "command": os.path.join(folder, name), "source": "시작프로그램 폴더"}
            )
    return items


def open_environment_variables_dialog():
    """Launches Windows' own Environment Variables editor directly (the
    well-known rundll32 shortcut), instead of re-implementing a viewer."""
    subprocess.Popen(["rundll32.exe", "sysdm.cpl,EditEnvironmentVariables"])


class WindowStatusPanel(QWidget):
    """Self-contained Windows status dashboard: OS version/CPU model, live
    CPU/memory/disk usage (with warning colors), recycle bin size/list/
    empty, and buttons for a top-process snapshot, folder size breakdown,
    startup program list, and the system environment-variables editor."""

    REFRESH_INTERVAL_MS = 3000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cpu_tracker = CpuUsageTracker()
        self._disk_rows = {}
        self._next_grid_row = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        sys_title = QLabel("시스템 정보")
        self._make_bold(sys_title)
        outer.addWidget(sys_title)

        self.os_label = QLabel()
        outer.addWidget(self.os_label)
        self.cpu_model_label = QLabel()
        outer.addWidget(self.cpu_model_label)

        self.info_grid = QGridLayout()
        self.info_grid.setHorizontalSpacing(8)
        self.info_grid.setVerticalSpacing(4)
        self.info_grid.setColumnMinimumWidth(0, 90)
        self.info_grid.setColumnStretch(1, 1)
        outer.addLayout(self.info_grid)

        self.cpu_bar, self.cpu_value_label = self._add_meter_row("CPU 사용률:")
        self.mem_bar, self.mem_value_label = self._add_meter_row("메모리:")

        disk_title = QLabel("디스크")
        self._make_bold(disk_title)
        outer.addWidget(disk_title)

        self.disk_grid = QGridLayout()
        self.disk_grid.setHorizontalSpacing(8)
        self.disk_grid.setVerticalSpacing(4)
        self.disk_grid.setColumnMinimumWidth(0, 90)
        self.disk_grid.setColumnStretch(1, 1)
        outer.addLayout(self.disk_grid)

        actions_row = QHBoxLayout()
        self.top_processes_button = QPushButton("상위 프로세스")
        self.top_processes_button.clicked.connect(self._show_top_processes)
        actions_row.addWidget(self.top_processes_button)
        self.folder_sizes_button = QPushButton("폴더 용량")
        self.folder_sizes_button.clicked.connect(self._show_folder_sizes)
        actions_row.addWidget(self.folder_sizes_button)
        self.startup_button = QPushButton("시작 프로그램 목록")
        self.startup_button.clicked.connect(self._show_startup_programs)
        actions_row.addWidget(self.startup_button)
        self.env_vars_button = QPushButton("시스템 변수 바로보기")
        self.env_vars_button.clicked.connect(open_environment_variables_dialog)
        actions_row.addWidget(self.env_vars_button)
        outer.addLayout(actions_row)

        bin_row = QHBoxLayout()
        bin_icon_label = QLabel()
        bin_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        bin_icon_label.setPixmap(bin_icon.pixmap(24, 24))
        bin_row.addWidget(bin_icon_label)
        self.bin_label = QLabel("휴지통: 확인 중...")
        bin_row.addWidget(self.bin_label, 1)
        self.bin_list_button = QPushButton("목록")
        self.bin_list_button.clicked.connect(self._show_recycle_bin_list)
        bin_row.addWidget(self.bin_list_button)
        self.bin_empty_button = QPushButton("휴지통 비우기")
        self.bin_empty_button.clicked.connect(self._empty_recycle_bin)
        bin_row.addWidget(self.bin_empty_button)
        outer.addLayout(bin_row)

        outer.addStretch()

        self._refresh()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(self.REFRESH_INTERVAL_MS)

    @staticmethod
    def _make_bold(label):
        font = label.font()
        font.setBold(True)
        label.setFont(font)

    @staticmethod
    def _apply_warning_style(bar, percent):
        if percent >= WARNING_PERCENT:
            bar.setStyleSheet("QProgressBar::chunk { background-color: #d64545; }")
        else:
            bar.setStyleSheet("")

    def _add_meter_row(self, title):
        row = self._next_grid_row
        self._next_grid_row += 1
        self.info_grid.addWidget(QLabel(title), row, 0)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(False)
        self.info_grid.addWidget(bar, row, 1)
        value_label = QLabel("0%")
        value_label.setMinimumWidth(180)
        self.info_grid.addWidget(value_label, row, 2)
        return bar, value_label

    def _refresh(self):
        self.os_label.setText(f"Windows 버전: {get_windows_version()}")
        self.cpu_model_label.setText(f"CPU 모델: {get_cpu_model()}")

        cpu_percent = self._cpu_tracker.cpu_percent()
        self.cpu_bar.setValue(int(cpu_percent))
        self._apply_warning_style(self.cpu_bar, cpu_percent)
        self.cpu_value_label.setText(f"{cpu_percent:.0f}%")

        mem_percent, mem_used, mem_total = get_memory_status()
        self.mem_bar.setValue(mem_percent)
        self._apply_warning_style(self.mem_bar, mem_percent)
        self.mem_value_label.setText(
            f"{mem_percent}% ({_format_bytes(mem_used)}/{_format_bytes(mem_total)})"
        )

        self._refresh_disks()
        self._refresh_recycle_bin_summary()

    def _refresh_disks(self):
        ordered_drives, present_set = list_display_drives()

        for drive in list(self._disk_rows):
            if drive not in ordered_drives:
                for widget in self._disk_rows.pop(drive)[2]:
                    widget.deleteLater()

        for drive in ordered_drives:
            if drive not in self._disk_rows:
                label = QLabel(drive.rstrip("\\"))
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setTextVisible(False)
                value_label = QLabel()
                value_label.setMinimumWidth(200)
                row = self._next_grid_row
                self._next_grid_row += 1
                self.disk_grid.addWidget(label, row, 0)
                self.disk_grid.addWidget(bar, row, 1)
                self.disk_grid.addWidget(value_label, row, 2)
                self._disk_rows[drive] = (bar, value_label, (label, bar, value_label))

            bar, value_label, _widgets = self._disk_rows[drive]

            if drive not in present_set:
                bar.setValue(0)
                bar.setStyleSheet("")
                value_label.setText("없음")
                continue

            usage = get_disk_usage(drive)
            if usage is None:
                value_label.setText("확인 불가")
                continue
            total, used, _free = usage
            percent = int(used / total * 100) if total else 0
            bar.setValue(percent)
            self._apply_warning_style(bar, percent)
            value_label.setText(f"{_format_bytes(used)}/{_format_bytes(total)} ({percent}%)")

    def _refresh_recycle_bin_summary(self):
        try:
            size, count = get_recycle_bin_summary()
        except OSError:
            self.bin_label.setText("휴지통: 확인 불가")
            return
        self.bin_label.setText(f"휴지통: {count}개 파일, {_format_bytes(size)}")

    def _show_recycle_bin_list(self):
        items = list_recycle_bin_items()

        dialog = QDialog(self)
        dialog.setWindowTitle("휴지통 파일 목록")
        dialog.resize(640, 420)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(len(items), 4)
        table.setHorizontalHeaderLabels(["이름", "원래 위치", "크기", "삭제된 시각"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, item in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(item["name"]))
            # A plain QTableWidgetItem's built-in text painter truncates
            # after just a couple of characters for some Hangul-containing
            # strings in this environment (data itself is intact - verified
            # via .text() - it's purely a rendering glitch); a QLabel cell
            # widget uses different paint machinery and renders correctly.
            path_label = QLabel(item["original_path"])
            path_label.setToolTip(item["original_path"])
            path_label.setContentsMargins(4, 0, 4, 0)
            table.setCellWidget(row, 1, path_label)
            table.setItem(row, 2, QTableWidgetItem(_format_bytes(item["size"])))
            deleted_at = item["deleted_at"]
            table.setItem(
                row, 3, QTableWidgetItem(deleted_at.strftime("%Y-%m-%d %H:%M") if deleted_at else "")
            )
        layout.addWidget(table)

        if not items:
            layout.addWidget(QLabel("휴지통이 비어 있습니다."))

        close_button = QPushButton("닫기")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _empty_recycle_bin(self):
        reply = QMessageBox.question(
            self,
            "휴지통 비우기",
            "휴지통을 완전히 비우시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            empty_recycle_bin()
        except OSError as exc:
            QMessageBox.warning(self, "오류", f"휴지통을 비우지 못했습니다:\n{exc}")
            return
        self._refresh_recycle_bin_summary()

    def _show_top_processes(self):
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            top_cpu, top_mem = get_top_processes()
        finally:
            self.unsetCursor()

        dialog = QDialog(self)
        dialog.setWindowTitle("상위 프로세스 (CPU / 메모리)")
        dialog.resize(560, 420)
        layout = QVBoxLayout(dialog)

        cpu_title = QLabel("CPU 사용률 상위 5개")
        self._make_bold(cpu_title)
        layout.addWidget(cpu_title)
        cpu_table = QTableWidget(len(top_cpu), 3)
        cpu_table.setHorizontalHeaderLabels(["이름", "PID", "CPU %"])
        cpu_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, proc in enumerate(top_cpu):
            cpu_table.setItem(row, 0, QTableWidgetItem(proc["name"]))
            cpu_table.setItem(row, 1, QTableWidgetItem(str(proc["pid"])))
            cpu_table.setItem(row, 2, QTableWidgetItem(f"{proc['cpu_percent']:.1f}%"))
        layout.addWidget(cpu_table)

        mem_title = QLabel("메모리 사용량 상위 5개")
        self._make_bold(mem_title)
        layout.addWidget(mem_title)
        mem_table = QTableWidget(len(top_mem), 3)
        mem_table.setHorizontalHeaderLabels(["이름", "PID", "메모리"])
        mem_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, proc in enumerate(top_mem):
            mem_table.setItem(row, 0, QTableWidgetItem(proc["name"]))
            mem_table.setItem(row, 1, QTableWidgetItem(str(proc["pid"])))
            mem_table.setItem(row, 2, QTableWidgetItem(_format_bytes(proc["memory"])))
        layout.addWidget(mem_table)

        close_button = QPushButton("닫기")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _show_folder_sizes(self):
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            results = get_folder_sizes()
        finally:
            self.unsetCursor()

        dialog = QDialog(self)
        dialog.setWindowTitle("폴더별 용량")
        dialog.resize(520, 200)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(len(results), 3)
        table.setHorizontalHeaderLabels(["폴더", "경로", "용량"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, item in enumerate(results):
            table.setItem(row, 0, QTableWidgetItem(item["label"]))
            path_label = QLabel(item["path"] or "-")
            path_label.setContentsMargins(4, 0, 4, 0)
            table.setCellWidget(row, 1, path_label)
            size_text = _format_bytes(item["size"]) if item["size"] is not None else "확인 불가"
            table.setItem(row, 2, QTableWidgetItem(size_text))
        layout.addWidget(table)

        close_button = QPushButton("닫기")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _show_startup_programs(self):
        items = list_startup_programs()

        dialog = QDialog(self)
        dialog.setWindowTitle("시작 프로그램 목록")
        dialog.resize(640, 420)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(len(items), 3)
        table.setHorizontalHeaderLabels(["이름", "실행 명령/경로", "출처"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, item in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(item["name"]))
            command_label = QLabel(item["command"])
            command_label.setToolTip(item["command"])
            command_label.setContentsMargins(4, 0, 4, 0)
            table.setCellWidget(row, 1, command_label)
            table.setItem(row, 2, QTableWidgetItem(item["source"]))
        layout.addWidget(table)

        if not items:
            layout.addWidget(QLabel("시작 프로그램이 없습니다."))

        close_button = QPushButton("닫기")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

class GeneratedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        page_0 = QWidget()
        page_0.setFixedSize(821, 536)
        page_0.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_0.setStyleSheet("background-color: #ddebe2;")

        self.tabs.addTab(page_0, "git")

        page_1 = QWidget()
        page_1.setFixedSize(821, 536)
        page_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_1.setStyleSheet("background-color: #f9f06b;")

        self.tab1_urlbox_1 = QLineEdit(page_1)
        self.tab1_urlbox_1.setPlaceholderText("URL 입력 (https://...)")
        _action = self.tab1_urlbox_1.addAction(self.tab1_urlbox_1.style().standardIcon(QStyle.StandardPixmap.SP_DirLinkIcon), QLineEdit.ActionPosition.TrailingPosition)
        _action.triggered.connect(lambda: _prompt_url(self.tab1_urlbox_1))
        self.tab1_urlbox_1.setText("https://ko.wikipedia.org/wiki/%ED%95%9C%EA%B8%80")
        self.tab1_urlbox_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab1_urlbox_1.setStyleSheet("background-color: #ffbe6f;")
        self.tab1_urlbox_1.move(134, 92)
        self.tab1_urlbox_1.adjustSize()
        self.tab1_urlbox_1.resize(306, 26)

        self.tab1_dirbox_1 = QLineEdit(page_1)
        self.tab1_dirbox_1.setPlaceholderText("디렉토리 경로 입력")
        _action = self.tab1_dirbox_1.addAction(self.tab1_dirbox_1.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon), QLineEdit.ActionPosition.TrailingPosition)
        _action.triggered.connect(lambda: _browse_directory(self.tab1_dirbox_1))
        self.tab1_dirbox_1.setText("C:/repository/hangul")
        self.tab1_dirbox_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab1_dirbox_1.setStyleSheet("background-color: #ffffff;")
        self.tab1_dirbox_1.move(134, 157)
        self.tab1_dirbox_1.adjustSize()
        self.tab1_dirbox_1.resize(307, 26)

        self.tab1_button_1 = QPushButton("버튼", page_1)
        self.tab1_button_1.setText("URL 에서 파일을 가져와서 md 로 변환")
        self.tab1_button_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab1_button_1.setStyleSheet("background-color: #aaaaff;")
        self.tab1_button_1.move(153, 284)
        self.tab1_button_1.adjustSize()
        self.tab1_button_1.resize(244, 24)
        self.tab1_button_1.clicked.connect(self._tab1_button_1_on_event)

        self.tab1_radiobutton_1 = QRadioButton("옵션", page_1)
        self.tab1_radiobutton_1.setAutoExclusive(False)
        self.tab1_radiobutton_1.setText("알아서 image 파일 분류")
        self.tab1_radiobutton_1.move(81, 215)
        self.tab1_radiobutton_1.adjustSize()
        self.tab1_radiobutton_1.resize(156, 15)

        self.tab1_radiobutton_2 = QRadioButton("옵션", page_1)
        self.tab1_radiobutton_2.setAutoExclusive(False)
        self.tab1_radiobutton_2.setText("클로드의 도움을 받아 상세히 image 파일 분류")
        self.tab1_radiobutton_2.move(82, 239)
        self.tab1_radiobutton_2.adjustSize()
        self.tab1_radiobutton_2.resize(280, 15)

        self.tab1_lineedit_1 = QLineEdit(page_1)
        self.tab1_lineedit_1.setPlaceholderText("텍스트 입력")
        self.tab1_lineedit_1.setText("URL :")
        self.tab1_lineedit_1.setFrame(False)
        self.tab1_lineedit_1.move(71, 93)
        self.tab1_lineedit_1.adjustSize()
        self.tab1_lineedit_1.resize(51, 24)

        self.tab1_lineedit_2 = QLineEdit(page_1)
        self.tab1_lineedit_2.setPlaceholderText("텍스트 입력")
        self.tab1_lineedit_2.setText("local :")
        self.tab1_lineedit_2.setFrame(False)
        self.tab1_lineedit_2.move(71, 157)
        self.tab1_lineedit_2.adjustSize()
        self.tab1_lineedit_2.resize(52, 23)

        tab1_radio_group_0 = QButtonGroup(self)
        tab1_radio_group_0.addButton(self.tab1_radiobutton_1)
        tab1_radio_group_0.addButton(self.tab1_radiobutton_2)
        self.tab1_radiobutton_1.setChecked(True)

        self.tabs.addTab(page_1, "wiki")

        page_2 = QWidget()
        page_2.setFixedSize(821, 536)
        page_2.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_2.setStyleSheet("background-color: #deddda;")

        self.tab2_windowstatus_1 = WindowStatusPanel(page_2)
        self.tab2_windowstatus_1.move(30, 56)
        self.tab2_windowstatus_1.adjustSize()
        self.tab2_windowstatus_1.resize(760, 400)

        self.tabs.addTab(page_2, "윈도우 현황")

        page_3 = QWidget()
        page_3.setFixedSize(821, 536)

        self.tab3_alarmclock_1 = AlarmClockPanel(page_3)
        self.tab3_alarmclock_1.move(10, 22)
        self.tab3_alarmclock_1.adjustSize()
        self.tab3_alarmclock_1.resize(802, 476)

        self.tabs.addTab(page_3, "alarm")

        page_4 = QWidget()
        page_4.setFixedSize(821, 536)
        page_4.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_4.setStyleSheet("background-color: #f4e8e8;")

        self.tab4_button_1 = QPushButton("버튼", page_4)
        self.tab4_button_1.setText("아름다운 나라 - 하윤주")
        self.tab4_button_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab4_button_1.setStyleSheet("background-color: #dc8add;")
        self.tab4_button_1.move(65, 107)
        self.tab4_button_1.adjustSize()
        self.tab4_button_1.resize(140, 23)
        self.tab4_button_1.clicked.connect(self._tab4_button_1_on_event)

        self.tab4_lineedit_1 = QLineEdit(page_4)
        self.tab4_lineedit_1.setPlaceholderText("텍스트 입력")
        self.tab4_lineedit_1.setText("  노래")
        self.tab4_lineedit_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab4_lineedit_1.setStyleSheet("background-color: #8ff0a4;")
        self.tab4_lineedit_1.move(106, 37)
        self.tab4_lineedit_1.adjustSize()
        self.tab4_lineedit_1.resize(55, 23)

        self.tab4_button_2 = QPushButton("버튼", page_4)
        self.tab4_button_2.setText("섬집 아기 - 하윤주")
        self.tab4_button_2.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab4_button_2.setStyleSheet("background-color: #ffbe6f;")
        self.tab4_button_2.move(65, 163)
        self.tab4_button_2.adjustSize()
        self.tab4_button_2.resize(116, 23)
        self.tab4_button_2.clicked.connect(self._tab4_button_2_on_event)

        self.tab4_button_3 = QPushButton("버튼", page_4)
        self.tab4_button_3.setText("아스피린 - 걸")
        self.tab4_button_3.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab4_button_3.setStyleSheet("background-color: #99c1f1;")
        self.tab4_button_3.move(65, 218)
        self.tab4_button_3.adjustSize()
        self.tab4_button_3.resize(93, 21)
        self.tab4_button_3.clicked.connect(self._tab4_button_3_on_event)

        self.tab4_hline_1 = QFrame(page_4)
        self.tab4_hline_1.setFrameShape(QFrame.Shape.HLine)
        self.tab4_hline_1.setFrameShadow(QFrame.Shadow.Plain)
        self.tab4_hline_1.setLineWidth(2)
        self.tab4_hline_1.setStyleSheet("color: #777777;")
        self.tab4_hline_1.move(28, 75)
        self.tab4_hline_1.adjustSize()
        self.tab4_hline_1.resize(486, 21)

        self.tab4_vline_1 = QFrame(page_4)
        self.tab4_vline_1.setFrameShape(QFrame.Shape.VLine)
        self.tab4_vline_1.setFrameShadow(QFrame.Shadow.Plain)
        self.tab4_vline_1.setLineWidth(2)
        self.tab4_vline_1.setStyleSheet("color: #777777;")
        self.tab4_vline_1.move(246, 26)
        self.tab4_vline_1.adjustSize()
        self.tab4_vline_1.resize(29, 374)

        self.tab4_lineedit_2 = QLineEdit(page_4)
        self.tab4_lineedit_2.setPlaceholderText("텍스트 입력")
        self.tab4_lineedit_2.setText("   만화")
        self.tab4_lineedit_2.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab4_lineedit_2.setStyleSheet("background-color: #ffbe6f;")
        self.tab4_lineedit_2.move(371, 34)
        self.tab4_lineedit_2.adjustSize()
        self.tab4_lineedit_2.resize(50, 24)

        self.tab4_button_4 = QPushButton("버튼", page_4)
        self.tab4_button_4.setText("네이버 웹툰 - 생활의 참견 2")
        self.tab4_button_4.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab4_button_4.setStyleSheet("background-color: #cdab8f;")
        self.tab4_button_4.move(307, 105)
        self.tab4_button_4.adjustSize()
        self.tab4_button_4.resize(187, 24)
        self.tab4_button_4.clicked.connect(self._tab4_button_4_on_event)

        self.tabs.addTab(page_4, "쉬었다 합시다")

    def _tab1_button_1_on_event(self):
        filename, ok = QInputDialog.getText(
            self, "MD 파일 이름", "저장할 md 파일 이름을 입력하세요:", text="output.md"
        )
        if not ok or not filename.strip():
            return
        filename = filename.strip()
        if not filename.lower().endswith(".md"):
            filename = filename + ".md"

        url = self.tab1_urlbox_1.text().strip()
        save_dir = self.tab1_dirbox_1.text().strip()

        if not url:
            QMessageBox.information(self, "오류", "URL을 입력해주세요.")
            return
        if not save_dir:
            QMessageBox.information(self, "오류", "저장할 디렉토리를 입력해주세요.")
            return

        make_dir(save_dir)

        try:
            html = fetch_url(url)
        except Exception as e:
            QMessageBox.information(self, "오류", f"문서를 가져오는 중 오류가 발생했습니다: {e}")
            return

        md = html_to_markdown(html)

        save_path = save_dir.rstrip("/") + "/" + filename
        write_file(save_path, md)

        images = extract_images(html, url)
        saved_count = 0
        if images and (self.tab1_radiobutton_1.isChecked() or self.tab1_radiobutton_2.isChecked()):
            images_dir = save_dir.rstrip("/") + "/images"
            make_dir(images_dir)
            for i, img in enumerate(images):
                img_url = img["url"]
                ext = img_url.split("?")[0].rsplit(".", 1)[-1]
                if not ext or len(ext) > 5:
                    ext = "png"
                temp_name = f"image_{i}.{ext}"
                temp_path = images_dir + "/" + temp_name
                try:
                    download_file(img_url, temp_path)
                except Exception:
                    continue
                saved_count += 1

                if self.tab1_radiobutton_2.isChecked():
                    topic = classify_image_with_claude(temp_path)
                    topic_dir = images_dir + "/" + topic
                    make_dir(topic_dir)
                    move_file(temp_path, topic_dir + "/" + temp_name)

        if self.tab1_radiobutton_1.isChecked():
            QMessageBox.information(
                self, "이미지 처리", f"이미지 {saved_count}개를 images 폴더에 저장했습니다."
            )
        elif self.tab1_radiobutton_2.isChecked():
            QMessageBox.information(
                self, "이미지 처리", f"이미지 {saved_count}개를 Claude가 분류한 폴더에 저장했습니다."
            )

        QMessageBox.information(self, "완료", f"{save_path} 에 저장되었습니다.")

    def _tab4_button_1_on_event(self):
        open_url("https://youtu.be/_lKiuqlg4ro?si=BnGTCMSJ1Nd_5VWC")

    def _tab4_button_2_on_event(self):
        open_url("https://youtu.be/3smn8BRrKKM?si=9YymxC7vznMOU2vE")

    def _tab4_button_3_on_event(self):
        open_url("https://youtu.be/QvbvibmiEmM?si=iI5yTWsD07JMID-a")

    def _tab4_button_4_on_event(self):
        open_url("https://comic.naver.com/webtoon/list?titleId=849676&page=2&sort=DESC")


def main():
    app = QApplication(sys.argv)
    window = GeneratedApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
