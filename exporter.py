import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

from alarm_widget import _serialize_alarms
from code_binder import SIGNAL_BY_KIND

_ALARM_WIDGET_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "alarm_widget.py"
)
_WINDOW_STATUS_WIDGET_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "window_status_widget.py"
)
_GIT_WIDGET_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "git_widget.py"
)
_GVF_WIDGET_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "gvf_widget.py"
)
_TAB_BAR_SOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tab_bar.py")
_THEME_SOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme.py")


def _read_alarm_widget_source():
    """Embeds alarm_widget.py's actual source into the exported app instead
    of hand-duplicating the class as a string template - keeps the builder
    and the standalone export from drifting apart."""
    with open(_ALARM_WIDGET_SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _read_window_status_widget_source():
    with open(_WINDOW_STATUS_WIDGET_SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _read_git_widget_source():
    with open(_GIT_WIDGET_SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _read_gvf_widget_source():
    with open(_GVF_WIDGET_SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _read_tab_bar_source():
    """Every export has tabs, so unlike the alarm/window-status widgets this
    one is always embedded (not conditional on a widget kind being used)."""
    with open(_TAB_BAR_SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _read_theme_source():
    """Same reasoning as the tab bar - every export should look like the
    builder, so the theme is always embedded rather than made conditional."""
    with open(_THEME_SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()

HEADER_TEMPLATE = '''import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import winreg
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as _html_to_markdown
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
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
    QTextEdit,
    QVBoxLayout,
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
            encoding="utf-8",
            errors="replace",
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


_STARTUP_RUN_KEY = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"

_DESCRIBABLE_KIND_LABELS = {{
    "QPushButton": "버튼",
    "QLineEdit": "입력창",
    "QComboBox": "드롭박스",
    "QRadioButton": "라디오 버튼",
    "QFrame": "구분선",
    "AlarmClockPanel": "알람 시계",
    "WindowStatusPanel": "윈도우 현황판",
    "GitPanel": "git 비교 패널",
    "GvfPanel": "FPGA 자원 현황판",
    "FpgaAcquisitionPanel": "FPGA 자원 취득판",
    "FpgaLoadingPanel": "FPGA loading판",
}}

_ENTRY_KIND_LABELS = {{
    "button": "버튼",
    "lineedit": "입력창",
    "urlbox": "URL 입력창",
    "dirbox": "디렉토리 입력창",
    "combobox": "드롭박스",
    "radiobutton": "라디오 버튼",
    "hline": "구분선",
    "vline": "구분선",
}}

_PANEL_LABELS = {{
    "alarmclock": "알람 시계",
    "windowstatus": "윈도우 현황판",
    "gitpanel": "git 비교 패널",
    "gvfpanel": "FPGA 자원 현황판",
    "fpgaacquisition": "FPGA 자원 취득판",
    "fpgaloading": "FPGA loading판",
}}

_PANEL_DESCRIPTIONS = {{
    "alarmclock": (
        "일회성/주기적 알람을 등록하면 설정한 시간에 20cm x 20cm 팝업 창으로 알려줍니다. "
        "왼쪽 버튼으로 알람을 추가하고, 자연어 입력칸에 문장을 쓰면 claude CLI가 알아서 "
        "일회성/주기적 알람으로 등록합니다."
    ),
    "windowstatus": (
        "Windows 버전/CPU/메모리/디스크(C·D·E) 현황을 보여주고, '상위 프로세스'/'시작 프로그램 "
        "목록'/'시스템 변수 바로보기' 버튼을 누르면 각각 해당 정보 창이 뜹니다. 휴지통과 temp "
        "폴더는 각각 '목록' 버튼으로 파일 목록을, '휴지통 비우기'/'temp 파일 비우기' 버튼으로 "
        "확인 후 비웁니다."
    ),
    "gitpanel": (
        "local/remote 저장소를 최대 6쌍 등록해두는 패널입니다. 각 쌍의 '비교' 버튼을 누르면 local과 "
        "remote의 HEAD 커밋을 비교해 '비교결과' 버튼 색으로 보여주고(초록=동일, 빨강=다름), 'stash' "
        "버튼을 누르면 커밋 안 된 변경 파일의 원본/현재 버전을 백업합니다. 'local drive 검색' 버튼은 "
        "C/D/E 드라이브를 훑어 git 저장소를 찾아 local 칸을 채우고, '전체 status check' 버튼은 "
        "remote/local이 둘 다 채워진 쌍을 한꺼번에 비교합니다."
    ),
    "gvfpanel": (
        "FPGA 자원 현황을 보여주는 패널입니다 (현재는 레이아웃만 있는 뼈대 상태 - 표시창 3개(FPGA "
        "번호 1/2/3)와 각각의 시작/종료 시간 표시 자리, '반납' 버튼만 있고, 실제 데이터 연결이나 "
        "'반납' 버튼의 실제 동작은 아직 없습니다)."
    ),
    "fpgaacquisition": (
        "FPGA 자원 취득 설정 패널입니다 (현재는 레이아웃만 있는 뼈대 상태 - '아이디' 문자열 입력, "
        "'FPGA 획득 마지막 시도' 시간 입력, 'FPGA 취득 간격'(분 단위, 기본 120분, 조절 가능) 입력, "
        "'max FPGA 취득'(최솟값 1, 기본 1, 조절 가능) 입력, '명령어 입력 디렉토리' 경로 입력(폴더 "
        "아이콘으로 선택), 'FPGA 대기열 삭제' 버튼, 누르면 '동작중'으로 바뀌는 '시작' 버튼과 누르면 "
        "시작 버튼을 '다시 시작'으로 바꾸는 '중지' 버튼만 있고, 실제로 그 간격마다 자동 획득을 "
        "시도하거나 그 디렉토리에서 명령어를 실행하거나 대기열 삭제/시작/중지하는 로직은 아직 "
        "없습니다)."
    ),
    "fpgaloading": (
        "FPGA loading 설정 패널입니다 (현재는 레이아웃만 있는 뼈대 상태 - 드롭박스 3개(FPGA 버전 "
        "고정 목록, 'FPGA 자원 현황' 패널의 'FPGA 번호' 표시창을 열 때마다 다시 읽어서 채우는 "
        "드롭박스, 메모리 타입 고정 목록) + '시작' 버튼만 있고, 실제로 '시작' 버튼을 눌렀을 때 "
        "무슨 일이 일어나는지는 아직 없습니다)."
    ),
}}


def _tab_pages(page):
    top = page.window()
    tabs_widget = getattr(top, "tabs", None)
    if tabs_widget is None:
        return []
    return [(tabs_widget.tabText(i), tabs_widget.widget(i)) for i in range(tabs_widget.count())]


def _describe_page_widgets(page):
    items = []
    for child in page.findChildren(QWidget):
        if child.parent() is not page:
            continue
        label = _DESCRIBABLE_KIND_LABELS.get(type(child).__name__)
        if label is None:
            continue
        text = child.text().strip() if hasattr(child, "text") and callable(child.text) else ""
        items.append(f"  - {{label}}: {{text}}" if text else f"  - {{label}}")
    return items


def _describe_page_entries(page):
    items = []
    for entry in page.entries.values():
        kind = entry.get("kind")
        if kind in _PANEL_DESCRIPTIONS:
            items.append(f"  - {{_PANEL_LABELS[kind]}}: {{_PANEL_DESCRIPTIONS[kind]}}")
            continue
        label = _ENTRY_KIND_LABELS.get(kind, kind)
        text = (entry.get("text") or "").strip()
        items.append(f'  - {{label}} "{{text}}"' if text else f"  - {{label}}")
        instruction = (entry.get("instruction") or "").strip()
        if instruction:
            instruction_lines = instruction.splitlines()
            items.append(f"    동작: {{instruction_lines[0]}}")
            items.extend(f"    {{line}}" for line in instruction_lines[1:])
    return items


def app_overview_text(page):
    pages = _tab_pages(page)
    lines = [
        "이 앱은 사용자가 직접 만든 개인용 도구 모음입니다.",
        f"현재 {{len(pages)}}개의 탭이 있습니다:",
        "",
    ]
    for title, tab_page in pages:
        count = len(tab_page.entries) if hasattr(tab_page, "entries") else len(_describe_page_widgets(tab_page))
        lines.append(f"- {{title}} ({{count}}개 항목)")
    lines.append("")
    lines.append("각 탭의 자세한 사용법은 '각 탭에 대한 설명' 버튼을 눌러 확인하세요.")
    return "\\n".join(lines)


def tab_usage_text(page):
    lines = []
    for title, tab_page in _tab_pages(page):
        lines.append(f"[{{title}}]")
        if hasattr(tab_page, "entries"):
            widget_lines = _describe_page_entries(tab_page)
        else:
            widget_lines = _describe_page_widgets(tab_page)
        lines.extend(widget_lines if widget_lines else ["  (빈 탭)"])
        lines.append("")
    return "\\n".join(lines).rstrip()


def show_text_dialog(parent, title, text):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.resize(520, 480)
    layout = QVBoxLayout(dialog)
    text_edit = QTextEdit()
    text_edit.setReadOnly(True)
    text_edit.setPlainText(text)
    layout.addWidget(text_edit)
    close_button = QPushButton("닫기")
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    dialog.exec()


def pick_startup_file(parent):
    standalone_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "standalone")
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "시작 프로그램에 등록/삭제할 파일 선택",
        standalone_dir,
        "실행 파일 (*.exe);;모든 파일 (*.*)",
    )
    return path or None


def add_to_startup(path):
    if not path:
        return False
    name = os.path.splitext(os.path.basename(path))[0]
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_RUN_KEY, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{{path}}"')
    finally:
        winreg.CloseKey(key)
    return True


def remove_from_startup(path):
    if not path:
        return False
    name = os.path.splitext(os.path.basename(path))[0]
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_RUN_KEY, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.DeleteValue(key, name)
    except FileNotFoundError:
        return False
    finally:
        winreg.CloseKey(key)
    return True


{tab_bar_source}
{theme_source}
{alarm_widget_source}
{window_status_widget_source}
{git_widget_source}
{gvf_widget_source}
class {class_name}(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("{window_title}")
        self.resize({width}, {height})
        self.tabs = QTabWidget()
        self.tabs.setTabBar(ColorTabBar())
        self.setCentralWidget(self.tabs)

{init_body}
'''

FOOTER_TEMPLATE = '''

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    window = {class_name}()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
'''


def _create_lines(
    widget_id, kind, x, y, parent_var, text=None, color=None, width=None, height=None,
    font_family=None, font_size=None, no_border=False, widget=None,
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
            f'self.{widget_id}.style().standardIcon(QStyle.StandardPixmap.SP_DirLinkIcon), '
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
        # Seed the exported panel with whatever alarms exist in the builder
        # right now, instead of it always starting empty.
        alarms_data = _serialize_alarms(widget._alarms) if widget is not None else []
        lines.append(
            f'self.{widget_id} = AlarmClockPanel({parent_var}, initial_alarms={alarms_data!r})'
        )
    elif kind == "windowstatus":
        lines.append(f'self.{widget_id} = WindowStatusPanel({parent_var})')
    elif kind == "gvfpanel":
        lines.append(f'self.{widget_id} = GvfPanel({parent_var})')
    elif kind == "fpgaacquisition":
        lines.append(f'self.{widget_id} = FpgaAcquisitionPanel({parent_var})')
    elif kind == "fpgaloading":
        lines.append(f'self.{widget_id} = FpgaLoadingPanel({parent_var})')
    elif kind == "gitpanel":
        # Seed the exported panel with whatever remote/local pairs exist in
        # the builder right now, instead of it always starting empty.
        pairs_data = (
            [
                {"remote": box.remote_edit.text(), "local": box.local_edit.text()}
                for box in widget.pair_boxes
            ]
            if widget is not None
            else []
        )
        lines.append(
            f'self.{widget_id} = GitPanel({parent_var}, initial_pairs={pairs_data!r})'
        )
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
        # Scoped by object name (id-selector), not a bare declaration or a
        # type-selector, so this color doesn't cascade into any dialog a
        # click handler might open on/under this widget - see the matching
        # comment on canvas_window.py's _apply_scoped_background. A bare
        # declaration cascades into everything; a type-selector would still
        # leak into same-type widgets nested *inside* such a dialog (e.g. a
        # QPushButton "확인" button inside a popup opened from a colored
        # QPushButton).
        lines.append(f'self.{widget_id}.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)')
        lines.append(f'self.{widget_id}.setObjectName("{widget_id}")')
        lines.append(f'self.{widget_id}.setStyleSheet("#{widget_id} {{ background-color: {color}; }}")')
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
    uses_window_status = any(
        entry["kind"] == "windowstatus" for tab in tabs for entry in tab["entries"].values()
    )
    uses_git_panel = any(
        entry["kind"] == "gitpanel" for tab in tabs for entry in tab["entries"].values()
    )
    uses_gvf_panel = any(
        entry["kind"] in ("gvfpanel", "fpgaacquisition", "fpgaloading")
        for tab in tabs
        for entry in tab["entries"].values()
    )

    for tab_index, tab in enumerate(tabs):
        prefix = f"tab{tab_index}_"
        page_var = f"page_{tab_index}"
        entries = tab["entries"]

        init_lines.append(f'{page_var} = QWidget()')
        # Not setFixedSize here - the page should just fill whatever content
        # area QTabWidget gives it (window size minus the tab bar's own
        # height), exactly like the builder's CanvasPage. Fixing it to the
        # full window size here would make the *window* grow by the tab
        # bar's height to fit it, since nothing else constrains the window.
        if tab.get("color"):
            init_lines.append(f'{page_var}.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)')
            # Scoped by object name (see the comment on the widget-color
            # case above) so this color doesn't cascade into dialogs opened
            # from buttons/panels living on this tab.
            init_lines.append(f'{page_var}.setObjectName("{page_var}")')
            init_lines.append(f'{page_var}.setStyleSheet("#{page_var} {{ background-color: {tab["color"]}; }}")')
        init_lines.append("")

        radio_groups = {}  # group id -> [(full_id, is_checked), ...]

        for widget_id, entry in entries.items():
            full_id = f"{prefix}{widget_id}"
            widget = entry["widget"]

            if entry["kind"] == "radiobutton":
                group = entry.get("group") or widget_id
                radio_groups.setdefault(group, []).append((full_id, widget.isChecked()))
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
                    widget,
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

        for group_index, members in enumerate(radio_groups.values()):
            group_var = f"{prefix}radio_group_{group_index}"
            init_lines.append(f'{group_var} = QButtonGroup(self)')
            for full_id, _is_checked in members:
                init_lines.append(f'{group_var}.addButton(self.{full_id})')
            # Preserve whichever option was actually selected in the builder;
            # fall back to the first member if none was (shouldn't happen).
            checked_id = next((fid for fid, is_checked in members if is_checked), members[0][0])
            init_lines.append(f'self.{checked_id}.setChecked(True)')
            init_lines.append("")

        title = tab["title"].replace('"', '\\"')
        init_lines.append(f'self.tabs.addTab({page_var}, "{title}")')
        if tab.get("color"):
            init_lines.append(
                f'self.tabs.tabBar().set_tab_color({tab_index}, QColor("{tab["color"]}"))'
            )
        init_lines.append("")

    init_body = textwrap.indent("\n".join(init_lines).rstrip(), "        ")

    source = HEADER_TEMPLATE.format(
        class_name=class_name,
        window_title=window_title,
        width=width,
        height=height,
        init_body=init_body,
        tab_bar_source=_read_tab_bar_source(),
        theme_source=_read_theme_source(),
        alarm_widget_source=_read_alarm_widget_source() if uses_alarm_clock else "",
        window_status_widget_source=(
            _read_window_status_widget_source() if uses_window_status else ""
        ),
        git_widget_source=_read_git_widget_source() if uses_git_panel else "",
        gvf_widget_source=_read_gvf_widget_source() if uses_gvf_panel else "",
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


def build_exe(tabs, width, height, dest_exe_path, class_name="GeneratedApp", window_title="My App"):
    """Generates the app source (same as export_to_file), then runs
    PyInstaller (via this venv's own `python -m PyInstaller`, so it doesn't
    depend on a global `pyinstaller` on PATH) to produce a single-file .exe,
    and copies the result to `dest_exe_path`. Raises RuntimeError with
    PyInstaller's own error output if the build fails. Takes roughly
    1-2 minutes - callers should run this off the UI thread."""
    source = generate_source(tabs, width, height, class_name, window_title)
    exe_stem = os.path.splitext(os.path.basename(dest_exe_path))[0] or "app"

    with tempfile.TemporaryDirectory(prefix="ai_gui_builder_exe_") as tmp_dir:
        src_path = os.path.join(tmp_dir, "app_src.py")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(source)

        dist_dir = os.path.join(tmp_dir, "dist")
        work_dir = os.path.join(tmp_dir, "build")

        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "PyInstaller",
                    "--onefile", "--windowed", "--noconfirm",
                    "--distpath", dist_dir,
                    "--workpath", work_dir,
                    "--specpath", tmp_dir,
                    "--name", exe_stem,
                    src_path,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "PyInstaller를 찾을 수 없습니다. 이 빌더의 venv에 "
                "`pip install pyinstaller`가 되어 있어야 합니다."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("빌드가 10분을 넘겨 시간 초과되었습니다.") from exc

        if result.returncode != 0:
            tail = "\n".join(result.stderr.strip().splitlines()[-20:])
            raise RuntimeError(f"PyInstaller 빌드에 실패했습니다:\n{tail}")

        built_exe = os.path.join(dist_dir, f"{exe_stem}.exe")
        if not os.path.exists(built_exe):
            raise RuntimeError("빌드는 성공했지만 결과 exe 파일을 찾을 수 없습니다.")

        shutil.copy2(built_exe, dest_exe_path)
