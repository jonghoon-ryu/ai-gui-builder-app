"""'윈도우 현황' 위젯: Windows 버전/CPU/메모리/디스크 현황 + 휴지통 관리.

Uses only the standard library (ctypes calls into kernel32/shell32/psapi,
plus winreg/subprocess) instead of a package like psutil, so standalone-
exported apps that embed this widget still only need PySide6 to run (see
CLAUDE.md's export guarantee).
"""

import ctypes
import os
import platform
import shutil
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
    QGroupBox,
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


# ---- Temp folder cleanup -------------------------------------------------

def get_temp_folder_path():
    return os.environ.get("TEMP") or os.environ.get("TMP") or ""


def get_temp_folder_summary():
    """Returns (file_count, total_size_bytes) for every file under the Temp
    folder, recursively. Walks the filesystem directly - can take a moment
    for a large Temp folder, same tradeoff as get_folder_sizes."""
    path = get_temp_folder_path()
    if not path or not os.path.isdir(path):
        return 0, 0
    count = 0
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
            count += 1
    return count, total


def list_temp_files():
    """Returns [{"name", "path", "size", "modified_at"}, ...] for every file
    under the Temp folder, most-recently-modified first."""
    path = get_temp_folder_path()
    items = []
    if not path or not os.path.isdir(path):
        return items
    for root, _dirs, files in os.walk(path):
        for name in files:
            full_path = os.path.join(root, name)
            try:
                stat = os.stat(full_path)
            except OSError:
                continue
            items.append(
                {
                    "name": name,
                    "path": full_path,
                    "size": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime),
                }
            )
    items.sort(key=lambda it: it["modified_at"], reverse=True)
    return items


def empty_temp_folder():
    """Deletes everything directly under the Temp folder (files and
    subfolders alike), skipping anything currently locked/in-use instead of
    aborting - very common for Temp, since Windows and running apps
    routinely keep files open there. Returns (deleted_count, skipped_count)
    counted at the top level (a skipped subfolder counts as one, not per
    file inside it)."""
    path = get_temp_folder_path()
    if not path or not os.path.isdir(path):
        return 0, 0
    deleted = 0
    skipped = 0
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        try:
            if os.path.isdir(full_path) and not os.path.islink(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            deleted += 1
        except OSError:
            skipped += 1
    return deleted, skipped


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

    REFRESH_INTERVAL_MS = 8000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cpu_tracker = CpuUsageTracker()
        self._disk_rows = {}
        self._next_grid_row = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        # ---- 시스템 정보 ----
        sys_group = QGroupBox("시스템 정보")
        sys_layout = QVBoxLayout(sys_group)
        self.os_label = QLabel()
        sys_layout.addWidget(self.os_label)
        self.cpu_model_label = QLabel()
        sys_layout.addWidget(self.cpu_model_label)
        outer.addWidget(sys_group)

        # ---- 자원 사용률 ----
        resource_group = QGroupBox("자원 사용률")
        resource_layout = QVBoxLayout(resource_group)

        self.info_grid = QGridLayout()
        self.info_grid.setHorizontalSpacing(8)
        self.info_grid.setVerticalSpacing(4)
        self.info_grid.setColumnMinimumWidth(0, 90)
        self.info_grid.setColumnStretch(1, 1)
        resource_layout.addLayout(self.info_grid)

        self.cpu_bar, self.cpu_value_label = self._add_meter_row("CPU 사용률:")
        self.mem_bar, self.mem_value_label = self._add_meter_row("메모리:")

        disk_title = QLabel("디스크")
        self._make_bold(disk_title)
        resource_layout.addWidget(disk_title)

        self.disk_grid = QGridLayout()
        self.disk_grid.setHorizontalSpacing(8)
        self.disk_grid.setVerticalSpacing(4)
        self.disk_grid.setColumnMinimumWidth(0, 90)
        self.disk_grid.setColumnStretch(1, 1)
        resource_layout.addLayout(self.disk_grid)

        outer.addWidget(resource_group)

        # ---- 확인 ----
        check_group = QGroupBox("확인")
        check_layout = QHBoxLayout(check_group)
        self.top_processes_button = QPushButton("상위 프로세스")
        self.top_processes_button.clicked.connect(self._show_top_processes)
        check_layout.addWidget(self.top_processes_button)
        self.folder_sizes_button = QPushButton("폴더 용량")
        self.folder_sizes_button.clicked.connect(self._show_folder_sizes)
        check_layout.addWidget(self.folder_sizes_button)
        self.startup_button = QPushButton("시작 프로그램 목록")
        self.startup_button.clicked.connect(self._show_startup_programs)
        check_layout.addWidget(self.startup_button)
        self.env_vars_button = QPushButton("시스템 변수 바로보기")
        self.env_vars_button.clicked.connect(open_environment_variables_dialog)
        check_layout.addWidget(self.env_vars_button)
        outer.addWidget(check_group)

        # ---- 휴지통, temp 파일 제거 ----
        cleanup_group = QGroupBox("휴지통, temp 파일 제거")
        cleanup_layout = QVBoxLayout(cleanup_group)

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
        cleanup_layout.addLayout(bin_row)

        temp_title = QLabel("temp 파일")
        self._make_bold(temp_title)
        cleanup_layout.addWidget(temp_title)

        temp_row = QHBoxLayout()
        temp_icon_label = QLabel()
        temp_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        temp_icon_label.setPixmap(temp_icon.pixmap(24, 24))
        temp_row.addWidget(temp_icon_label)
        self.temp_label = QLabel("temp 파일: 확인 중...")
        temp_row.addWidget(self.temp_label, 1)
        self.temp_list_button = QPushButton("목록")
        self.temp_list_button.clicked.connect(self._show_temp_files)
        temp_row.addWidget(self.temp_list_button)
        self.temp_empty_button = QPushButton("temp 파일 비우기")
        self.temp_empty_button.clicked.connect(self._empty_temp_folder)
        temp_row.addWidget(self.temp_empty_button)
        cleanup_layout.addLayout(temp_row)

        outer.addWidget(cleanup_group)

        outer.addStretch()

        self._refresh()
        self._refresh_temp_summary()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        # Started/stopped from showEvent/hideEvent instead of here, so the
        # periodic refresh only runs while this tab is actually the one
        # being looked at, not for every hidden tab in the background.

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()
        self._refresh_temp_summary()
        self._timer.start(self.REFRESH_INTERVAL_MS)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

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

    def _refresh_temp_summary(self):
        count, size = get_temp_folder_summary()
        self.temp_label.setText(f"temp 파일: {count}개 파일, {_format_bytes(size)}")

    def _show_temp_files(self):
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            items = list_temp_files()
        finally:
            self.unsetCursor()

        dialog = QDialog(self)
        dialog.setWindowTitle("temp 파일 목록")
        dialog.resize(640, 420)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(len(items), 3)
        table.setHorizontalHeaderLabels(["이름", "경로", "크기"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, item in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(item["name"]))
            # Same Hangul-truncation workaround as the recycle bin list.
            path_label = QLabel(item["path"])
            path_label.setToolTip(item["path"])
            path_label.setContentsMargins(4, 0, 4, 0)
            table.setCellWidget(row, 1, path_label)
            table.setItem(row, 2, QTableWidgetItem(_format_bytes(item["size"])))
        layout.addWidget(table)

        if not items:
            layout.addWidget(QLabel("temp 폴더가 비어 있습니다."))

        close_button = QPushButton("닫기")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _empty_temp_folder(self):
        reply = QMessageBox.question(
            self,
            "temp 파일 비우기",
            "temp 폴더의 파일을 모두 삭제하시겠습니까?\n사용 중인 파일/폴더는 자동으로 건너뜁니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            deleted, skipped = empty_temp_folder()
        finally:
            self.unsetCursor()
        self._refresh_temp_summary()
        if skipped:
            QMessageBox.information(
                self,
                "완료",
                f"{deleted}개 항목을 삭제했습니다.\n{skipped}개는 사용 중이라 건너뛰었습니다.",
            )

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
