"""'git' 위젯: local/remote 6쌍 비교·stash + 전체 status check.

Only uses the standard library plus the `git` executable via subprocess (no
extra pip packages), so standalone-exported apps embedding this widget still
only need PySide6 to run (see CLAUDE.md's export guarantee). The exported
app's user still needs `git` itself installed and on PATH, same as the
"동작 설정" natural-language features need `claude`.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

from PySide6.QtCore import QThread, Signal
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

# PyInstaller onefile builds unpack __file__ into a temp dir that's wiped
# after exit, so state saved there wouldn't survive a restart - save next to
# the actual .exe instead when frozen.
_STATE_DIR = (
    os.path.dirname(os.path.abspath(sys.executable))
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
GIT_PANEL_STATE_FILE = os.path.join(_STATE_DIR, "git_panel_state.json")


def _run_git(args, cwd=None, timeout=_GIT_TIMEOUT_SECONDS):
    """Returns (ok, stdout, stderr) - never raises for a missing repo/remote,
    only for git itself being unavailable or timing out."""
    try:
        result = subprocess.run(
            [GIT_BIN, *args], cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        return False, "", "git 명령을 찾을 수 없습니다. git이 설치되어 있고 PATH에 등록되어 있어야 합니다."
    except subprocess.TimeoutExpired:
        return False, "", "git 명령이 시간 초과되었습니다."
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def _existing_drive_roots():
    return [f"{letter}:\\" for letter in "CDE" if os.path.exists(f"{letter}:\\")]


def find_git_repos(drive_roots, limit=None):
    """Walks each drive root looking for a `.git` entry, skipping into it
    (and a few other huge/irrelevant folders) once found. Stops as soon as
    `limit` repos have been found, if given - a full-drive walk is
    inherently slow, so callers should both cap it and run it off the UI
    thread."""
    found = []
    for root in drive_roots:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _e: None):
            if ".git" in dirnames or ".git" in filenames:
                found.append(dirpath)
                if limit is not None and len(found) >= limit:
                    return found
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        remote_row = QHBoxLayout()
        remote_row.addWidget(QLabel("remote:"))
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
        local_row.addWidget(QLabel("local:"))
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

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(10)

        top_row = QHBoxLayout()
        self.scan_button = QPushButton("local drive 검색")
        self.scan_button.clicked.connect(self._run_local_drive_search)
        top_row.addWidget(self.scan_button)
        self.status_button = QPushButton("전체 status check")
        self.status_button.clicked.connect(self._run_full_status_check)
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
        outer.addStretch()

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
        self.scan_button.setEnabled(False)
        self.scan_button.setText("검색 중...")
        self._scan_worker = _GitScanWorker(drives, self.PAIR_COUNT, self)
        self._scan_worker.succeeded.connect(self._on_scan_succeeded)
        self._scan_worker.failed.connect(self._on_scan_failed)
        self._scan_worker.start()

    def _on_scan_succeeded(self, repos):
        self.scan_button.setEnabled(True)
        self.scan_button.setText("local drive 검색")
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
