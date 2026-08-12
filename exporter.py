import os
import re
import textwrap

from code_binder import SIGNAL_BY_KIND

_ALARM_WIDGET_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "alarm_widget.py"
)


def _read_alarm_widget_source():
    """Embeds alarm_widget.py's actual source into the exported app instead
    of hand-duplicating the class as a string template - keeps the builder
    and the standalone export from drifting apart."""
    with open(_ALARM_WIDGET_SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()

HEADER_TEMPLATE = '''import os
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
        raise ValueError(f"http(s) URL만 열 수 있습니다: {{url!r}}")
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
        f"정말 삭제하시겠습니까?\\n\\n{{path}}",
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
        raise ValueError(f"http(s) URL만 가져올 수 있습니다: {{url!r}}")
    request = urllib.request.Request(url, headers={{"User-Agent": _BROWSER_USER_AGENT}})
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
        images.append({{"url": urljoin(base_url, src), "alt": img.get("alt") or ""}})
    return images


def download_file(url, path):
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 다운로드할 수 있습니다: {{url!r}}")
    request = urllib.request.Request(url, headers={{"User-Agent": _BROWSER_USER_AGENT}})
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
                f"{{path}} 이 이미지를 보고 주제를 폴더 이름으로 쓸 수 있는 영문 소문자 한 단어로만 "
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
        options=QFileDialog.Option.DontUseNativeDialog,
    )
    if directory:
        line_edit.setText(directory)


def _prompt_url(line_edit):
    text, ok = QInputDialog.getText(
        line_edit, "URL 입력", "URL:", QLineEdit.EchoMode.Normal, line_edit.text()
    )
    if ok and text:
        line_edit.setText(text)


{alarm_widget_source}
class {class_name}(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("{window_title}")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

{init_body}
'''

FOOTER_TEMPLATE = '''

def main():
    app = QApplication(sys.argv)
    window = {class_name}()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
'''


def _create_lines(
    widget_id, kind, x, y, parent_var, text=None, color=None, width=None, height=None,
    font_family=None, font_size=None, no_border=False,
):
    lines = []
    if kind == "combobox":
        lines.append(f'self.{widget_id} = QComboBox({parent_var})')
        lines.append(f'self.{widget_id}.addItems(["옵션 1", "옵션 2", "옵션 3"])')
    elif kind == "button":
        lines.append(f'self.{widget_id} = QPushButton("버튼", {parent_var})')
    elif kind == "lineedit":
        lines.append(f'self.{widget_id} = QLineEdit({parent_var})')
        lines.append(f'self.{widget_id}.setPlaceholderText("텍스트 입력")')
    elif kind == "urlbox":
        lines.append(f'self.{widget_id} = QLineEdit({parent_var})')
        lines.append(f'self.{widget_id}.setPlaceholderText("URL 입력 (https://...)")')
        lines.append(
            f'_action = self.{widget_id}.addAction('
            f'self.{widget_id}.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon), '
            f'QLineEdit.ActionPosition.TrailingPosition)'
        )
        lines.append(f'_action.triggered.connect(lambda: _prompt_url(self.{widget_id}))')
    elif kind == "dirbox":
        lines.append(f'self.{widget_id} = QLineEdit({parent_var})')
        lines.append(f'self.{widget_id}.setPlaceholderText("디렉토리 경로 입력")')
        lines.append(
            f'_action = self.{widget_id}.addAction('
            f'self.{widget_id}.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon), '
            f'QLineEdit.ActionPosition.TrailingPosition)'
        )
        lines.append(f'_action.triggered.connect(lambda: _browse_directory(self.{widget_id}))')
    elif kind == "radiobutton":
        lines.append(f'self.{widget_id} = QRadioButton("옵션", {parent_var})')
        lines.append(f'self.{widget_id}.setAutoExclusive(False)')
    elif kind == "alarmclock":
        lines.append(f'self.{widget_id} = AlarmClockPanel({parent_var})')
    elif kind == "hline":
        lines.append(f'self.{widget_id} = QFrame({parent_var})')
        lines.append(f'self.{widget_id}.setFrameShape(QFrame.Shape.HLine)')
        lines.append(f'self.{widget_id}.setFrameShadow(QFrame.Shadow.Plain)')
        lines.append(f'self.{widget_id}.setLineWidth(2)')
        lines.append(f'self.{widget_id}.setStyleSheet("color: #777777;")')
    elif kind == "vline":
        lines.append(f'self.{widget_id} = QFrame({parent_var})')
        lines.append(f'self.{widget_id}.setFrameShape(QFrame.Shape.VLine)')
        lines.append(f'self.{widget_id}.setFrameShadow(QFrame.Shadow.Plain)')
        lines.append(f'self.{widget_id}.setLineWidth(2)')
        lines.append(f'self.{widget_id}.setStyleSheet("color: #777777;")')
    else:
        raise ValueError(f"unknown widget kind: {kind}")

    if text is not None and kind != "combobox":
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'self.{widget_id}.setText("{escaped}")')
    if color:
        lines.append(f'self.{widget_id}.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)')
        lines.append(f'self.{widget_id}.setStyleSheet("background-color: {color};")')
    if font_family and font_size:
        escaped_family = font_family.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'self.{widget_id}.setFont(QFont("{escaped_family}", {font_size}))')
    if no_border:
        lines.append(f'self.{widget_id}.setFrame(False)')

    lines.append(f'self.{widget_id}.move({x}, {y})')
    lines.append(f'self.{widget_id}.adjustSize()')
    if width and height:
        lines.append(f'self.{widget_id}.resize({width}, {height})')
    return lines


def _method_source(widget_id, code):
    """Renames the stored `def on_event(self): ...` into a uniquely named
    method and indents it to nest inside the generated class body."""
    renamed = code.replace("def on_event(", f"def _{widget_id}_on_event(", 1)
    return textwrap.indent(renamed.rstrip() + "\n", "    ")


def _scope_code(code, entries, prefix):
    """Handler code was generated referencing sibling widgets on the same
    tab as `self.<id>`. Since exported ids are prefixed per tab to avoid
    collisions across tabs, rewrite those same-tab references to match."""
    for widget_id in entries:
        code = re.sub(rf'self\.{re.escape(widget_id)}\b', f'self.{prefix}{widget_id}', code)
    return code


def generate_source(tabs, width, height, class_name="GeneratedApp", window_title="My App"):
    """`tabs` is a list of {"title": str, "color": str | None, "entries": dict}."""
    init_lines = []
    method_blocks = []
    uses_alarm_clock = any(
        entry["kind"] == "alarmclock" for tab in tabs for entry in tab["entries"].values()
    )

    for tab_index, tab in enumerate(tabs):
        prefix = f"tab{tab_index}_"
        page_var = f"page_{tab_index}"
        entries = tab["entries"]

        init_lines.append(f'{page_var} = QWidget()')
        init_lines.append(f'{page_var}.setFixedSize({width}, {height})')
        if tab.get("color"):
            init_lines.append(f'{page_var}.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)')
            init_lines.append(f'{page_var}.setStyleSheet("background-color: {tab["color"]};")')
        init_lines.append("")

        radio_groups = {}  # group id -> [full_id, ...]

        for widget_id, entry in entries.items():
            full_id = f"{prefix}{widget_id}"
            widget = entry["widget"]

            if entry["kind"] == "radiobutton":
                group = entry.get("group") or widget_id
                radio_groups.setdefault(group, []).append(full_id)
            pos = widget.pos()
            size = widget.size()
            # Read live text (whatever the user actually typed, including
            # leading/trailing spaces) rather than a separately tracked
            # field that only updates via the rename dialog.
            live_text = widget.text() if hasattr(widget, "text") else None
            init_lines.extend(
                _create_lines(
                    full_id,
                    entry["kind"],
                    pos.x(),
                    pos.y(),
                    page_var,
                    live_text,
                    entry.get("color"),
                    size.width(),
                    size.height(),
                    entry.get("font_family"),
                    entry.get("font_size"),
                    entry.get("no_border", False),
                )
            )

            if entry["code"]:
                signal_name = SIGNAL_BY_KIND[entry["kind"]]
                init_lines.append(
                    f'self.{full_id}.{signal_name}.connect(self._{full_id}_on_event)'
                )
                scoped_code = _scope_code(entry["code"], entries, prefix)
                method_blocks.append(_method_source(full_id, scoped_code))

            init_lines.append("")

        for group_index, full_ids in enumerate(radio_groups.values()):
            group_var = f"{prefix}radio_group_{group_index}"
            init_lines.append(f'{group_var} = QButtonGroup(self)')
            for full_id in full_ids:
                init_lines.append(f'{group_var}.addButton(self.{full_id})')
            init_lines.append(f'self.{full_ids[0]}.setChecked(True)')
            init_lines.append("")

        title = tab["title"].replace('"', '\\"')
        init_lines.append(f'self.tabs.addTab({page_var}, "{title}")')
        init_lines.append("")

    init_body = textwrap.indent("\n".join(init_lines).rstrip(), "        ")

    source = HEADER_TEMPLATE.format(
        class_name=class_name,
        window_title=window_title,
        width=width,
        height=height,
        init_body=init_body,
        alarm_widget_source=_read_alarm_widget_source() if uses_alarm_clock else "",
    )
    if method_blocks:
        source += "\n" + "\n".join(method_blocks)
    source += FOOTER_TEMPLATE.format(class_name=class_name)
    return source


def export_to_file(tabs, width, height, file_path, class_name="GeneratedApp", window_title="My App"):
    source = generate_source(tabs, width, height, class_name, window_title)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(source)
    return source
