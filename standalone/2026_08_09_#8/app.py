import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as _html_to_markdown
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStyle,
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


def list_dir(path):
    return sorted(os.listdir(path))


def make_dir(path):
    os.makedirs(path, exist_ok=True)


def move_file(src, dst):
    shutil.move(src, dst)


_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _urlopen_with_retry(request, timeout=15, retries=3):
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
    """Fetches an http(s) URL's body as text."""
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 가져올 수 있습니다: {url!r}")
    request = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})
    with _urlopen_with_retry(request) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_markdown(html):
    return _html_to_markdown(html)


def extract_images(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        images.append({"url": urljoin(base_url, src), "alt": img.get("alt") or ""})
    return images


def download_file(url, path):
    if not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
        raise ValueError(f"http(s) URL만 다운로드할 수 있습니다: {url!r}")
    request = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})
    with _urlopen_with_retry(request) as response:
        data = response.read()
    with open(path, "wb") as f:
        f.write(data)


def classify_image_with_claude(path):
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


def _browse_directory(line_edit):
    directory = QFileDialog.getExistingDirectory(
        line_edit, "디렉토리 선택", line_edit.text(),
        options=QFileDialog.Option.DontUseNativeDialog,
    )
    if directory:
        line_edit.setText(directory)


def _prompt_url(line_edit):
    text, ok = QInputDialog.getText(
        line_edit, "URL 입력", "URL:", QLineEdit.EchoMode.Normal, line_edit.text()
    )
    if ok and text:
        line_edit.setText(text)


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

        self.tab1_urlbox_1 = QLineEdit(page_1)
        self.tab1_urlbox_1.setPlaceholderText("URL 입력 (https://...)")
        _action = self.tab1_urlbox_1.addAction(self.tab1_urlbox_1.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon), QLineEdit.ActionPosition.TrailingPosition)
        _action.triggered.connect(lambda: _prompt_url(self.tab1_urlbox_1))
        self.tab1_urlbox_1.setText("https://namu.wiki/w/LG%EC%A0%84%EC%9E%90")
        self.tab1_urlbox_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab1_urlbox_1.setStyleSheet("background-color: #ffbe6f;")
        self.tab1_urlbox_1.move(161, 166)
        self.tab1_urlbox_1.adjustSize()
        self.tab1_urlbox_1.resize(382, 27)

        self.tab1_dirbox_1 = QLineEdit(page_1)
        self.tab1_dirbox_1.setPlaceholderText("디렉토리 경로 입력")
        _action = self.tab1_dirbox_1.addAction(self.tab1_dirbox_1.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon), QLineEdit.ActionPosition.TrailingPosition)
        _action.triggered.connect(lambda: _browse_directory(self.tab1_dirbox_1))
        self.tab1_dirbox_1.setText("/mnt/0C084C3768880E8A/RyuVault/wiki/LG")
        self.tab1_dirbox_1.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tab1_dirbox_1.setStyleSheet("background-color: #ffffff;")
        self.tab1_dirbox_1.move(161, 270)
        self.tab1_dirbox_1.adjustSize()
        self.tab1_dirbox_1.resize(384, 29)

        self.tab1_button_1 = QPushButton("버튼", page_1)
        self.tab1_button_1.setText("가져와서 md 로 변환")
        self.tab1_button_1.move(103, 479)
        self.tab1_button_1.adjustSize()
        self.tab1_button_1.resize(163, 42)
        self.tab1_button_1.clicked.connect(self._tab1_button_1_on_event)

        self.tab1_radiobutton_1 = QRadioButton("옵션", page_1)
        self.tab1_radiobutton_1.setAutoExclusive(False)
        self.tab1_radiobutton_1.setText("알아서 image 파일 분류")
        self.tab1_radiobutton_1.move(101, 362)
        self.tab1_radiobutton_1.adjustSize()
        self.tab1_radiobutton_1.resize(195, 25)

        self.tab1_radiobutton_2 = QRadioButton("옵션", page_1)
        self.tab1_radiobutton_2.setAutoExclusive(False)
        self.tab1_radiobutton_2.setText("클로드의 도움을 받아 상세히 image 파일 분류")
        self.tab1_radiobutton_2.move(102, 392)
        self.tab1_radiobutton_2.adjustSize()
        self.tab1_radiobutton_2.resize(350, 25)

        self.tab1_lineedit_1 = QLineEdit(page_1)
        self.tab1_lineedit_1.setPlaceholderText("텍스트 입력")
        self.tab1_lineedit_1.setText("URL :")
        self.tab1_lineedit_1.setFrame(False)
        self.tab1_lineedit_1.move(98, 158)
        self.tab1_lineedit_1.adjustSize()
        self.tab1_lineedit_1.resize(55, 40)

        self.tab1_lineedit_2 = QLineEdit(page_1)
        self.tab1_lineedit_2.setPlaceholderText("텍스트 입력")
        self.tab1_lineedit_2.setText("local :")
        self.tab1_lineedit_2.setFrame(False)
        self.tab1_lineedit_2.move(99, 263)
        self.tab1_lineedit_2.adjustSize()
        self.tab1_lineedit_2.resize(55, 40)

        tab1_radio_group_0 = QButtonGroup(self)
        tab1_radio_group_0.addButton(self.tab1_radiobutton_1)
        tab1_radio_group_0.addButton(self.tab1_radiobutton_2)
        self.tab1_radiobutton_1.setChecked(True)

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

        page_4 = QWidget()
        page_4.setFixedSize(1100, 733)

        self.tabs.addTab(page_4, "alarm")

    def _tab1_button_1_on_event(self):
        from PySide6.QtWidgets import QInputDialog

        filename, ok = QInputDialog.getText(
            self, "MD 파일 이름", "저장할 md 파일 이름을 입력하세요:", text="output.md"
        )
        if not ok or not filename.strip():
            return
        filename = filename.strip()
        if not filename.lower().endswith(".md"):
            filename = filename + ".md"

        url = self.tab1_urlbox_1.text().strip()
        save_dir = self.tab1_dirbox_1.text().strip()

        if not url:
            QMessageBox.information(self, "오류", "URL을 입력해주세요.")
            return
        if not save_dir:
            QMessageBox.information(self, "오류", "저장할 디렉토리를 입력해주세요.")
            return

        make_dir(save_dir)

        try:
            html = fetch_url(url)
        except Exception as e:
            QMessageBox.information(self, "오류", f"문서를 가져오는 중 오류가 발생했습니다: {e}")
            return

        md = html_to_markdown(html)

        save_path = save_dir.rstrip("/") + "/" + filename
        write_file(save_path, md)

        if self.tab1_radiobutton_1.isChecked():
            QMessageBox.information(self, "이미지 처리", "이미지 파일을 자동으로 분류하여 저장합니다.")
        elif self.tab1_radiobutton_2.isChecked():
            QMessageBox.information(self, "이미지 처리", "Claude에게 요청하여 이미지 파일을 분류하여 저장합니다.")

        QMessageBox.information(self, "완료", f"{save_path} 에 저장되었습니다.")

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
