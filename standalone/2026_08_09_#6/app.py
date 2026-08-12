import os
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
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


class GeneratedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        page_0 = QWidget()
        page_0.setFixedSize(1100, 733)
        page_0.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_0.setStyleSheet("background-color: #ddebe2;")

        self.tabs.addTab(page_0, "git")

        page_1 = QWidget()
        page_1.setFixedSize(1100, 733)
        page_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_1.setStyleSheet("background-color: #f9f06b;")

        self.tabs.addTab(page_1, "wiki")

        page_2 = QWidget()
        page_2.setFixedSize(1100, 733)
        page_2.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_2.setStyleSheet("background-color: #f4e8e8;")

        self.tab2_button_1 = QPushButton("버튼", page_2)
        self.tab2_button_1.setText("아름다운 나라 - 하윤주")
        self.tab2_button_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab2_button_1.setStyleSheet("background-color: #dc8add;")
        self.tab2_button_1.move(81, 180)
        self.tab2_button_1.adjustSize()
        self.tab2_button_1.resize(175, 39)
        self.tab2_button_1.clicked.connect(self._tab2_button_1_on_event)

        self.tab2_lineedit_1 = QLineEdit(page_2)
        self.tab2_lineedit_1.setPlaceholderText("텍스트 입력")
        self.tab2_lineedit_1.setText("   노래")
        self.tab2_lineedit_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab2_lineedit_1.setStyleSheet("background-color: #8ff0a4;")
        self.tab2_lineedit_1.move(130, 63)
        self.tab2_lineedit_1.adjustSize()
        self.tab2_lineedit_1.resize(71, 39)

        self.tab2_button_2 = QPushButton("버튼", page_2)
        self.tab2_button_2.setText("섬집 아기 - 하윤주")
        self.tab2_button_2.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab2_button_2.setStyleSheet("background-color: #ffbe6f;")
        self.tab2_button_2.move(81, 275)
        self.tab2_button_2.adjustSize()
        self.tab2_button_2.resize(145, 39)
        self.tab2_button_2.clicked.connect(self._tab2_button_2_on_event)

        self.tab2_button_3 = QPushButton("버튼", page_2)
        self.tab2_button_3.setText("아스피린 - 걸")
        self.tab2_button_3.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab2_button_3.setStyleSheet("background-color: #99c1f1;")
        self.tab2_button_3.move(81, 367)
        self.tab2_button_3.adjustSize()
        self.tab2_button_3.resize(116, 36)
        self.tab2_button_3.clicked.connect(self._tab2_button_3_on_event)

        self.tab2_hline_1 = QFrame(page_2)
        self.tab2_hline_1.setFrameShape(QFrame.Shape.HLine)
        self.tab2_hline_1.setFrameShadow(QFrame.Shadow.Sunken)
        self.tab2_hline_1.move(35, 126)
        self.tab2_hline_1.adjustSize()
        self.tab2_hline_1.resize(608, 36)

        self.tab2_vline_1 = QFrame(page_2)
        self.tab2_vline_1.setFrameShape(QFrame.Shape.VLine)
        self.tab2_vline_1.setFrameShadow(QFrame.Shadow.Sunken)
        self.tab2_vline_1.move(307, 44)
        self.tab2_vline_1.adjustSize()
        self.tab2_vline_1.resize(36, 631)

        self.tab2_lineedit_2 = QLineEdit(page_2)
        self.tab2_lineedit_2.setPlaceholderText("텍스트 입력")
        self.tab2_lineedit_2.setText("   노래")
        self.tab2_lineedit_2.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab2_lineedit_2.setStyleSheet("background-color: #8ff0a4;")
        self.tab2_lineedit_2.move(464, 58)
        self.tab2_lineedit_2.adjustSize()
        self.tab2_lineedit_2.resize(74, 39)

        self.tabs.addTab(page_2, "쉬었다 합시다")

        page_3 = QWidget()
        page_3.setFixedSize(1100, 733)
        page_3.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_3.setStyleSheet("background-color: #deddda;")

        self.tabs.addTab(page_3, "윈도우 현황")

    def _tab2_button_1_on_event(self):
        open_url("https://youtu.be/_lKiuqlg4ro?si=BnGTCMSJ1Nd_5VWC")

    def _tab2_button_2_on_event(self):
        open_url("https://youtu.be/3smn8BRrKKM?si=9YymxC7vznMOU2vE")

    def _tab2_button_3_on_event(self):
        open_url("https://youtu.be/QvbvibmiEmM?si=iI5yTWsD07JMID-a")


def main():
    app = QApplication(sys.argv)
    window = GeneratedApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
