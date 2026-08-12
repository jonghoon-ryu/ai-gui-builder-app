import os
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
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

        self.tabs.addTab(page_2, "bookmark 1")

        page_3 = QWidget()
        page_3.setFixedSize(1100, 733)
        page_3.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        page_3.setStyleSheet("background-color: #deddda;")

        self.tabs.addTab(page_3, "bookmark 2")


def main():
    app = QApplication(sys.argv)
    window = GeneratedApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
