import os
import shutil
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from canvas_window import CanvasWindow, get_saved_window_size
from palette_window import PaletteWindow
from theme import APP_STYLESHEET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ICON_PATH = os.path.join(BASE_DIR, "app_icon.ico")

CM_PER_INCH = 2.54
DEFAULT_DPI = 96


def cm_to_px(cm, dpi):
    return round(cm * dpi / CM_PER_INCH)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    if os.path.exists(APP_ICON_PATH):
        app.setWindowIcon(QIcon(APP_ICON_PATH))

    screen = app.primaryScreen()
    dpi_x = screen.physicalDotsPerInchX() if screen else DEFAULT_DPI
    dpi_y = screen.physicalDotsPerInchY() if screen else DEFAULT_DPI

    saved_size = get_saved_window_size()
    if saved_size and saved_size[0] and saved_size[1]:
        width_px, height_px = saved_size
    else:
        width_px = cm_to_px(30, dpi_x)
        height_px = cm_to_px(20, dpi_y)

    canvas = CanvasWindow(width_px, height_px)
    canvas.move(100, 100)
    canvas.show()

    palette = PaletteWindow(canvas_window=canvas)
    palette.show()
    app.processEvents()
    palette.move(canvas.frameGeometry().right() + 1, canvas.frameGeometry().top())

    if shutil.which("claude") is None:
        QMessageBox.information(
            canvas,
            "Claude CLI 안내",
            "claude 명령을 찾을 수 없습니다.\n"
            "위젯의 동작을 자연어로 생성하려면 Claude Code(claude CLI)가 설치되어 있고 "
            "PATH에 등록되어 있어야 합니다.",
        )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
