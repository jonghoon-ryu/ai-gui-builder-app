import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as _html_to_markdown
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QInputDialog, QMessageBox


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
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "기타"
    if result.returncode != 0 or not result.stdout.strip():
        return "기타"
    word = "".join(ch for ch in result.stdout.strip().split()[0] if ch.isalnum() or ch in "-_")
    return word or "기타"


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
                "classify_image_with_claude\n\n"
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
