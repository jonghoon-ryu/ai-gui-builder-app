import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import winreg
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as _html_to_markdown
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def open_url(url):
    """Opens only http(s) links in the system's default browser. Anything
    else (file://, custom schemes, etc.) is rejected so this can't be used
    to launch arbitrary local files or apps."""
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 열 수 있습니다: {url!r}")
    QDesktopServices.openUrl(QUrl(url))


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def list_dir(path):
    """Returns the names of files/folders directly inside `path`."""
    return sorted(os.listdir(path))


def make_dir(path):
    """Creates `path` (and any missing parent directories)."""
    os.makedirs(path, exist_ok=True)


def move_file(src, dst):
    """Moves/renames a file, binary-safe (unlike read_file/write_file,
    which are text-mode - use this for images and other non-text files)."""
    shutil.move(src, dst)


_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _urlopen_with_retry(request, timeout=15, retries=3):
    """Retries on HTTP 429 (rate limited), waiting for the server's
    Retry-After header if given, else a short exponential backoff. Common
    when downloading many images from the same host back-to-back."""
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
    """Fetches an http(s) URL's body as text. Same scheme restriction as
    open_url - no file://, no other protocols. Sends a browser-like
    User-Agent since many sites 403 the default urllib one."""
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 가져올 수 있습니다: {url!r}")
    request = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})
    with _urlopen_with_retry(request) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_markdown(html):
    return _html_to_markdown(html)


def extract_images(html, base_url):
    """Returns [{"url": absolute_url, "alt": alt_text}, ...] for every
    <img> tag in the given HTML, with src resolved against base_url."""
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        images.append({"url": urljoin(base_url, src), "alt": img.get("alt") or ""})
    return images


def download_file(url, path):
    """Downloads an http(s) URL's raw bytes to a local file. Use this for
    binary content like images - fetch_url is for text/HTML."""
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 다운로드할 수 있습니다: {url!r}")
    request = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})
    with _urlopen_with_retry(request) as response:
        data = response.read()
    with open(path, "wb") as f:
        f.write(data)


def classify_image_with_claude(path):
    """Asks the locally installed `claude` CLI to look at the image and
    return a short, lowercase, folder-name-safe topic word. Falls back to
    "기타" if the CLI is missing, times out, or gives an unusable answer."""
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


_STARTUP_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

_DESCRIBABLE_KIND_LABELS = {
    "QPushButton": "버튼",
    "QLineEdit": "입력창",
    "QComboBox": "드롭박스",
    "QRadioButton": "라디오 버튼",
    "QFrame": "구분선",
    "AlarmClockPanel": "알람 시계",
    "WindowStatusPanel": "윈도우 현황판",
    "GitPanel": "git 비교 패널",
}

_ENTRY_KIND_LABELS = {
    "button": "버튼",
    "lineedit": "입력창",
    "urlbox": "URL 입력창",
    "dirbox": "디렉토리 입력창",
    "combobox": "드롭박스",
    "radiobutton": "라디오 버튼",
    "hline": "구분선",
    "vline": "구분선",
}

_PANEL_LABELS = {
    "alarmclock": "알람 시계",
    "windowstatus": "윈도우 현황판",
    "gitpanel": "git 비교 패널",
}

_PANEL_DESCRIPTIONS = {
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
}


def _tab_pages(page):
    """Walks up from a tab's page widget to the top-level window and reads
    its live `.tabs` widget - works for both the builder (CanvasWindow) and
    an exported standalone app (GeneratedApp), since both expose `.tabs`."""
    top = page.window()
    tabs_widget = getattr(top, "tabs", None)
    if tabs_widget is None:
        return []
    return [(tabs_widget.tabText(i), tabs_widget.widget(i)) for i in range(tabs_widget.count())]


def _describe_page_widgets(page):
    """Lists this tab's own widgets (direct children only, so a panel like
    AlarmClockPanel is described as one item rather than its internals).
    Used when `page` doesn't carry the builder's `entries` metadata (e.g.
    an exported standalone app), so only the widget kind/label is known -
    no click-behavior detail, since `instruction` text isn't exported."""
    items = []
    for child in page.findChildren(QWidget):
        if child.parent() is not page:
            continue
        label = _DESCRIBABLE_KIND_LABELS.get(type(child).__name__)
        if label is None:
            continue
        text = child.text().strip() if hasattr(child, "text") and callable(child.text) else ""
        items.append(f"  - {label}: {text}" if text else f"  - {label}")
    return items


def _describe_page_entries(page):
    """Like `_describe_page_widgets`, but for a builder `CanvasPage`: reads
    the natural-language `instruction` each widget's behavior was generated
    from, so a button is described by what it actually does when clicked,
    not just its label."""
    items = []
    for entry in page.entries.values():
        kind = entry.get("kind")
        if kind in _PANEL_DESCRIPTIONS:
            items.append(f"  - {_PANEL_LABELS[kind]}: {_PANEL_DESCRIPTIONS[kind]}")
            continue
        label = _ENTRY_KIND_LABELS.get(kind, kind)
        text = (entry.get("text") or "").strip()
        items.append(f'  - {label} "{text}"' if text else f"  - {label}")
        instruction = (entry.get("instruction") or "").strip()
        if instruction:
            instruction_lines = instruction.splitlines()
            items.append(f"    동작: {instruction_lines[0]}")
            items.extend(f"    {line}" for line in instruction_lines[1:])
    return items


def app_overview_text(page):
    """Live overview of the whole app: current tab list and how many
    widgets each holds. Recomputed on every call by reading the actual
    tab widget, so it never goes stale when tabs are added/removed/edited."""
    pages = _tab_pages(page)
    lines = [
        "이 앱은 사용자가 직접 만든 개인용 도구 모음입니다.",
        f"현재 {len(pages)}개의 탭이 있습니다:",
        "",
    ]
    for title, tab_page in pages:
        count = len(tab_page.entries) if hasattr(tab_page, "entries") else len(_describe_page_widgets(tab_page))
        lines.append(f"- {title} ({count}개 항목)")
    lines.append("")
    lines.append("각 탭의 자세한 사용법은 '각 탭에 대한 설명' 버튼을 눌러 확인하세요.")
    return "\n".join(lines)


def tab_usage_text(page):
    """Live per-tab breakdown of every widget - including, when available,
    what each button actually does when clicked. Recomputed on every call,
    so it never goes stale when tabs/widgets change."""
    lines = []
    for title, tab_page in _tab_pages(page):
        lines.append(f"[{title}]")
        if hasattr(tab_page, "entries"):
            widget_lines = _describe_page_entries(tab_page)
        else:
            widget_lines = _describe_page_widgets(tab_page)
        lines.extend(widget_lines if widget_lines else ["  (빈 탭)"])
        lines.append("")
    return "\n".join(lines).rstrip()


def show_text_dialog(parent, title, text):
    """Shows a titled, scrollable, read-only text window - for descriptions
    too long to comfortably fit in a QMessageBox."""
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
    """Opens a file picker starting in this app's `standalone` export
    folder. Returns the chosen path, or None if the user canceled."""
    standalone_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "standalone")
    path, _ = QFileDialog.getOpenFileName(
        parent,
        "시작 프로그램에 등록/삭제할 파일 선택",
        standalone_dir,
        "실행 파일 (*.exe);;모든 파일 (*.*)",
    )
    return path or None


def add_to_startup(path):
    """Registers `path` to launch at Windows login via the current user's
    registry Run key. The value name is the file's basename without
    extension, so re-registering the same file overwrites its own entry
    instead of duplicating it."""
    if not path:
        return False
    name = os.path.splitext(os.path.basename(path))[0]
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_RUN_KEY, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{path}"')
    finally:
        winreg.CloseKey(key)
    return True


def remove_from_startup(path):
    """Removes the Run-key entry that add_to_startup would have created for
    `path` (matched by basename without extension). Returns False if there
    was no such entry."""
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


def _make_delete_file(parent):
    def delete_file(path):
        """Deletes a file only after the user confirms in a blocking dialog —
        LLM-generated delete calls never run unattended."""
        reply = QMessageBox.question(
            parent,
            "삭제 확인",
            f"정말 삭제하시겠습니까?\n\n{path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        os.remove(path)

    return delete_file


SAFE_BUILTINS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "range": range,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "enumerate": enumerate,
    "isinstance": isinstance,
}

SIGNAL_BY_KIND = {
    "button": "clicked",
    "combobox": "currentIndexChanged",
    "lineedit": "returnPressed",
    "urlbox": "returnPressed",
    "dirbox": "returnPressed",
    "radiobutton": "clicked",
}


class HandlerCompileError(Exception):
    pass


def compile_handler(code, canvas):
    """Compiles generated `def on_event(self): ...` source into a callable
    bound to `canvas`, with runtime errors caught and shown instead of
    crashing the live builder."""
    namespace = {
        "__builtins__": SAFE_BUILTINS,
        "QMessageBox": QMessageBox,
        "QInputDialog": QInputDialog,
        "open_url": open_url,
        "read_file": read_file,
        "write_file": write_file,
        "delete_file": _make_delete_file(canvas),
        "list_dir": list_dir,
        "make_dir": make_dir,
        "move_file": move_file,
        "fetch_url": fetch_url,
        "html_to_markdown": html_to_markdown,
        "extract_images": extract_images,
        "download_file": download_file,
        "classify_image_with_claude": classify_image_with_claude,
        "show_text_dialog": show_text_dialog,
        "pick_startup_file": pick_startup_file,
        "add_to_startup": add_to_startup,
        "remove_from_startup": remove_from_startup,
        "app_overview_text": app_overview_text,
        "tab_usage_text": tab_usage_text,
    }
    try:
        exec(code, namespace)
    except SyntaxError as exc:
        raise HandlerCompileError(f"코드 컴파일 오류: {exc}") from exc

    handler = namespace.get("on_event")
    if not callable(handler):
        raise HandlerCompileError("`on_event(self)` 함수를 찾을 수 없습니다.")

    def bound_handler(*_args, **_kwargs):
        try:
            handler(canvas)
        except ImportError:
            QMessageBox.warning(
                canvas,
                "실행 오류",
                "이 동작이 import가 필요한 기능을 쓰려고 해서 실행할 수 없습니다.\n"
                "보안을 위해 생성된 코드에서는 import를 쓸 수 없고, 아래 함수만 사용 가능합니다:\n"
                "open_url / read_file / write_file / delete_file / list_dir / make_dir / "
                "move_file / fetch_url / html_to_markdown / extract_images / download_file / "
                "classify_image_with_claude / show_text_dialog / pick_startup_file / "
                "add_to_startup / remove_from_startup / app_overview_text / tab_usage_text\n\n"
                "'동작 설정'에서 원하는 동작을 이 함수들로 표현되게 다시 설명해서 재생성해보세요.",
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            QMessageBox.warning(
                canvas, "실행 오류", f"동작 실행 중 오류가 발생했습니다:\n{exc}"
            )

    return bound_handler


def bind_handler(widget, widget_kind, bound_handler, previous_handler=None):
    signal = getattr(widget, SIGNAL_BY_KIND[widget_kind])
    if previous_handler is not None:
        try:
            signal.disconnect(previous_handler)
        except (RuntimeError, TypeError):
            pass
    signal.connect(bound_handler)
    return bound_handler
