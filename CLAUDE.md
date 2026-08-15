# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 참고하는 가이드다.

## 작업 방식

사용자가 지시하는 작업은 진행할지 묻지 말고 바로 실행한다. 단, 되돌리기 힘든 파괴적인 작업(예: 파일/브랜치
삭제, 강제 push 등)은 여전히 신중하게 판단한다.

**빌더 앱 자체의 창 크기(`builder_state.json`의 `window.width`/`window.height`)는 사용자가 직접
요청하지 않는 한 절대 바꾸지 않는다.** 새 위젯을 추가하거나 배치하다가 지금 창 크기로는 자리가
부족하더라도, 창을 넓히지 말고 위젯 크기/배치를 조정해서 기존 창 크기 안에 맞춘다. 창 크기 자체를
바꾸는 건 오직 사용자가 그걸 명시적으로 요청했을 때만 한다.

## 사용법 문서 최신 상태 유지

`md_files/how_to_use.md`는 빌더 실행 방법, 빌더 사용 흐름(위젯 드래그/이동/크기조절/삭제/복사·붙여넣기,
탭 관리 등), standalone 앱 내보내기·실행 방법을 담고 있다. **동작 방식이 바뀌는 변경(새 기능 추가, 버튼
이름 변경, 실행 절차 변경 등)을 할 때마다 `md_files/how_to_use.md`도 함께 업데이트한다.** 문서가 실제
동작과 어긋나지 않도록, 코드 변경과 같은 턴에 문서 반영까지 끝내는 것을 기본으로 한다.

`md_files/progress_status.md`는 "지금까지 뭐가 되어 있고 다음에 뭘 이어서 할 수 있는지"를 보여주는
현재 상태 스냅샷이다 (현재 탭 구성, 알려진 미완/보류 항목 등). 큰 기능 단위 작업이 끝날 때마다 (매
사소한 수정마다는 아니고) 이 파일도 최신 상태로 갱신한다.

## 프로젝트 목적

이 프로젝트는 **사용자가 코딩 없이 자신이 원하는 간단한 툴(GUI 앱)을 직접 만들 수 있는 프로그램**을 제공한다.
위젯(버튼/드롭박스/텍스트박스 등)을 캔버스에 드래그해 화면을 구성하고, 위젯을 눌렀을 때의 동작은
자연어로 설명하면 로컬 `claude` CLI가 코드를 생성해 위젯에 연결해준다. 자세한 사용 흐름과 파일 구성은
`md_files/how_to_use.md` 참고.

## 핵심 원칙 (지켜야 할 방향성)

1. **목적** — 사용자가 원하는 간단한 툴을 직접 만들 수 있게 하는 것이 이 프로그램의 존재 이유다.
   기능을 추가/변경할 때 이 목적에서 벗어나 불필요하게 복잡해지지 않도록 한다.

2. **참고용 기본 예제 제공** — 사용자가 참고할 수 있는 기본 예제(간단한 위젯 + 동작 조합)를 제공한다.
   `executable_py/2026_07_26/app.py`가 내보내기 결과물의 예시로 남아 있고, 실제로는 빌더를 실행하면
   `builder_state.json`에 저장된 실사용 탭 구성(git/wiki/윈도우 현황/alarm/쉬었다 합시다)이 그대로
   화면에 뜨기 때문에 사용자가 바로 참고할 수 있는 상태다. 다만 이건 실사용 데이터가 쌓인 것이지
   교육용으로 정리된 최소 예제는 아니다. 예제를 추가/수정할 때는 실제로 동작하는 최소 예제(위젯 1~2개 +
   자연어로 만든 동작)를 유지한다.

3. **독립 실행(standalone) 내보내기** — 사용자가 빌더로 만든 툴은 빌더나 `claude` CLI 없이도 단독으로
   실행 가능해야 하며, 사용자가 원하는 위치에 파일로 저장할 수 있어야 한다. 이미 `exporter.py`
   (`generate_source`/`export_to_file`)와 `palette_window.py`의 "실행 py 저장" 버튼
   (`CanvasWindow.export_dialog` 호출)으로 구현되어 있다 (`QFileDialog.getSaveFileName`으로 저장 위치·
   파일명 선택). 내보낸 `.py`는 PySide6만 있으면 `venv\Scripts\python.exe 파일.py`로 실행된다 — 이
   성질을 깨는 변경(빌더 전용 모듈 임포트, `claude` CLI 의존 코드 포함 등)은 피한다.

4. **예제를 화면에 노출** — 프로그램(`main.py`)을 실행하면 사용자가 참고할 수 있는 예제가 화면에 보여야
   한다. 현재는 `builder_state.json` 자동 복원(`CanvasTabs.__init__`)으로 이전에 저장된 탭 구성이
   그대로 뜨는 방식으로 사실상 충족되고 있다 (빈 캔버스가 아님). 다만 이 상태는 사용자의 실사용
   데이터이지 처음 쓰는 사람을 위해 큐레이션된 예제는 아니다 — 별도의 "예제 보기" 진입점이나 최초
   실행 시 전용 예제 탭을 추가하는 방식은 여전히 검토 대상이다.

## 실행 방법

```powershell
cd C:\repository\ai-gui-builder-app
venv\Scripts\pythonw.exe main.py
```

시스템 파이썬에는 PySide6가 없으므로 반드시 이 venv를 사용한다. `python.exe`(콘솔 서브시스템)로 실행하면
"python.exe"라는 제목의 불필요한 콘솔 창이 캔버스/팔레트 창과 함께 하나 더 뜨므로, 반드시 windowless
버전인 `pythonw.exe`를 사용한다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `main.py` | 진입점. cm→px 변환, 캔버스/팔레트 두 창 생성 |
| `palette_window.py` | 위젯 팔레트 창 (드래그 원본 + 저장 버튼) |
| `canvas_window.py` | 캔버스 창. 드롭 처리, 위젯 레지스트리, 우클릭 메뉴, 내보내기 |
| `behavior_dialog.py` | "동작 설정" 다이얼로그 (자연어 입력 → 코드 생성/미리보기/저장) |
| `ai_client.py` | `claude` CLI 호출해 동작 코드 생성 (허용 함수 화이트리스트 프롬프트) |
| `code_binder.py` | 생성 코드를 제한된 네임스페이스에서 실행, 위젯 시그널에 바인딩 |
| `exporter.py` | 캔버스 상태를 독립 실행 가능한 `.py` 소스로 직렬화 |
| `alarm_widget.py` | "알람 시계" 위젯 (캘린더/시간 선택, 남은 시간 표시, 아날로그 시계, 자연어 알람 등록(`claude` CLI 호출), `alarm_state.json` 저장/복원) |
| `window_status_widget.py` | "윈도우 현황" 위젯 (Windows 버전/CPU/메모리/디스크/휴지통, `ctypes`+`winreg`+`subprocess` 사용, 추가 pip 패키지 없음) |
| `git_widget.py` | "git" 위젯 (local/remote 비교·stash 6쌍, local drive 검색, 전체 status check. `git` CLI 필요) |
| `theme.py` | 빌더 창(캔버스/팔레트)에 적용하는 앱 전역 QSS. `main.py`에서 `QApplication.setStyleSheet`로 적용. standalone 내보내기에도 항상 함께 포함됨 |
| `tab_bar.py` | 탭바 구현 (`ColorTabBar`: 둥근 모서리, 탭별 색깔, 선택된 탭 볼드). 빌더/standalone 양쪽에서 같은 소스 파일 그대로 사용 |
| `md_files/` | 문서(`how_to_use.md`, `tool_requirement.md`) 모음 |
| `executable_py/` | "실행 py 저장" 버튼을 누르면 저장 다이얼로그가 기본으로 여기서 시작한다. 내보낸 `.py` 결과물들을 날짜별 하위 폴더로 정리해 모아두는 곳 (예: `executable_py/2026_07_26/app.py`) |
| `standalone/` | "standalone 실행 파일 저장"(.exe) 버튼을 누르면 저장 다이얼로그가 기본으로 여기서 시작한다 |

자세한 내용(생성 코드가 쓸 수 있는 함수, 위젯 간 참조 방법 등)은 `md_files/how_to_use.md`를 참고한다.
