from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

import ai_client


class _GenerateWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, target_id, target_type, all_widgets, instruction, parent=None):
        super().__init__(parent)
        self._target_id = target_id
        self._target_type = target_type
        self._all_widgets = all_widgets
        self._instruction = instruction

    def run(self):
        try:
            code = ai_client.generate_handler_code(
                self._target_id, self._target_type, self._all_widgets, self._instruction
            )
        except Exception as exc:  # surfaced via signal; dialog stays open
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(code)


class BehaviorDialog(QDialog):
    """Lets the user describe a widget's behavior in natural language,
    triggers Claude to generate the handler code, and previews/edits it
    before it gets compiled and bound to the widget."""

    def __init__(
        self,
        widget_id,
        widget_kind,
        all_widgets,
        existing_instruction="",
        existing_code="",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"동작 설정 — {widget_id}")
        self.resize(480, 420)

        self._widget_id = widget_id
        self._widget_kind = widget_kind
        self._all_widgets = all_widgets
        self._worker = None

        self.result_code = None
        self.instruction_text = ""

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"'{widget_id}' ({widget_kind})의 동작을 자연어로 설명하세요:"))

        self.instruction_edit = QTextEdit()
        self.instruction_edit.setPlainText(existing_instruction)
        self.instruction_edit.setFixedHeight(80)
        layout.addWidget(self.instruction_edit)

        self.generate_button = QPushButton("생성")
        self.generate_button.clicked.connect(self._on_generate)
        layout.addWidget(self.generate_button)

        layout.addWidget(QLabel("생성된 코드 (직접 수정 가능):"))
        self.code_edit = QPlainTextEdit()
        self.code_edit.setPlainText(existing_code)
        layout.addWidget(self.code_edit)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        hint_label = QLabel("※ '생성'만으로는 위젯에 연결되지 않습니다. 반드시 '저장'을 눌러야 합니다.")
        hint_label.setStyleSheet("color: #b45309;")
        layout.addWidget(hint_label)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("저장 (위젯에 연결)")
        self.save_button.clicked.connect(self._on_save)
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        button_row.addStretch()
        button_row.addWidget(self.save_button)
        button_row.addWidget(cancel_button)
        layout.addLayout(button_row)

    def _on_generate(self):
        instruction = self.instruction_edit.toPlainText().strip()
        if not instruction:
            QMessageBox.warning(self, "알림", "동작을 설명하는 문장을 입력하세요.")
            return

        self.generate_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.status_label.setText("생성 중...")

        self._worker = _GenerateWorker(
            self._widget_id, self._widget_kind, self._all_widgets, instruction, self
        )
        self._worker.succeeded.connect(self._on_generate_succeeded)
        self._worker.failed.connect(self._on_generate_failed)
        self._worker.start()

    def _on_generate_succeeded(self, code):
        self.code_edit.setPlainText(code)
        self.status_label.setText("생성 완료")
        self.generate_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def _on_generate_failed(self, message):
        self.status_label.setText("")
        self.generate_button.setEnabled(True)
        self.save_button.setEnabled(True)
        QMessageBox.critical(self, "생성 실패", message)

    def _on_save(self):
        code = self.code_edit.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "알림", "저장할 코드가 없습니다. 먼저 생성하세요.")
            return
        self.instruction_text = self.instruction_edit.toPlainText().strip()
        self.result_code = code
        self.accept()
