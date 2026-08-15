import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QWidget,
)


def open_url(url):
    """Opens only http(s) links in the system's default browser."""
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 열 수 있습니다: {url!r}")
    QDesktopServices.openUrl(QUrl(url))


class GeneratedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        central = QWidget()
        self.setCentralWidget(central)
        central.setFixedSize(1100, 733)

        self.button_1 = QPushButton("버튼", central)
        self.button_1.move(319, 235)
        self.button_1.adjustSize()
        self.button_1.clicked.connect(self._button_1_on_event)

    def _button_1_on_event(self):
        open_url("https://ppomppu.co.kr/")


def main():
    app = QApplication(sys.argv)
    window = GeneratedApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
