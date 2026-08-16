"""'git' 위젯: local/remote 6쌍 비교·stash + 전체 status check.

Only uses the standard library plus the `git` executable via subprocess (no
extra pip packages), so standalone-exported apps embedding this widget still
only need PySide6 to run (see CLAUDE.md's export guarantee). The exported
app's user still needs `git` itself installed and on PATH, same as the
"동작 설정" natural-language features need `claude`.
"""

import ctypes
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

GIT_BIN = "git"
_GIT_TIMEOUT_SECONDS = 20
RESULT_SAME_COLOR = "#3aa655"
RESULT_DIFF_COLOR = "#d64545"
_SKIP_DIR_NAMES = {".git", "node_modules", "$RECYCLE.BIN", "System Volume Information"}

# "local drive 검색"/"전체 status check" 상단 버튼 2개를 나머지 평범한 흰 버튼들보다
# 진하게 강조하기 위한 스타일 (탭 전체를 작동시키는 주요 동작 버튼이라 눈에 띄어야 함).
_PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: #5b72e0;
    color: #ffffff;
    border: 1px solid #4a5fc7;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #4a5fc7;
}
QPushButton:pressed {
    background-color: #3d4fb0;
}
QPushButton:disabled {
    background-color: #aab2e8;
    color: #f0f0f0;
    border-color: #aab2e8;
}
"""

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
GIT_PANEL_STATE_FILE = os.path.join(_APP_DATA_DIR, "git_panel_state.json")
_LEGACY_GIT_PANEL_STATE_FILE = os.path.join(_STATE_DIR, "git_panel_state.json")


def _migrate_legacy_git_panel_state():
    """One-time move of a pre-appData/ git_panel_state.json into appData/, so
    upgrading to this layout doesn't silently lose already-saved pairs."""
    if os.path.exists(GIT_PANEL_STATE_FILE) or not os.path.exists(_LEGACY_GIT_PANEL_STATE_FILE):
        return
    try:
        os.makedirs(_APP_DATA_DIR, exist_ok=True)
        shutil.move(_LEGACY_GIT_PANEL_STATE_FILE, GIT_PANEL_STATE_FILE)
    except OSError:
        pass


def set_state_dir(path):
    """Redirects where the git panel's 6 remote/local pairs are read/written
    - called by canvas_window.py whenever the active 틀 changes, so this
    data follows whichever builder_framework/<이름>/ is currently active
    instead of always sitting next to this .py file. Never called for a
    standalone-exported app (no concept of "틀" there)."""
    global _STATE_DIR, _APP_DATA_DIR, GIT_PANEL_STATE_FILE, _LEGACY_GIT_PANEL_STATE_FILE
    _STATE_DIR = path
    _APP_DATA_DIR = os.path.join(_STATE_DIR, "appData")
    GIT_PANEL_STATE_FILE = os.path.join(_APP_DATA_DIR, "git_panel_state.json")
    _LEGACY_GIT_PANEL_STATE_FILE = os.path.join(_STATE_DIR, "git_panel_state.json")
    _migrate_legacy_git_panel_state()


_migrate_legacy_git_panel_state()


def _run_git(args, cwd=None, timeout=_GIT_TIMEOUT_SECONDS):
    """Returns (ok, stdout, stderr) - never raises for a missing repo/remote,
    only for git itself being unavailable or timing out."""
    try:
        result = subprocess.run(
            [GIT_BIN, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError:
        return False, "", "git 명령을 찾을 수 없습니다. git이 설치되어 있고 PATH에 등록되어 있어야 합니다."
    except subprocess.TimeoutExpired:
        return False, "", "git 명령이 시간 초과되었습니다."
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def _existing_drive_roots():
    return [f"{letter}:\\" for letter in "CDE" if os.path.exists(f"{letter}:\\")]


DRIVE_SEARCH_MAX_DEPTH = 3


def find_git_repos(drive_roots, limit=None, max_depth=DRIVE_SEARCH_MAX_DEPTH):
    """Walks each drive root looking for a `.git` entry, skipping into it
    (and a few other huge/irrelevant folders) once found. Only descends
    `max_depth` levels of subdirectories below the drive root itself (a
    full-drive walk is inherently slow) - a repo nested deeper than that
    won't be found. Stops as soon as `limit` repos have been found, if
    given. Callers should run this off the UI thread regardless, since even
    a depth-capped walk can take a moment on a large drive."""
    found = []
    for root in drive_roots:
        root_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _e: None):
            if ".git" in dirnames or ".git" in filenames:
                found.append(dirpath)
                if limit is not None and len(found) >= limit:
                    return found
            depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
            if depth >= max_depth:
                dirnames[:] = []
            else:
                dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES]
    return found


def get_local_head(path):
    """Returns (commit_hash, branch_name)."""
    ok, out, err = _run_git(["rev-parse", "HEAD"], cwd=path)
    if not ok:
        raise RuntimeError(f"로컬 저장소를 읽을 수 없습니다: {err or out or '알 수 없는 오류'}")
    ok2, branch, _err2 = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    return out, (branch if ok2 else "?")


def get_remote_head(url, ref="HEAD"):
    ok, out, err = _run_git(["ls-remote", url, ref])
    if not ok:
        raise RuntimeError(f"원격 저장소를 읽을 수 없습니다: {err or out or '알 수 없는 오류'}")
    if not out:
        raise RuntimeError("원격 저장소에서 커밋 정보를 찾을 수 없습니다.")
    return out.split()[0]


def compare_repos(local_path, remote_url):
    local_hash, local_branch = get_local_head(local_path)
    remote_hash = get_remote_head(remote_url)
    return {
        "local_hash": local_hash,
        "local_branch": local_branch,
        "remote_hash": remote_hash,
        "same": local_hash == remote_hash,
    }


def list_dirty_files(path):
    """Tracked files with uncommitted changes (staged or not) - untracked
    files are excluded since they have no committed 'original' to compare."""
    ok1, out1, err1 = _run_git(["diff", "--name-only"], cwd=path)
    ok2, out2, err2 = _run_git(["diff", "--cached", "--name-only"], cwd=path)
    if not (ok1 and ok2):
        raise RuntimeError(f"변경된 파일 목록을 가져올 수 없습니다: {err1 or err2 or '이 경로가 git 저장소인지 확인하세요.'}")
    files = {f for f in out1.splitlines() if f} | {f for f in out2.splitlines() if f}
    return sorted(files)


def _git_show_bytes(cwd, rel_path):
    try:
        result = subprocess.run(
            [GIT_BIN, "show", f"HEAD:{rel_path}"],
            cwd=cwd,
            capture_output=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"{rel_path}의 원본 버전을 가져오지 못했습니다: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"{rel_path}의 원본 버전을 가져오지 못했습니다 (HEAD에 없는 새 파일일 수 있음)."
        )
    return result.stdout


def stash_backup(path):
    """For every tracked file with uncommitted changes, saves both the
    last-committed ('.orig') and current working ('.current') content into
    a timestamped backup folder next to the repo. Returns
    (backup_folder, saved_count) - (None, 0) if nothing was dirty."""
    dirty_files = list_dirty_files(path)
    if not dirty_files:
        return None, 0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(path, f"_stash_backup_{timestamp}")

    saved = 0
    for rel_path in dirty_files:
        dest_dir = os.path.join(backup_root, os.path.dirname(rel_path))
        os.makedirs(dest_dir, exist_ok=True)
        base_name = os.path.basename(rel_path)

        try:
            original_bytes = _git_show_bytes(path, rel_path)
            with open(os.path.join(dest_dir, base_name + ".orig"), "wb") as f:
                f.write(original_bytes)
        except RuntimeError:
            pass  # new/never-committed file - nothing to save as "original"

        try:
            with open(os.path.join(path, rel_path), "rb") as f:
                current_bytes = f.read()
        except OSError:
            continue
        with open(os.path.join(dest_dir, base_name + ".current"), "wb") as f:
            f.write(current_bytes)
        saved += 1

    return backup_root, saved


# ---- Locked-file handling (for "git clone": wiping the local folder can hit
# files another running process still has open) ---------------------------

_CCH_RM_SESSION_KEY = 32
_CCH_RM_MAX_APP_NAME = 255
_CCH_RM_MAX_SVC_NAME = 63
_RM_ERROR_MORE_DATA = 234
_PROCESS_TERMINATE = 0x0001


class _RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [
        ("dwProcessId", wintypes.DWORD),
        ("ProcessStartTime", wintypes.FILETIME),
    ]


class _RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [
        ("Process", _RM_UNIQUE_PROCESS),
        ("strAppName", ctypes.c_wchar * (_CCH_RM_MAX_APP_NAME + 1)),
        ("strServiceShortName", ctypes.c_wchar * (_CCH_RM_MAX_SVC_NAME + 1)),
        ("ApplicationType", ctypes.c_int),
        ("AppStatus", wintypes.ULONG),
        ("TSSessionId", wintypes.DWORD),
        ("bRestartable", wintypes.BOOL),
    ]


def find_locking_processes(path):
    """Returns [(pid, name), ...] of processes currently holding `path`
    open, via the Windows Restart Manager API (the same mechanism behind
    "Resource Monitor"'s file-handle search). Returns [] if nothing has it
    locked or the API call fails for any reason - callers treat that the
    same as "unknown, nothing to offer the user"."""
    try:
        rstrtmgr = ctypes.WinDLL("rstrtmgr")
    except OSError:
        return []

    session = wintypes.DWORD()
    session_key = ctypes.create_unicode_buffer(_CCH_RM_SESSION_KEY + 1)
    if rstrtmgr.RmStartSession(ctypes.byref(session), 0, session_key) != 0:
        return []
    try:
        file_array = (ctypes.c_wchar_p * 1)(path)
        if rstrtmgr.RmRegisterResources(session, 1, file_array, 0, None, 0, None) != 0:
            return []

        needed = wintypes.UINT(0)
        count = wintypes.UINT(0)
        reboot_reasons = wintypes.DWORD(0)
        result = rstrtmgr.RmGetList(
            session, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reboot_reasons)
        )
        if result not in (0, _RM_ERROR_MORE_DATA) or needed.value == 0:
            return []

        count.value = needed.value
        proc_array = (_RM_PROCESS_INFO * needed.value)()
        result = rstrtmgr.RmGetList(
            session, ctypes.byref(needed), ctypes.byref(count), proc_array, ctypes.byref(reboot_reasons)
        )
        if result != 0:
            return []
        return [(p.Process.dwProcessId, p.strAppName) for p in proc_array[: count.value]]
    finally:
        rstrtmgr.RmEndSession(session)


def terminate_process(pid):
    """Force-terminates a process by PID. Returns True on success."""
    handle = ctypes.windll.kernel32.OpenProcess(_PROCESS_TERMINATE, False, pid)
    if not handle:
        return False
    try:
        return bool(ctypes.windll.kernel32.TerminateProcess(handle, 1))
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _clear_readonly_and_retry(path):
    """A plain remove/rmtree commonly fails on a `.git` folder on Windows
    even with nothing else touching it, because git marks its object/pack
    files read-only - not an actual process lock, so Restart Manager would
    find nothing. Clears the read-only attribute recursively and retries
    before ever bothering the user about a "locking process". Returns True
    if `path` is gone afterward."""

    def _on_rmtree_error(func, target, _exc_info):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    try:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, onerror=_on_rmtree_error)
        else:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
    except OSError:
        pass
    return not os.path.exists(path)


def clear_directory(path, on_locked_file, exclude=None):
    """Deletes everything directly under `path` (files and subfolders
    alike) except names listed in `exclude`, leaving `path` itself in
    place. When a file can't be removed even after clearing read-only
    attributes (see `_clear_readonly_and_retry`) - i.e. another process
    genuinely has it open - calls `on_locked_file(file_path, [(pid, name),
    ...])`, which should return True to retry the deletion (e.g. after
    killing the offending process(es)) or False to give up entirely.
    Returns True if `path` ended up fully cleared (aside from anything in
    `exclude`), False if something else was left behind (caller gave up on
    it)."""
    exclude = exclude or set()
    ok = True
    for entry in os.listdir(path):
        if entry in exclude:
            continue
        full_path = os.path.join(path, entry)
        if _clear_readonly_and_retry(full_path):
            continue
        while True:
            locking = find_locking_processes(full_path)
            if not on_locked_file(full_path, locking):
                ok = False
                break
            # on_locked_file() said "retry" (e.g. it just killed the
            # offending process(es)) - Windows can take a brief moment to
            # fully release a handle after the owning process actually
            # dies, so a removal attempted the instant TerminateProcess()
            # returns can still fail. Give it a little room before asking
            # find_locking_processes for another look.
            removed = False
            for _ in range(10):
                if _clear_readonly_and_retry(full_path):
                    removed = True
                    break
                time.sleep(0.2)
            if removed:
                break
    return ok


def _load_git_panel_state():
    if not os.path.exists(GIT_PANEL_STATE_FILE):
        return []
    try:
        with open(GIT_PANEL_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def _save_git_panel_state(pairs):
    try:
        os.makedirs(_APP_DATA_DIR, exist_ok=True)
        with open(GIT_PANEL_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(pairs, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


class _BatchCompareWorker(QThread):
    """Runs compare_repos() for every (index, local, remote) job off the UI
    thread, since each comparison makes a network call (git ls-remote) that
    could hang or take a while - emits one result per job as it completes
    rather than waiting for all of them, so boxes update as they finish."""

    result_ready = Signal(int, object)  # (box_index, result_dict | error_message)
    finished_all = Signal()

    def __init__(self, jobs, parent=None):
        super().__init__(parent)
        self._jobs = jobs

    def run(self):
        for index, local, remote in self._jobs:
            try:
                result = compare_repos(local, remote)
            except RuntimeError as exc:
                self.result_ready.emit(index, str(exc))
            else:
                self.result_ready.emit(index, result)
        self.finished_all.emit()


class _GitScanWorker(QThread):
    """Finds up to `limit` git repos on the given drives, off the UI thread
    (a drive walk is slow) - used to auto-fill empty 'local' boxes before
    running the full status check."""

    succeeded = Signal(list)
    failed = Signal(str)

    def __init__(self, drive_roots, limit, parent=None):
        super().__init__(parent)
        self._drive_roots = drive_roots
        self._limit = limit

    def run(self):
        try:
            repos = find_git_repos(self._drive_roots, limit=self._limit)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(repos)


class _RepoPairBox(QFrame):
    """One bordered remote/local pair: URL + directory inputs (matching the
    urlbox/dirbox trailing-icon pattern) plus '비교'(compare)/'stash'
    buttons for that pair."""

    def __init__(self, remote_text, local_text, save_callback, parent=None):
        super().__init__(parent)
        self._save_callback = save_callback
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        # 탭 바탕색이 무엇이든(사용자가 우클릭 메뉴로 바꿀 수 있음) 항상 그대로 비쳐
        # 보이도록 배경은 투명하게 두고 테두리만 스타일시트로 명시함 (스타일시트를
        # 하나라도 주면 setFrameShape의 네이티브 테두리가 무시되는 Qt 특성 때문에
        # border도 같이 지정해야 함).
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "_RepoPairBox { background-color: transparent; border: 1px solid #ced2db;"
            " border-radius: 5px; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # remote/local 라벨 폭을 통일해야 두 QLineEdit(stretch=1)의 시작 x좌표가
        # 같아지고, 결과적으로 두 입력창의 실제 폭도 서로 같아짐 ("remote:"가
        # "local:"보다 길어서 라벨 폭을 맞추지 않으면 입력창 폭이 서로 달라짐).
        # +12px 여유를 둬서 라벨(=remote/local 텍스트 창) 폭을 조금 더 넓히고, 그만큼
        # 뒤에 오는 입력창(stretch=1)이 조금 줄어듦. "local:"처럼 원래 텍스트보다 넓은
        # 라벨 안에서는 가운데 정렬로 표시함(기본 왼쪽 정렬이면 텍스트가 한쪽에
        # 치우쳐 보임).
        label_width = (
            max(QLabel("remote:").sizeHint().width(), QLabel("local:").sizeHint().width())
            + 12
        )

        remote_row = QHBoxLayout()
        remote_label = QLabel("remote:")
        remote_label.setFixedWidth(label_width)
        remote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remote_row.addWidget(remote_label)
        self.remote_edit = QLineEdit(remote_text)
        self.remote_edit.setPlaceholderText("remote 저장소 URL")
        remote_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirLinkIcon)
        remote_action = self.remote_edit.addAction(
            remote_icon, QLineEdit.ActionPosition.TrailingPosition
        )
        remote_action.setToolTip("remote URL 입력")
        remote_action.triggered.connect(self._prompt_remote_url)
        self.remote_edit.editingFinished.connect(self._save_callback)
        remote_row.addWidget(self.remote_edit, 1)
        layout.addLayout(remote_row)

        local_row = QHBoxLayout()
        local_label = QLabel("local:")
        local_label.setFixedWidth(label_width)
        local_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        local_row.addWidget(local_label)
        self.local_edit = QLineEdit(local_text)
        self.local_edit.setPlaceholderText("local 디렉토리 경로")
        dir_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        local_action = self.local_edit.addAction(
            dir_icon, QLineEdit.ActionPosition.TrailingPosition
        )
        local_action.setToolTip("디렉토리 선택")
        local_action.triggered.connect(self._browse_local_dir)
        self.local_edit.editingFinished.connect(self._save_callback)
        local_row.addWidget(self.local_edit, 1)
        layout.addLayout(local_row)

        self._last_result = None

        button_row = QHBoxLayout()
        self.compare_button = QPushButton("비교")
        self.compare_button.clicked.connect(self._compare)
        button_row.addWidget(self.compare_button)
        self.result_button = QPushButton("비교결과")
        self.result_button.setToolTip("클릭하면 마지막 비교 결과를 다시 봅니다.")
        self.result_button.clicked.connect(self._show_last_result)
        button_row.addWidget(self.result_button)
        self.stash_button = QPushButton("stash")
        self.stash_button.clicked.connect(self._stash)
        button_row.addWidget(self.stash_button)
        self.clone_button = QPushButton("git clone")
        self.clone_button.clicked.connect(self._git_clone)
        button_row.addWidget(self.clone_button)
        layout.addLayout(button_row)

    def _prompt_remote_url(self):
        text, ok = QInputDialog.getText(
            self, "remote URL 입력", "URL:", QLineEdit.EchoMode.Normal, self.remote_edit.text()
        )
        if ok and text:
            self.remote_edit.setText(text)
            self._save_callback()

    def _browse_local_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "디렉토리 선택", self.local_edit.text())
        if directory:
            self.local_edit.setText(directory)
            self._save_callback()

    def _compare(self):
        local = self.local_edit.text().strip()
        remote = self.remote_edit.text().strip()
        if not local or not remote:
            QMessageBox.information(self, "안내", "remote URL과 local 디렉토리를 모두 입력하세요.")
            return
        try:
            result = compare_repos(local, remote)
        except RuntimeError as exc:
            self.set_result_error(str(exc))
            QMessageBox.warning(self, "비교 실패", str(exc))
            return
        self.set_result(result)
        self._show_result_dialog(result)

    def set_result(self, result):
        """Applied both by this box's own '비교' button and by the panel's
        batch '전체 status check' worker."""
        self._last_result = result
        color = RESULT_SAME_COLOR if result["same"] else RESULT_DIFF_COLOR
        self.result_button.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: white; font-weight: bold; }}"
        )
        self.result_button.setText("동일" if result["same"] else "다름")

    def set_result_error(self, message):
        self._last_result = None
        self.result_button.setStyleSheet("")
        self.result_button.setText("오류")
        self.result_button.setToolTip(message)

    def _show_last_result(self):
        if self._last_result is None:
            QMessageBox.information(self, "비교결과", "아직 비교한 적이 없습니다.")
            return
        self._show_result_dialog(self._last_result)

    def _show_result_dialog(self, result):
        if result["same"]:
            QMessageBox.information(
                self, "비교 결과", f"local과 remote가 동일합니다.\n\ncommit: {result['local_hash']}"
            )
        else:
            QMessageBox.information(
                self,
                "비교 결과",
                f"local({result['local_branch']}): {result['local_hash']}\n"
                f"remote: {result['remote_hash']}\n\n서로 다른 커밋입니다.",
            )

    def _stash(self):
        directory = QFileDialog.getExistingDirectory(self, "stash할 디렉토리 선택", self.local_edit.text())
        if not directory:
            return
        try:
            backup_folder, count = stash_backup(directory)
        except RuntimeError as exc:
            QMessageBox.warning(self, "stash 실패", str(exc))
            return
        if count == 0:
            QMessageBox.information(self, "stash", "커밋되지 않은 변경 사항이 없습니다.")
            return
        QMessageBox.information(
            self, "stash 완료", f"{count}개 파일의 원본/현재 버전을 저장했습니다.\n\n{backup_folder}"
        )

    def _on_clone_locked_file(self, file_path, locking):
        """Called from clear_directory() when a file can't be deleted
        because another process has it open. Returns True to retry (after
        killing the offending process(es), if the user agrees) or False to
        give up on this file."""
        if not locking:
            QMessageBox.warning(
                self, "삭제 실패", f"다른 프로그램이 사용 중이라 삭제할 수 없습니다:\n{file_path}"
            )
            return False
        names = ", ".join(f"{name} (PID {pid})" for pid, name in locking)
        reply = QMessageBox.question(
            self,
            "프로세스 종료",
            f"다음 파일을 다른 프로세스가 사용 중이라 삭제할 수 없습니다:\n{file_path}\n\n"
            f"사용 중인 프로세스: {names}\n\n해당 프로세스를 중단할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return False
        for pid, _name in locking:
            terminate_process(pid)
        return True

    def _git_clone(self):
        local = self.local_edit.text().strip()
        remote = self.remote_edit.text().strip()
        if not local or not remote:
            QMessageBox.information(self, "안내", "remote와 local을 모두 입력하세요.")
            return

        self.setCursor(Qt.CursorShape.WaitCursor)
        remote_ok, _out, remote_err = _run_git(["ls-remote", remote])
        self.unsetCursor()
        if not remote_ok:
            QMessageBox.critical(
                self,
                "git clone 실패",
                "remote 저장소를 확인할 수 없습니다 (주소가 없거나 잘못됨):\n"
                f"{remote_err or '알 수 없는 오류'}",
            )
            return

        local_exists = os.path.isdir(local)
        dirty = []
        if local_exists:
            try:
                dirty = list_dirty_files(local)
            except RuntimeError:
                dirty = []

        # Names directly under `local` to leave alone when wiping it below -
        # only ever gets a name added if the user picks `local` itself (or a
        # folder inside it) as the stash-backup destination, so the backup
        # doesn't just get deleted again immediately after being made.
        keep_names = set()

        if dirty:
            reply = QMessageBox.question(
                self,
                "git clone",
                "모든 파일이 삭제됩니다. 현재 수정된 파일을 저장할까요?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                # 동작은 stash 버튼과 동일: 백업할 디렉토리를 고르고 그 안에
                # _stash_backup_시각/ 폴더로 원본/현재 버전을 저장함.
                backup_dir = QFileDialog.getExistingDirectory(self, "stash할 디렉토리 선택", local)
                if not backup_dir:
                    return
                try:
                    backup_folder, count = stash_backup(backup_dir)
                except RuntimeError as exc:
                    QMessageBox.warning(self, "stash 실패", str(exc))
                    return
                if count:
                    QMessageBox.information(
                        self,
                        "stash 완료",
                        f"{count}개 파일의 원본/현재 버전을 저장했습니다.\n\n{backup_folder}",
                    )
                    local_abs = os.path.abspath(local)
                    backup_abs = os.path.abspath(backup_folder)
                    if os.path.commonpath([local_abs, backup_abs]) == local_abs:
                        keep_names.add(os.path.relpath(backup_abs, local_abs).split(os.sep)[0])
        elif local_exists:
            reply = QMessageBox.question(
                self,
                "git clone",
                "local 폴더의 모든 파일/서브디렉토리가 삭제되고 remote 저장소를 새로 "
                "clone합니다. 계속하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.clone_button.setEnabled(False)
        self.clone_button.setText("clone 중...")
        try:
            if local_exists:
                self.setCursor(Qt.CursorShape.WaitCursor)
                cleared = clear_directory(local, self._on_clone_locked_file, exclude=keep_names)
                self.unsetCursor()
                if not cleared:
                    QMessageBox.warning(
                        self,
                        "git clone 중단",
                        "local 폴더를 완전히 비우지 못해 clone을 중단했습니다.",
                    )
                    return
            else:
                os.makedirs(local, exist_ok=True)

            # Clone into a fresh temp directory rather than straight into
            # `local` - if a stash backup folder was just created (and kept)
            # inside `local`, that leaves `local` non-empty, and `git clone`
            # refuses a non-empty target. Moving the cloned contents in
            # afterward sidesteps that regardless of whether anything was
            # kept.
            tmp_clone_dir = tempfile.mkdtemp(prefix="git_clone_tmp_")
            os.rmdir(tmp_clone_dir)
            self.setCursor(Qt.CursorShape.WaitCursor)
            clone_ok, clone_out, clone_err = _run_git(
                ["clone", remote, tmp_clone_dir], timeout=600
            )
            self.unsetCursor()
            if not clone_ok:
                shutil.rmtree(tmp_clone_dir, ignore_errors=True)
                QMessageBox.critical(self, "git clone 실패", clone_err or clone_out or "알 수 없는 오류")
                return
            for entry in os.listdir(tmp_clone_dir):
                shutil.move(os.path.join(tmp_clone_dir, entry), os.path.join(local, entry))
            shutil.rmtree(tmp_clone_dir, ignore_errors=True)
        finally:
            self.clone_button.setEnabled(True)
            self.clone_button.setText("git clone")

        QMessageBox.information(self, "git clone 완료", f"{remote}\n\n위 저장소를 clone했습니다.")


class GitPanel(QWidget):
    """'git' 탭 전용 위젯: 6쌍의 remote/local 비교·stash 상자 + 전체 status
    check(입력된 모든 쌍을 한 번에 비교)."""

    PAIR_COUNT = 6

    def __init__(self, parent=None, initial_pairs=None):
        super().__init__(parent)
        self._batch_worker = None
        self._scan_worker = None
        # `initial_pairs` (same shape as the JSON state file) lets the
        # standalone exporter seed this panel with whatever remote/local
        # pairs existed in the builder at export time, instead of always
        # starting empty.
        self._initial_pairs = initial_pairs

        # 앱 전역 스타일시트가 모든 QWidget에 회색(#f4f5f8) 배경을 주기 때문에,
        # 이걸 투명하게 비워서 탭 자체의 바탕색이 그대로 비쳐 보이게 함.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("GitPanel { background-color: transparent; }")

        outer = QVBoxLayout(self)
        # 위쪽 여백을 줄여서 상단 버튼 두 개를 조금 위로 올리고, 아래쪽 여백은
        # 좌우 여백(12)과 같게 맞춤(예전엔 10이었는데, 실제로는 트레일링
        # addStretch()가 패널에 할당된 캔버스 높이의 남는 공간을 전부 떠안아서
        # 체감 여백이 훨씬 커 보였음 - addStretch를 없애고 패널 캔버스 높이
        # 자체를 내용물에 맞게 줄이는 쪽으로 대신 해결함).
        outer.setContentsMargins(12, 4, 12, 12)
        outer.setSpacing(10)

        top_row = QHBoxLayout()
        self.scan_button = QPushButton("local drive 검색")
        self.scan_button.clicked.connect(self._run_local_drive_search)
        self.scan_button.setStyleSheet(_PRIMARY_BUTTON_STYLE)
        top_row.addWidget(self.scan_button)
        self.status_button = QPushButton("전체 status check")
        self.status_button.clicked.connect(self._run_full_status_check)
        self.status_button.setStyleSheet(_PRIMARY_BUTTON_STYLE)
        top_row.addWidget(self.status_button)
        outer.addLayout(top_row)

        # `self._initial_pairs` seeds a fresh export, but once
        # git_panel_state.json actually exists (created either by the
        # builder or by a previous run of the exported app), it is the
        # source of truth - otherwise every restart of the exported app
        # would revert to the export-time snapshot baked into its source,
        # undoing anything typed since then.
        if os.path.exists(GIT_PANEL_STATE_FILE):
            saved_pairs = _load_git_panel_state()
        elif self._initial_pairs is not None:
            saved_pairs = self._initial_pairs
            _save_git_panel_state(saved_pairs)
        else:
            saved_pairs = []

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        self.pair_boxes = []
        for i in range(self.PAIR_COUNT):
            saved = saved_pairs[i] if i < len(saved_pairs) else {}
            box = _RepoPairBox(saved.get("remote", ""), saved.get("local", ""), self._save_all_pairs)
            self.pair_boxes.append(box)
            grid.addWidget(box, i // 2, i % 2)
        outer.addLayout(grid)

    def _save_all_pairs(self):
        data = [
            {"remote": box.remote_edit.text(), "local": box.local_edit.text()}
            for box in self.pair_boxes
        ]
        _save_git_panel_state(data)

    def _run_full_status_check(self):
        jobs = []
        for index, box in enumerate(self.pair_boxes):
            local = box.local_edit.text().strip()
            remote = box.remote_edit.text().strip()
            if local and remote:
                jobs.append((index, local, remote))

        if not jobs:
            QMessageBox.information(
                self, "안내", "remote와 local이 모두 입력된 상자가 없습니다."
            )
            return

        reply = QMessageBox.question(
            self,
            "전체 status check",
            "local repo와 remote repo와의 차이를 확인합니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.status_button.setEnabled(False)
        self.status_button.setText("확인 중...")
        self._batch_worker = _BatchCompareWorker(jobs, self)
        self._batch_worker.result_ready.connect(self._on_batch_result)
        self._batch_worker.finished_all.connect(self._on_batch_finished)
        self._batch_worker.start()

    def _on_batch_result(self, index, result):
        box = self.pair_boxes[index]
        if isinstance(result, str):
            box.set_result_error(result)
        else:
            box.set_result(result)

    def _on_batch_finished(self):
        self.status_button.setEnabled(True)
        self.status_button.setText("전체 status check")

    def _run_local_drive_search(self):
        drives = _existing_drive_roots()
        if not drives:
            QMessageBox.information(self, "안내", "검색할 드라이브를 찾을 수 없습니다.")
            return
        reply = QMessageBox.question(
            self,
            "local drive 검색",
            f"각 드라이브의 최상위 폴더 기준 {DRIVE_SEARCH_MAX_DEPTH}단계 하위 폴더까지만 "
            "검색합니다.\n그보다 더 깊은 곳에 있는 저장소는 찾지 못할 수 있습니다.\n"
            "기존 정보는 모두 지워집니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.scan_button.setEnabled(False)
        self.scan_button.setText("검색 중...")
        self._scan_worker = _GitScanWorker(drives, self.PAIR_COUNT, self)
        self._scan_worker.succeeded.connect(self._on_scan_succeeded)
        self._scan_worker.failed.connect(self._on_scan_failed)
        self._scan_worker.start()

    def _on_scan_succeeded(self, repos):
        self.scan_button.setEnabled(True)
        self.scan_button.setText("local drive 검색")
        # 확인창에서 예고한 대로 기존 local 정보를 전부 지운 뒤 새로 찾은 것만 채움
        # (이전엔 새로 찾은 개수가 6개보다 적으면 남은 상자들에 예전 값이 그대로 남아있었음).
        for box in self.pair_boxes:
            box.local_edit.setText("")
        for box, path in zip(self.pair_boxes, repos):
            box.local_edit.setText(path)
        self._save_all_pairs()
        if len(repos) < self.PAIR_COUNT:
            QMessageBox.information(
                self, "local drive 검색", f"{len(repos)}개의 git 저장소를 찾아서 채웠습니다."
            )

    def _on_scan_failed(self, message):
        self.scan_button.setEnabled(True)
        self.scan_button.setText("local drive 검색")
        QMessageBox.warning(self, "검색 실패", message)
