"""'gvf' 위젯: GVF 자원 현황 표시 패널.

오늘은 뼈대(레이아웃)만 구현 - 실제 자원 데이터/시간 연결은 다음에 이어서 한다.
Only uses the standard library plus PySide6, so standalone-exported apps
embedding this widget still only need PySide6 to run (see CLAUDE.md's export
guarantee).
"""

import json
import os
import sys

from PySide6.QtCore import QTime, Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStyle,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

DISPLAY_COUNT = 3

# PyInstaller onefile builds unpack __file__ into a temp dir that's wiped
# after exit, so state saved there wouldn't survive a restart - save next to
# the actual .exe instead when frozen (same approach as git_widget.py).
_STATE_DIR = (
    os.path.dirname(os.path.abspath(sys.executable))
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
_APP_DATA_DIR = os.path.join(_STATE_DIR, "appData")
GVF_STATE_FILE = os.path.join(_APP_DATA_DIR, "gvf_state.json")


def _load_gvf_state():
    if not os.path.exists(GVF_STATE_FILE):
        return {}
    try:
        with open(GVF_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_gvf_state(data):
    try:
        os.makedirs(_APP_DATA_DIR, exist_ok=True)
        with open(GVF_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _update_gvf_state(key, value):
    """Read-modify-write a single top-level key so saving one panel's data
    (GvfPanel/FpgaAcquisitionPanel/FpgaLoadingPanel each own a distinct key)
    never wipes out what another panel already saved to the same file."""
    state = _load_gvf_state()
    state[key] = value
    _save_gvf_state(state)


class _DigitalTimeBox(QFrame):
    """표시창 오른쪽에 붙는 시작/종료 시간 디지털 시계 스타일 표시. 지금은
    자리표시자 값("00:00:00")만 보여주고, 실제 시간 연결은 나중에 구현한다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWidth(0)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("_DigitalTimeBox { background-color: #101418; border: none; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        # 초 단위는 표시하지 않음(요청) - 그만큼 비는 가로 공간을 글자 크기를
        # 키워서 채움(17px, 기존 "00:00:00" 12px 폭과 비슷하게 맞춘 값).
        self.start_label = QLabel("시작 00:00")
        self.end_label = QLabel("종료 00:00")
        for label in (self.start_label, self.end_label):
            label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            label.setStyleSheet(
                "background-color: transparent; color: #4be36a;"
                " font-family: Consolas, monospace; font-size: 16px;"
            )
            layout.addWidget(label)
        # setFixedWidth(고정)을 써야 함 - setMinimumWidth만 쓰면 이 위젯이 유일하게
        # 명시적 최대 폭이 없는 항목이라, row가 패널 폭보다 여유가 있을 때 그 남는
        # 공간을 전부 이 시계가 혼자 흡수해버려서(예: 25% 줄인 값이 화면에 그대로
        # 반영 안 되고 도로 커짐) "가로 길이를 N%만큼 줄인다"는 요청이 무의미해짐.
        self.setFixedWidth(layout.sizeHint().width())


class _DisplayRow(QFrame):
    """표시창 하나 + 오른쪽의 시작/종료 디지털 시계 한 쌍."""

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("_DisplayRow { background-color: transparent; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        self.display_label = QLabel(f"FPGA #{index}")
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_label.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #ced2db; border-radius: 5px;"
            " font-size: 11px;"
        )
        self.display_label.setFixedWidth(68)
        self.display_label.setMinimumHeight(40)
        layout.addWidget(self.display_label)

        self.number_edit = QLineEdit(self)
        self.number_edit.setPlaceholderText("000")
        self.number_edit.setMaxLength(3)
        self.number_edit.setValidator(QIntValidator(0, 999, self.number_edit))
        self.number_edit.setFixedWidth(38)
        layout.addWidget(self.number_edit)

        self.time_box = _DigitalTimeBox(self)
        layout.addWidget(self.time_box)

        self.return_button = QPushButton("반납", self)
        return_size = self.return_button.sizeHint()
        button_size = (
            int(return_size.width() * 1.5 * 0.9 * 0.9),
            int(return_size.height() * 1.5 * 0.9),
        )
        self.return_button.setFixedSize(*button_size)

        self.owned_button = QPushButton("소유중", self)
        self.owned_button.setFixedSize(*button_size)
        layout.addWidget(self.owned_button)
        layout.addWidget(self.return_button)


class GvfPanel(QWidget):
    """'gvf' 탭 전용 위젯: "gvf 자원 현황" 그룹박스 + 표시창 3개(뼈대만).

    표시창("FPGA #1"/"FPGA #2"/"FPGA #3") 3개 각각의 오른쪽에 숫자 3자리
    입력칸, 그 오른쪽에 시작/종료 시간을 보여줄 디지털 시계 자리, 맨 오른쪽에
    "반납" 버튼(기본 크기의 1.5배)이 붙는다. 실제 자원 데이터를 채우거나 시간을
    실시간으로 갱신하는 로직, "반납" 버튼을 눌렀을 때의 실제 동작은 아직 없음 -
    레이아웃만 먼저 잡아둔 상태."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("GvfPanel { background-color: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("FPGA 자원 현황", self)
        outer.addWidget(group)

        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(4, 10, 4, 10)
        group_layout.setSpacing(10)

        self.rows = []
        for i in range(1, DISPLAY_COUNT + 1):
            row = _DisplayRow(i, group)
            group_layout.addWidget(row)
            self.rows.append(row)

        self._restore_state()
        for row in self.rows:
            row.number_edit.editingFinished.connect(self._save_state)

    def _restore_state(self):
        numbers = _load_gvf_state().get("display_numbers", [])
        for row, value in zip(self.rows, numbers):
            row.number_edit.setText(value)

    def _save_state(self):
        _update_gvf_state("display_numbers", [row.number_edit.text() for row in self.rows])


DEFAULT_ACQUISITION_INTERVAL_MINUTES = 120
DEFAULT_MAX_FPGA_COUNT = 1


class FpgaAcquisitionPanel(QWidget):
    """'gvf' 탭 우측 상단 위젯: "FPGA 자원 취득" 그룹박스(뼈대만).

    맨 위 "아이디" 문자열 입력창(`QLineEdit`), 그 아래 "명령어 입력 디렉토리" 경로
    입력(git 탭의 local 디렉토리 입력창과 같은 방식 - 폴더 아이콘을 누르면 Windows
    폴더 선택 창이 뜸), "FPGA 획득 마지막 시도" 시간 입력(`QTimeEdit`), "FPGA 취득
    간격"(분 단위, 기본 120분, 스핀박스로 조절 가능)과 "max FPGA 취득"(최솟값 1,
    기본값 1, 스핀박스로 조절 가능)이 한 줄에, "FPGA 대기열 삭제" 버튼, 맨 아래
    시작/중지 버튼 한 쌍까지 일곱 줄만 잡아둔 상태 - 실제로 아이디를 어디에
    쓸지, 그 간격마다 자동으로 획득을 시도하거나 그 디렉토리에서 명령어를
    실행하는 로직, "FPGA 대기열 삭제"/시작/중지 버튼을 눌렀을 때의 실제 동작은
    아직 없음(다음에 이어서 구현) - 지금은 값 입력/버튼 이름 토글만 된다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("FpgaAcquisitionPanel { background-color: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("FPGA 자원 취득", self)
        outer.addWidget(group)

        form = QVBoxLayout(group)
        form.setContentsMargins(15, 10, 15, 10)
        form.setSpacing(10)

        id_row = QHBoxLayout()
        id_row.addWidget(QLabel("아이디"))
        self.id_edit = QLineEdit(group)
        id_row.addWidget(self.id_edit, 1)
        form.addLayout(id_row)

        self.command_dir_edit = QLineEdit(group)
        self.command_dir_edit.setPlaceholderText("명령어 입력 디렉토리")
        dir_icon = self.command_dir_edit.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        dir_action = self.command_dir_edit.addAction(
            dir_icon, QLineEdit.ActionPosition.TrailingPosition
        )
        dir_action.setToolTip("디렉토리 선택")
        dir_action.triggered.connect(self._browse_command_dir)
        form.addWidget(self.command_dir_edit)

        last_try_row = QHBoxLayout()
        last_try_row.addWidget(QLabel("FPGA 획득 마지막 시도"))
        self.last_attempt_time = QTimeEdit(QTime.currentTime(), group)
        self.last_attempt_time.setDisplayFormat("HH:mm:ss")
        self.last_attempt_time.setFixedHeight(26)
        last_try_row.addWidget(self.last_attempt_time)
        last_try_row.addStretch(1)
        form.addLayout(last_try_row)

        # 한 줄에 label 2개 + spinbox 2개를 모두 넣어야 해서(요청: "max FPGA 취득"을
        # "FPGA 취득 간격" 오른쪽으로), 폭이 빠듯함 - 이 줄의 라벨 두 개만 살짝 작은
        # 글자(11px, 다른 줄 라벨은 그대로)를 써서 필요한 가로 폭을 줄임.
        interval_row = QHBoxLayout()
        interval_label = QLabel("FPGA 취득 간격")
        interval_label.setStyleSheet("font-size: 11px;")
        interval_row.addWidget(interval_label)
        self.interval_minutes = QSpinBox(group)
        self.interval_minutes.setRange(1, 1440)
        self.interval_minutes.setValue(DEFAULT_ACQUISITION_INTERVAL_MINUTES)
        self.interval_minutes.setSuffix(" 분")
        self.interval_minutes.setMaximumWidth(62)
        self.interval_minutes.setFixedHeight(26)
        interval_row.addWidget(self.interval_minutes)
        interval_row.addStretch(1)
        max_count_label = QLabel("max FPGA 취득")
        max_count_label.setStyleSheet("font-size: 11px;")
        interval_row.addWidget(max_count_label)
        self.max_fpga_count = QSpinBox(group)
        self.max_fpga_count.setRange(1, 999)
        self.max_fpga_count.setValue(DEFAULT_MAX_FPGA_COUNT)
        self.max_fpga_count.setMaximumWidth(42)
        self.max_fpga_count.setFixedHeight(26)
        interval_row.addWidget(self.max_fpga_count)
        form.addLayout(interval_row)

        self.clear_queue_button = QPushButton("FPGA 대기열 삭제", group)
        self.clear_queue_button.setFixedHeight(26)
        form.addWidget(self.clear_queue_button)

        control_row = QHBoxLayout()
        self.start_button = QPushButton("시작", group)
        self.start_button.setFixedHeight(26)
        self.start_button.clicked.connect(self._on_start_clicked)
        control_row.addWidget(self.start_button)
        self.stop_button = QPushButton("중지", group)
        self.stop_button.setFixedHeight(26)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        control_row.addWidget(self.stop_button)
        form.addLayout(control_row)

        # max FPGA 취득 줄을 FPGA 취득 간격 줄에 합쳐서 항목이 7개에서 6개로 줄어든
        # 만큼, 사각형 세로 길이(패널 높이)는 그대로 두고 남는 공간을 6개 항목에 균등
        # 배분해 각 항목의 세로 길이가 서로 같아지도록 함.
        for i in range(form.count()):
            form.setStretch(i, 1)

        self._restore_state()
        self.id_edit.editingFinished.connect(self._save_state)
        self.last_attempt_time.editingFinished.connect(self._save_state)
        self.interval_minutes.valueChanged.connect(lambda _value: self._save_state())
        self.max_fpga_count.valueChanged.connect(lambda _value: self._save_state())
        self.command_dir_edit.editingFinished.connect(self._save_state)

    def _restore_state(self):
        state = _load_gvf_state().get("acquisition", {})
        if "id" in state:
            self.id_edit.setText(state["id"])
        if "last_attempt_time" in state:
            saved_time = QTime.fromString(state["last_attempt_time"], "HH:mm:ss")
            if saved_time.isValid():
                self.last_attempt_time.setTime(saved_time)
        if "interval_minutes" in state:
            self.interval_minutes.setValue(state["interval_minutes"])
        if "max_fpga_count" in state:
            self.max_fpga_count.setValue(state["max_fpga_count"])
        if "command_dir" in state:
            self.command_dir_edit.setText(state["command_dir"])

    def _save_state(self):
        _update_gvf_state(
            "acquisition",
            {
                "id": self.id_edit.text(),
                "last_attempt_time": self.last_attempt_time.time().toString("HH:mm:ss"),
                "interval_minutes": self.interval_minutes.value(),
                "max_fpga_count": self.max_fpga_count.value(),
                "command_dir": self.command_dir_edit.text(),
            },
        )

    def _on_start_clicked(self):
        self.start_button.setText("동작중")

    def _on_stop_clicked(self):
        self.start_button.setText("다시 시작")

    def _browse_command_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "디렉토리 선택", self.command_dir_edit.text()
        )
        if directory:
            self.command_dir_edit.setText(directory)
            self._save_state()


FPGA_VERSION_ITEMS = ["FPGA v18.0", "FPGA v19.0", "FPGA v24.0", "FPGA v25.0"]
FPGA_NUMBER_ITEMS = ["FPGA #1", "FPGA #2", "FPGA #3"]
FPGA_MEMORY_TYPE_ITEMS = ["TLC", "QLC", "SLC/QLC", "TLC/QLC"]
FPGA_OS_ITEMS = ["linux", "windows", "test"]


def _radio_group(items, parent):
    """공통 라디오 버튼 묶음 생성 헬퍼. 첫 번째 옵션이 기본 선택되고,
    (QButtonGroup, [QRadioButton, ...]) 튜플을 반환한다."""
    button_group = QButtonGroup(parent)
    buttons = []
    for i, text in enumerate(items):
        radio = QRadioButton(text, parent)
        if i == 0:
            radio.setChecked(True)
        button_group.addButton(radio)
        buttons.append(radio)
    return button_group, buttons


class FpgaLoadingPanel(QWidget):
    """'gvf' 탭 하단 위젯: "FPGA loading" 그룹박스(뼈대만).

    라디오 버튼 그룹 4개(FPGA 버전, FPGA 번호 - "FPGA #1"/"FPGA #2"/"FPGA #3"
    각각 옆에 숫자 3자리 입력칸이 붙음, 메모리 타입, OS - linux/windows/test)를
    한 줄에 나열하고, 맨 오른쪽에 "시작" 버튼(기본 크기의 1.5배)을 놓는다. 선택된 라디오 버튼/숫자
    입력값은 바뀔 때마다 자동으로 `appData/gvf_state.json`("loading" 키)에
    저장되고 재시작 시 복원된다. 실제로 "시작" 버튼을 눌렀을 때 무슨 일이
    일어나는지는 아직 없음(다음에 이어서 구현)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("FpgaLoadingPanel { background-color: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("FPGA loading", self)
        outer.addWidget(group)

        form = QVBoxLayout(group)
        # QGroupBox reserves extra room above its content for the title text
        # regardless of these margins, so a small top margin here still ends
        # up visually similar to left/right/bottom once that reserved title
        # space is added on top of it (checked empirically with headless
        # pixel measurements - equal margins on all four sides here would
        # have made the top look far bigger than the rest).
        # 좌/우/아래 여백은 "FPGA 자원 현황" 그룹박스 안의 표시창 3개 사이
        # 간격(group_layout.setSpacing(10))과 맞춤. 위쪽은 QGroupBox가 제목
        # 글자를 위해 항상 별도 공간을 예약하는 스타일 특성 때문에 0으로 둬도
        # 시각적으로 다른 방향과 비슷해짐(헤드리스 픽셀 측정으로 확인함).
        form.setContentsMargins(15, 0, 15, 10)
        form.setSpacing(10)

        # 라디오 버튼을 한 줄로 나란히 늘어놓으면 폭이 지나치게 넓어져서(11개
        # 라디오 버튼 기준 1500px+), 그룹별로 세로로 쌓은 좁은 열 3개를 만들고
        # 그 열들을 가로로 배치하는 방식으로 바꿈 - 맨 오른쪽에 "시작" 버튼.
        row = QHBoxLayout()
        # OS 라디오 그룹(4번째 열)이 추가되면서 기존 80px 간격을 유지하면 필요
        # 폭이 캔버스 폭을 크게 초과해서(978px vs 794px 가용), 4개 열이 모두
        # 들어가도록 32px까지 줄였다가, "간격이 너무 좁다"는 요청으로 30% 늘림
        # (다른 요소들(숫자 입력칸 등) 폭을 줄여서 확보한 여유를 여기로 돌림).
        row.setSpacing(29)

        version_col = QVBoxLayout()
        version_col.setSpacing(2)
        self.version_group, self.version_buttons = _radio_group(FPGA_VERSION_ITEMS, group)
        for radio in self.version_buttons:
            version_col.addWidget(radio)
        row.addLayout(version_col)

        number_col = QVBoxLayout()
        number_col.setSpacing(2)
        self.number_group, self.number_buttons = _radio_group(FPGA_NUMBER_ITEMS, group)
        self.number_value_edits = []
        for radio in self.number_buttons:
            entry_row = QHBoxLayout()
            entry_row.setSpacing(8)
            entry_row.addWidget(radio)
            number_value_edit = QLineEdit(group)
            number_value_edit.setPlaceholderText("000")
            number_value_edit.setMaxLength(3)
            number_value_edit.setValidator(QIntValidator(0, 999, number_value_edit))
            number_value_edit.setFixedWidth(41)
            entry_row.addWidget(number_value_edit)
            self.number_value_edits.append(number_value_edit)
            number_col.addLayout(entry_row)
        row.addLayout(number_col)

        memory_col = QVBoxLayout()
        memory_col.setSpacing(2)
        self.memory_type_group, self.memory_type_buttons = _radio_group(
            FPGA_MEMORY_TYPE_ITEMS, group
        )
        for radio in self.memory_type_buttons:
            memory_col.addWidget(radio)
        row.addLayout(memory_col)

        os_col = QVBoxLayout()
        os_col.setSpacing(2)
        self.os_group, self.os_buttons = _radio_group(FPGA_OS_ITEMS, group)
        for radio in self.os_buttons:
            os_col.addWidget(radio)
        row.addLayout(os_col)

        row.addStretch(1)

        self.start_button = QPushButton("시작", group)
        start_size = self.start_button.sizeHint()
        # 세로 길이는 요청으로 기존(자연 크기의 3배)의 2배인 자연 크기의 6배로 키움.
        self.start_button.setFixedSize(int(start_size.width() * 3), int(start_size.height() * 6))
        row.addWidget(self.start_button, 0, Qt.AlignmentFlag.AlignVCenter)

        form.addLayout(row)

        self._restore_state()
        self.version_group.buttonClicked.connect(self._save_state)
        self.number_group.buttonClicked.connect(self._save_state)
        self.memory_type_group.buttonClicked.connect(self._save_state)
        self.os_group.buttonClicked.connect(self._save_state)
        for number_value_edit in self.number_value_edits:
            number_value_edit.editingFinished.connect(self._save_state)

    def _restore_state(self):
        loading = _load_gvf_state().get("loading", {})
        version = loading.get("version")
        if version:
            for radio in self.version_buttons:
                if radio.text() == version:
                    radio.setChecked(True)
        number = loading.get("number")
        if number:
            for radio in self.number_buttons:
                if radio.text() == number:
                    radio.setChecked(True)
        for edit, value in zip(self.number_value_edits, loading.get("number_values", [])):
            edit.setText(value)
        memory_type = loading.get("memory_type")
        if memory_type:
            for radio in self.memory_type_buttons:
                if radio.text() == memory_type:
                    radio.setChecked(True)
        os_name = loading.get("os")
        if os_name:
            for radio in self.os_buttons:
                if radio.text() == os_name:
                    radio.setChecked(True)

    def _save_state(self):
        checked_version = next((b.text() for b in self.version_buttons if b.isChecked()), None)
        checked_number = next((b.text() for b in self.number_buttons if b.isChecked()), None)
        checked_memory_type = next(
            (b.text() for b in self.memory_type_buttons if b.isChecked()), None
        )
        checked_os = next((b.text() for b in self.os_buttons if b.isChecked()), None)
        _update_gvf_state(
            "loading",
            {
                "version": checked_version,
                "number": checked_number,
                "number_values": [edit.text() for edit in self.number_value_edits],
                "memory_type": checked_memory_type,
                "os": checked_os,
            },
        )
