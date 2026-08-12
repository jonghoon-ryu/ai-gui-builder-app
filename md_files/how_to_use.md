# how_to_use.md — ai-gui-builder-app 사용법

일반 GUI 빌더와 다른 점: 위젯(버튼 등)을 눌렀을 때의 동작을 사용자가 직접 코딩하지 않고,
**자연어로 설명하면 로컬에 설치된 Claude Code(`claude` CLI)가 그 동작을 구현하는 코드를 생성**하고,
그 코드가 **빌더 화면에서 바로 실행 가능한 상태로 위젯에 연결**된다.

## 0. 처음 사용하는 사람을 위한 설치 가이드 (Linux / Windows)

이 프로그램을 한 번도 안 써본 사람이 자기 컴퓨터에 처음 준비하는 절차다. 공통으로 필요한 것:

- **Python 3.9 이상** (PySide6가 요구하는 최소 버전대)
- **Claude Code(`claude` CLI)** — 위젯에 자연어로 동작을 만들어 붙이는 기능(동작 설정)에 필요.
  단순히 빌더를 켜서 화면만 구성하는 것은 `claude` CLI 없이도 되지만, "동작 설정"을 쓰려면 반드시 있어야
  하고 로그인도 되어 있어야 한다. 설치 후 최초 한 번 로그인이 필요하다.
  ```bash
  npm install -g @anthropic-ai/claude-code
  claude login
  ```
  (Node.js/npm이 없다면 먼저 설치해야 한다.)

### Linux에서 처음 설치하기

1. 프로젝트 폴더를 원하는 위치로 받는다 (예: `git clone` 또는 압축 해제).
2. 터미널에서 그 폴더로 이동한다.
   ```bash
   cd /경로/ai-gui-builder-app
   ```
3. 가상환경(venv)을 새로 만든다.
   ```bash
   python3 -m venv venv
   ```
   - 만약 `The virtual environment was not created successfully` 같은 오류가 나면 `python3-venv`
     패키지가 없는 것이다 (Debian/Ubuntu 계열): `sudo apt install python3-venv` 로 설치 후 다시 시도.
4. venv 안에 필요한 패키지를 설치한다.
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```
   - `error: externally-managed-environment` 오류는 venv 밖(시스템 파이썬)에 직접 설치하려 할 때만
     발생한다. 반드시 `./venv/bin/pip`를 써야 하며, 시스템 `pip3 install`은 사용하지 않는다.
5. 빌더를 실행한다.
   ```bash
   ./venv/bin/python main.py
   ```
6. (선택) 자연어로 동작을 만들고 싶다면, 위의 Claude Code 설치·로그인이 되어 있어야 한다. `claude`가
   PATH에 없으면 실행 시 안내 팝업이 뜬다.

### Windows에서 처음 설치하기

1. [python.org](https://www.python.org/downloads/)에서 Python 설치 — 설치 화면에서 **"Add python.exe
   to PATH"** 체크박스를 반드시 켠다.
2. 프로젝트 폴더를 원하는 위치로 받는다 (`git clone` 또는 zip 압축 해제).
3. **PowerShell**(또는 명령 프롬프트)을 열고 그 폴더로 이동한다.
   ```powershell
   cd C:\경로\ai-gui-builder-app
   ```
4. 가상환경을 만든다.
   ```powershell
   py -m venv venv
   ```
5. venv 안에 필요한 패키지를 설치한다.
   ```powershell
   .\venv\Scripts\pip install -r requirements.txt
   ```
6. 빌더를 실행한다.
   ```powershell
   .\venv\Scripts\python main.py
   ```
   - PowerShell에서 `venv\Scripts\Activate.ps1`로 가상환경을 "활성화"해서 쓰고 싶다면, 스크립트 실행이
     막혀 있을 수 있다 (`이 시스템에서 스크립트를 실행할 수 없으므로...` 오류). 그럴 땐 관리자 권한
     PowerShell에서 한 번만 아래를 실행:
     ```powershell
     Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
     ```
     활성화하지 않고 위 5-6번처럼 `.\venv\Scripts\pip`, `.\venv\Scripts\python`을 매번 직접 써도 된다
     (이쪽이 더 간단하고 문제가 적다).
7. (선택) 자연어 동작 생성 기능을 쓰려면 Windows에도 Node.js를 설치한 뒤 위의 `npm install -g
   @anthropic-ai/claude-code` → `claude login`을 PowerShell에서 그대로 실행한다.

### 설치 후 공통

- 실행하면 "나만의 tool"(캔버스)과 "위젯 팔레트" 두 창이 뜬다. 자세한 사용법은 아래 1번부터 참고.
- 이후로는 매번 `npm`/`pip install` 없이, 아래 "1. 빌더 실행시키는 방법"의 명령만 실행하면 된다.

## 1. 빌더(위젯 만드는 도구) 실행시키는 방법

```bash
cd /home/ryuj/Ryu/ai-gui-builder-app
./venv/bin/python main.py
```

시스템 파이썬(`python3`)에는 PySide6가 없으므로 반드시 이 프로젝트 전용 가상환경인
`./venv/bin/python`으로 실행해야 한다.

실행하면 두 창이 뜬다:
- **나만의 tool** (왼쪽) — 30cm×20cm 크기, 탭으로 여러 화면 구성 가능. 완성될 앱이 실제로 살아있는 화면.
- **위젯 팔레트** (오른쪽) — 왼쪽 컬럼에 드롭박스/누름 버튼/텍스트박스/URL 입력창/디렉토리 입력창/
  라디오 버튼/가로선/세로선 원본이 나열되고, 세로 구분선 건너 오른쪽 컬럼에 "틀 저장"/"standalone
  저장" 버튼이 따로 있음 (두 컬럼 너비는 서로 같게 맞춰져 있음).

동작 생성 단계(자연어 → 코드)에는 `claude` CLI가 로그인되어 있어야 한다 (별도 API 키 불필요,
지금 로그인된 Claude Code 계정을 그대로 사용).

앱을 껐다 켜면 이전에 만들어둔 탭/위젯 구성이 `builder_state.json`에서 자동으로 복원된다
(캔버스 창을 닫을 때 자동 저장되고, 팔레트의 "틀 저장" 버튼으로 언제든 수동 저장도 가능).

## 2. 빌더에서 툴 만드는 흐름

1. 팔레트에서 드롭박스/버튼/텍스트박스/URL 입력창/디렉토리 입력창/라디오 버튼/가로선/세로선을
   캔버스로 **드래그** (팔레트에는 원본이 그대로 남음, 복사 방식)
   - **URL 입력창**과 **디렉토리 입력창**은 오른쪽 끝에 아이콘 버튼이 내장되어 있다. URL 입력창의
     아이콘을 누르면 URL을 입력할 수 있는 작은 팝업 창이 뜨고(직접 타이핑도 그대로 가능), 디렉토리
     입력창의 아이콘을 누르면 디렉토리 선택 창이 떠서 고른 경로가 입력창에 채워진다. 이 아이콘들은
     standalone으로 내보낸 앱에서도 그대로 동작한다.
   - **가로선/세로선**은 진하고 두꺼운 직선으로 그려져 눈에 잘 띈다 (캔버스, 팔레트, standalone
     내보내기 결과물 모두 동일한 스타일).
   - **라디오 버튼**은 같은 탭 안에서도 서로 다른 그룹을 가질 수 있다. 팔레트에서 새로 드래그한
     라디오 버튼은 각각 자기 자신만의 독립된 그룹으로 시작하고, 우클릭 메뉴의 **"옵션 추가"**로 만든
     라디오 버튼만 원본과 같은 그룹(서로 배타적)이 된다. 예: "성별"(남/여) 그룹과 "크기"(소/중/대)
     그룹을 같은 화면에 놓아도 서로 간섭하지 않는다. 각 그룹의 **첫 번째로 만들어진 라디오 버튼이
     기본으로 선택된 상태**로 시작한다(그룹이 빈 상태로 시작하지 않도록).
2. 캔버스에 놓인 위젯을 **우클릭**하면 메뉴가 뜬다:
   - 맨 위에 **"ID: <위젯id>"**가 항상 표시됨 (클릭은 안 되는 안내용) — 다른 위젯의 "동작 설정"에서
     이 위젯을 `self.<id>`로 참조할 때 이 id를 그대로 쓰면 됨
   - **동작 설정...** — 자연어로 동작 설명 → "생성"(Claude 호출) → 코드 확인/수정 → "저장"해야 실제로 위젯에 연결됨
   - **색깔 변경** — 위젯 배경색 변경
   - **이름 변경** — 텍스트가 있는 위젯(버튼/텍스트박스/URL 입력창/디렉토리 입력창/라디오 버튼)만; 새 이름 입력 후 Yes/No
   - **폰트 설정** — 텍스트박스류(텍스트박스/URL 입력창/디렉토리 입력창)만; 폰트 종류/크기 선택 창(`QFontDialog`)이 뜸
   - **테두리 없애기** — 텍스트박스류만; 누르면 그 위젯의 테두리가 바로 사라짐 (`QLineEdit.setFrame(False)`)
   - **옵션 추가** / **옵션 제거** — 라디오 버튼만; 추가하면 바로 아래에 새 라디오 버튼이 하나 더 생기고
     (같은 탭 안에서 자동으로 배타적 그룹), 제거하면 그 라디오 버튼 자체가 삭제됨
   - (가로선/세로선은 "동작 설정..."이 없음 — 클릭 동작 자체가 없는 위젯이라서)
3. 위젯을 왼쪽 버튼으로 눌러서 끌면 이동, 가장자리를 눌러서 끌면 크기 조절 가능
4. 캔버스 빈 공간에서 마우스로 박스를 그리면(러버밴드) 그 안에 걸치는 위젯들이 선택됨
   - 선택 후 **Delete/Backspace** — 삭제
   - 선택 후 **Ctrl+C** → **Ctrl+V** — 복사/붙여넣기 (다른 탭에도 붙여넣기 가능)
5. 탭(화면) 우클릭 → **delete**(삭제 확인)/**탭 제목 편집**/**바탕색** 메뉴, 탭을 눌러서 좌우로 끌면 순서 변경
6. 동작이 연결된 위젯을 클릭하면 생성된 동작이 실제로 실행됨
   (버튼→clicked, 드롭박스→currentIndexChanged, 텍스트박스→returnPressed)

## 3. 알람 시계 위젯

**"alarm"** 탭에 처음부터 놓여있는 위젯이다 (팔레트에는 없음 — 드래그해서 새로 만드는 게 아니라
"alarm" 탭 전용으로 미리 배치해둔 것). 다른 위젯들과 다르게 그 자체로 하나의 작은 완성된 도구다
(텍스트/색깔 같은 일반 속성 대신 자체 UI를 가짐):

- **일회성 알람 추가** 버튼(위) / **주기적 알람 추가** 버튼(아래) — 왼쪽 위에 세로로 붙어 있고,
  둘 사이에 여유 있는 간격이 있음
  - 일회성: 달력에서 날짜 선택 → 시간 + **알람 메시지**(기본값 "시간이 됐어요 !!", 직접 수정 가능)
    선택 → 알람 등록
  - 주기적: 시작/끝 날짜 선택 → 반복할 요일(월~일, 복수 선택 가능) 선택 → 시간 + 알람 메시지 선택
    → 알람 등록
- 그 옆(버튼 컬럼보다 약간 왼쪽으로 붙은 위치)에 오늘 날짜가 선택된 **달력**이, 그 오른쪽에 실시간
  **아날로그 시계**(180×180px)가 표시됨
- **주기적 알람 추가** 버튼 아래(동일한 간격을 두고)에 **자연어로 알람 설정** 입력칸이 있음 — 좁고
  세로로 긴 여러 줄 입력칸으로, "내일 오전 9시에 회의 알람", "매주 화목 저녁 8시에 운동" 처럼 여러
  줄에 걸쳐 문장을 쓸 수 있다. **Enter는 줄바꿈**이고, **Ctrl+Enter** 또는 그 아래 "자연어로 알람
  설정" 버튼을 눌러야 실제로 제출된다. 제출하면 로컬 `claude` CLI가 문장을 해석해 일회성/주기적
  알람으로 자동 등록함. 응답을 기다리는 동안에도 창이 멈추지 않으며, 해석에 실패하면 오류 팝업이 뜸.
  **claude CLI 자체가 없으면** "Claude Code 필요"라는 제목의 팝업으로 설치(`npm install -g
  @anthropic-ai/claude-code`)·로그인(`claude login`) 안내가 뜬다
- **알람 목록** 제목 아래 목록에 등록된 알람이 날짜/시간 정보 + **알람 메시지**(따옴표로 표시) +
  "다음 알람까지 남은 시간"과 함께 실시간(1초마다)으로 갱신되어 표시됨
  (예: `일회성: 2026-08-13 09:00 — "회의 알람"    남은 시간: 17시간 7분`). 각 알람 줄 오른쪽에
  **"끄기"/"켜기" 버튼**과 둥근 **× 버튼**이 있음
  - "끄기"를 누르면 그 알람은 목록에 계속 보이되(글자가 회색으로 흐려지고 "꺼짐"으로 표시) 시간이
    되어도 울리지 않는다. "켜기"를 다시 누르면 정상적으로 복귀 (밀린 시간이 이미 지났다면 다음
    새로고침에 바로 울림)
  - × 버튼을 누르면 그 알람만 목록에서 완전히 삭제됨
- 알람 시간이 되면 **가로 20cm × 세로 20cm 정사각형 팝업 창**이 뜨고, 창 제목과 본문 모두에 알람
  등록 시 입력한(또는 자연어에서 자동으로 만들어진) 메시지가 표시됨. 일회성 알람은 울린 뒤 목록에서
  사라지고, 주기적 알람은 다음 반복 요일로 자동으로 넘어감 (끝 날짜가 지나면 더 이상 표시 안 됨)
- 패널 기본 크기 840×640 (처음 크기 대비 2배)

**알아둘 점**: 등록한 알람 목록 자체는 앱을 껐다 켜면 초기화된다 (위젯의 위치/크기만 저장되고, 알람
내용은 저장 대상이 아님). standalone으로 내보내도 동일하게 동작하며(내보낸 앱에도 `alarm_widget.py`
소스가 그대로 포함됨, 자연어 알람 설정 기능도 포함되어 실행 PC에 `claude` CLI가 있으면 그대로
동작함), 알람 목록이 비어있는 상태로 시작한다.

## 4. standalone(독립 실행) 앱 만들고 실행시키는 방법

### 4-1. 빌더에서 내보내기

팔레트의 **"standalone 저장"** 버튼 클릭 → 폴더 선택 + 파일명 입력(`.py`) → 저장.
탭 여러 개로 만든 내용, 각 위젯의 텍스트/색깔/크기/폰트/동작이 전부 그대로 내보내진다.

내보낼 때는 `standalone/` 디렉토리 밑에 날짜(+번호)별 하위 폴더를 만들어 저장하는 것이 이 프로젝트의
정리 방식이다 (예: `standalone/2026_08_09_#2/app.py`). 프로젝트 루트가 지저분해지지 않도록 새로 내보낼
때도 이 규칙을 따른다.

### 4-2. 내보낸 앱 실행시키는 방법

**이 프로젝트의 venv를 그대로 쓰는 경우** (같은 컴퓨터에서 바로 실행할 때 가장 간단):

```bash
/home/ryuj/Ryu/ai-gui-builder-app/venv/bin/python 내보낸파일.py
```

**완전히 독립된 환경에서 실행하려는 경우** (다른 컴퓨터로 옮기거나 이 프로젝트와 분리해서 쓸 때):

```bash
cd 내보낸파일이_있는_폴더
python3 -m venv venv
./venv/bin/pip install PySide6 markdownify beautifulsoup4
./venv/bin/python 내보낸파일.py
```

내보낸 `.py` 파일은 빌더나 `claude` CLI 없이 PySide6만 있으면 실행된다.

## 5. 위젯 간 참조

생성된 코드에서 `self.<위젯id>` 형태로 캔버스의 다른 위젯을 참조/조작할 수 있다
(예: `self.textbox_1.text()`, `self.combobox_1.currentText()`, `self.radiobutton_1.isChecked()`).
id는 `종류_번호` 형식으로 자동 부여되며(`button_1`, `lineedit_1`, `combobox_1`, `radiobutton_1`, ...)
위젯에 마우스를 올리면 툴팁으로 확인 가능.

## 6. 생성 코드가 쓸 수 있는 함수 (안전을 위한 화이트리스트)

LLM이 생성한 코드는 클릭 한 번에 확인 없이 바로 실행되기 때문에, 임의의 파이썬을 다 허용하지 않고
아래로 제한한다:

- PySide6 위젯 조작 (`.text()`, `.setText()`, `.addItem()` 등) + 순수 파이썬 로직
- `QMessageBox.information(...)` 등 팝업
- `QInputDialog.getText(self, "제목", "안내문", text="기본값")` — 사용자에게 텍스트 입력받는 팝업
- `open_url("https://...")` — http/https 링크만 기본 브라우저로 열기 (file://, javascript: 등은 거부)
- `read_file(path)`, `write_file(path, content)` — 자유롭게 파일 읽기/쓰기
- `delete_file(path)` — 호출하면 항상 "정말 삭제하시겠습니까?" 확인 팝업을 거친 뒤에만 실제 삭제
- `list_dir(path)` — 디렉토리 안 파일/폴더 이름 목록 반환
- `make_dir(path)` — 디렉토리 생성 (하위 디렉토리까지 한 번에, 이미 있어도 에러 없음)
- `move_file(src, dst)` — 파일 이동/이름변경 (바이너리 안전; 이미지 등은 read_file/write_file
  대신 반드시 이걸 사용 — read_file/write_file은 텍스트 전용이라 이미지가 깨짐)
- `fetch_url(url)` — http/https URL 내용을 문자열로 가져오기 (open_url과 동일하게 스킴 제한)
- `html_to_markdown(html)` — HTML 문자열을 마크다운 문자열로 변환 (`markdownify` 라이브러리 사용)
- `extract_images(html, base_url)` — html 안의 `<img>` 태그들을 `[{"url":..., "alt":...}, ...]`로 반환
- `download_file(url, path)` — http/https URL의 바이너리 내용(이미지 등)을 그대로 저장
- `classify_image_with_claude(path)` — 로컬 이미지 파일을 `claude` CLI에게 보여주고 폴더명으로 쓸 수
  있는 영문 소문자 카테고리 단어를 받아옴 (CLI 없음/타임아웃/실패 시 "기타" 반환). 이미지 개수만큼
  순차 호출되므로 느릴 수 있음
- 그 외 `import`, os/subprocess 접근, 임의 네트워크 요청은 금지

내보낸 독립 실행 `.py` 파일에도 동일한 함수들(`open_url`/`read_file`/`write_file`/`delete_file`/
`list_dir`/`make_dir`/`move_file`/`fetch_url`/`html_to_markdown`/`extract_images`/`download_file`/
`classify_image_with_claude`)이 모듈 함수로 그대로 포함되어, 빌더 없이도 그대로 동작한다. 단
`html_to_markdown`/`extract_images`가 `markdownify`/`beautifulsoup4` 패키지를 쓰기 때문에, 내보낸
앱을 돌리는 쪽 venv에도 `pip install -r requirements.txt`(PySide6 + markdownify + beautifulsoup4)가
되어 있어야 한다. `classify_image_with_claude`를 쓰는 동작을 내보낸 앱에서 실행하려면 그 컴퓨터에도
`claude` CLI가 설치·로그인되어 있어야 한다.

## 7. 파일 구성

| 파일 | 역할 |
|---|---|
| `main.py` | 진입점. cm→px 변환(30cm×20cm), 두 창 생성 및 배치 |
| `palette_window.py` | 팔레트 창. 드래그 가능한 위젯 원본(`DraggableMixin` 기반) + "틀 저장"/"standalone 저장" 버튼 |
| `canvas_window.py` | 캔버스 창. 탭 관리, 드롭 처리, 위젯 이동/크기조절/선택/복사·붙여넣기, 위젯·탭 우클릭 메뉴, 상태 저장/복원, 내보내기 다이얼로그 |
| `behavior_dialog.py` | "동작 설정" 다이얼로그. 자연어 입력 + 코드 미리보기 + 생성(백그라운드 스레드)/저장 |
| `ai_client.py` | `claude` CLI를 서브프로세스로 호출해 `def on_event(self): ...` 코드 생성. 시스템 프롬프트로 허용 함수/제약 명시 |
| `code_binder.py` | 생성 코드를 제한된 네임스페이스에서 `exec`, 위젯 시그널에 바인딩. `open_url`/`read_file`/`write_file`/`delete_file` 정의 |
| `exporter.py` | 캔버스 상태(여러 탭 포함)를 독립 실행 가능한 `.py` 소스로 직렬화 (`generate_source`/`export_to_file`) |
| `alarm_widget.py` | "알람 시계" 위젯 구현 (`AlarmClockPanel`, `AnalogClock`, 날짜/시간 선택 다이얼로그들) |
| `builder_state.json` | 빌더 자체 상태(탭/위젯 구성) 저장 파일. 실행 시 자동 로드 |
| `md_files/` | 문서 모음 (`how_to_use.md`, `tool_requirement.md`) |
| `standalone/` | standalone 내보내기 결과물을 날짜별 하위 폴더(`2026_08_09_#2` 등)로 정리해 모아두는 곳 |
| `venv/` | PySide6가 설치된 가상환경 (`./venv/bin/python`으로 실행) |

## 8. 알아두면 좋은 것들

- **venv**: 이 프로젝트 전용 파이썬 패키지 설치 공간. 시스템 파이썬에는 PySide6가 없으므로 반드시
  `./venv/bin/python`으로 실행해야 한다.
- 위젯 id는 탭(캔버스 페이지)마다 독립적으로 순차 증가하는 카운터로 부여된다 (`button_1`, `button_2`, ...).
  위젯을 삭제해도 카운터는 줄어들지 않는다 (id 재사용 안 함).
- 저장/내보내기 다이얼로그는 `QFileDialog.Option.DontUseNativeDialog`를 사용한다 — 시스템 기본
  GTK 다이얼로그 대신 Qt 자체 다이얼로그를 써야 "새 폴더 생성" 버튼이 항상 보인다.
