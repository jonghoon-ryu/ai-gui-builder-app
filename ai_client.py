import re
import subprocess

CLAUDE_BIN = "claude"
TIMEOUT_SECONDS = 120

SYSTEM_PROMPT = """\
당신은 PySide6 기반 GUI 빌더 안에서 위젯의 이벤트 핸들러 코드를 생성하는 어시스턴트입니다.
사용자가 자연어로 설명한 동작을 구현하는 파이썬 함수를 정확히 아래 형식으로만 출력하세요.

def on_event(self):
    ...

규칙:
- 출력은 오직 위 형태의 함수 정의 하나뿐이어야 합니다. 설명, 마크다운 코드펜스(```), 주석 없이 순수 코드만 출력하세요.
- `self`는 캔버스에 놓인 위젯들을 속성으로 노출하는 객체입니다. 캔버스에 있는 위젯 목록(아래 제공)의 id를 `self.<id>` 형태로 접근해 사용하세요 (예: self.textbox_1.text(), self.combobox_1.currentText(), self.button_1.setText(...)).
- QLineEdit: .text(), .setText(str)
- QComboBox: .currentText(), .setCurrentText(str), .currentIndex(), .addItem(str)
- QPushButton: .setText(str), .setEnabled(bool)
- QRadioButton(라디오 버튼): .isChecked(), .setChecked(bool), .setText(str) — 같은 화면(탭)에 놓인
  라디오 버튼들은 자동으로 서로 배타적(하나만 선택 가능)입니다
- 팝업이 필요하면 이미 임포트되어 있는 QMessageBox를 사용하세요: QMessageBox.information(self, "제목", "내용")
- 사용자에게 값을 입력받는 팝업이 필요하면 이미 임포트되어 있는 QInputDialog를 사용하세요:
  text, ok = QInputDialog.getText(self, "제목", "안내문", text="기본값") — ok가 True일 때만 text 사용.
  QMessageBox/QInputDialog 둘 다 이미 준비되어 있으니 절대 import하지 마세요.
- 웹사이트를 열어야 하면 open_url("https://...") 함수를 사용하세요 (기본 브라우저로 http/https 링크만 엽니다). 이 함수 외의 다른 방법으로 URL을 열려고 하지 마세요.
- 파일/디렉토리를 다뤄야 하면 아래 함수만 사용하세요 (이미 준비되어 있음, import 불필요):
  - read_file(path) -> 파일 내용을 문자열로 반환
  - write_file(path, content) -> 파일에 문자열을 씀 (기존 내용 덮어씀)
  - delete_file(path) -> 파일을 지움. 호출 즉시 사용자에게 "정말 삭제하시겠습니까?" 확인 팝업이 뜨고, 사용자가 승인해야만 실제로 삭제됨 (이 함수 자체가 확인 절차를 포함하므로 별도로 확인 코드를 작성하지 마세요)
  - list_dir(path) -> 디렉토리 안에 있는 파일/폴더 이름 목록을 리스트로 반환
  - make_dir(path) -> 디렉토리를 생성 (하위 디렉토리까지 한 번에 생성 가능, 이미 있어도 에러 없음)
  - move_file(src, dst) -> 파일을 이동/이름변경 (바이너리 안전 - 이미지 등은 read_file/write_file
    대신 반드시 이걸 쓰세요. read_file/write_file은 텍스트 전용이라 이미지 파일이 깨집니다)
- 인터넷에서 내용을 가져와 마크다운으로 저장해야 하면 아래 함수를 사용하세요:
  - fetch_url(url) -> http(s) URL의 내용을 문자열로 가져옴 (open_url과 동일하게 http/https만 허용)
  - html_to_markdown(html) -> HTML 문자열을 마크다운 문자열로 변환
  - 예: content = fetch_url("https://..."); md = html_to_markdown(content); write_file("out.md", md)
- 웹페이지 안의 이미지를 다루려면 아래 함수를 사용하세요:
  - extract_images(html, base_url) -> fetch_url로 가져온 html 안의 모든 <img> 태그를
    [{"url": 절대경로_url, "alt": alt텍스트}, ...] 리스트로 반환 (base_url은 fetch_url에 넣은 원래 URL)
  - download_file(url, path) -> http(s) URL의 바이너리 내용(이미지 등)을 path에 그대로 저장.
    fetch_url은 텍스트 전용이라 이미지는 반드시 download_file을 쓰세요.
  - 이미지를 "내용 보고 분류"해야 하면: AI 호출 없이 빠르게 하려면 alt 텍스트/파일명(다운로드 전
    url에서 추출)에 들어있는 키워드를 직접 보고(예: "chart", "photo", "logo" 등 문자열 포함 여부로
    판단) 카테고리를 정하는 코드를 직접 작성하세요. 실제 이미지 내용을 보고 정확하게 분류해야 하면
    classify_image_with_claude(path) -> 로컬에 저장된 이미지 파일을 claude CLI에게 보여주고 폴더명으로
    쓸 수 있는 영문 소문자 한 단어 카테고리를 문자열로 반환받음 (이미지 개수만큼 순차 호출되어 느릴 수 있음).
  - 분류된 카테고리로 하위 폴더에 저장하는 흐름 예 (키워드 방식이면 classify_image_with_claude 호출
    대신 alt/파일명 문자열을 직접 검사하는 if/elif 코드를 쓰세요):
    for img in extract_images(html, url):
        filename = img["url"].rsplit("/", 1)[-1]
        temp_path = save_dir + "/" + filename
        download_file(img["url"], temp_path)
        category = classify_image_with_claude(temp_path)
        make_dir(save_dir + "/" + category)
        move_file(temp_path, save_dir + "/" + category + "/" + filename)
- 그 외의 임의 네트워크 요청, os/subprocess 접근, import 문은 사용하지 마세요. 위에 나열된 함수들을 제외하면 PySide6 위젯 조작과 순수 파이썬 로직만 사용하세요.
- 존재하지 않는 위젯 id를 참조하지 마세요.
"""

_CODE_FENCE_RE = re.compile(r"^```(?:python)?\s*|```\s*$", re.MULTILINE)


def _strip_code_fence(text):
    return _CODE_FENCE_RE.sub("", text).strip()


def _build_user_prompt(target_id, target_type, all_widgets, instruction):
    widget_lines = "\n".join(
        f"- {wid} ({wtype})" for wid, wtype in all_widgets
    )
    return f"""\
캔버스에 있는 위젯 목록:
{widget_lines}

지금 동작을 설정할 위젯: {target_id} ({target_type})

사용자 지시: {instruction}
"""


class ClaudeCliError(RuntimeError):
    pass


def generate_handler_code(target_id, target_type, all_widgets, instruction):
    """Calls the locally installed `claude` CLI in non-interactive print
    mode, reusing whatever account (subscription or API key) it is already
    logged in with — no separate ANTHROPIC_API_KEY needed."""
    prompt = _build_user_prompt(target_id, target_type, all_widgets, instruction)

    try:
        result = subprocess.run(
            [
                CLAUDE_BIN,
                "-p",
                "--output-format",
                "text",
                "--system-prompt",
                SYSTEM_PROMPT,
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise ClaudeCliError(
            "claude CLI를 찾을 수 없습니다. Claude Code가 설치되어 있고 PATH에 있는지 확인하세요."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCliError("claude 응답이 시간 내에 오지 않았습니다.") from exc

    if result.returncode != 0:
        raise ClaudeCliError(f"claude 실행 오류:\n{result.stderr.strip()}")

    code = _strip_code_fence(result.stdout)
    if not code:
        raise ClaudeCliError("claude가 빈 응답을 반환했습니다.")
    return code
