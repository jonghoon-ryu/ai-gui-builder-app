# progress_status.md — 현재까지 진행 상황 (다음에 이어서 시작할 때 참고)

기준 시점: 2026-08-12 저녁, Windows로 이전 후. 이 문서는 "지금 뭐가 되어 있고, 다음에 뭘 더 할 수
있는지"를 빠르게 파악하기 위한 스냅샷이다. 자세한 사용법은 `how_to_use.md`, 지금까지의 요구사항 변경
이력은 `tool_requirement.md` 참고.

## 지금 상태 (한 줄 요약)

빌더(`main.py`)는 완성도 있게 동작 중이고, 실제로 사용자가 5개 탭(git/wiki/쉬었다 합시다/윈도우 현황/
alarm)에 위젯을 채워서 쓰고 있다. 위젯 종류, 저장/복원, standalone 내보내기, 자연어 동작 생성용
화이트리스트 함수, 전용 "알람 시계"/"윈도우 현황" 위젯까지 전부 구현 완료 상태. 이제 Windows에서
직접 실행/검증됨 (아래 "Windows 이전" 참고).

## Windows 이전 (2026-08-12)

원래 Linux/WSL에서 개발되던 프로젝트를 Windows에서 직접 실행/작업하는 것으로 전환했다.
- `./venv`는 Windows용으로 새로 만들어져 있음 (`venv\Scripts\python.exe`)
- 창 크기(가로/세로)가 `builder_state.json`의 `"window"` 키에 저장되고, 앱 시작 시 이를 우선 사용
  (없으면 기존처럼 30cm×20cm 계산값 사용) — `canvas_window.get_saved_window_size()`
- 앱 폰트는 별도 설정 없이 Qt가 자동으로 Windows 시스템 폰트(맑은 고딕)를 그대로 사용 중이라
  손댈 필요 없었음
- 빌더 창(캔버스/팔레트)에 전역 QSS 테마 적용됨 (`theme.py`, `main.py`에서
  `app.setStyleSheet(APP_STYLESHEET)`) — 버튼/입력창/탭바/스크롤바 등 전체적으로 더 정돈된 모양
- URL/디렉토리 입력창 아이콘을 Windows 스타일에 맞게 통일(`SP_DirLinkIcon`/`SP_DirIcon`), 디렉토리
  선택 창은 native Windows 폴더 선택창을 쓰도록 변경(`DontUseNativeDialog` 제거)
- 탭바에서 현재 선택된 탭 제목만 볼드로 표시하도록 개선 (`ColorTabBar.paintEvent`)

## 지금 켜져 있는 앱 실행법

```powershell
cd C:\repository\ai-gui-builder-app
venv\Scripts\pythonw.exe main.py
```

(`python.exe`로 실행하면 "python.exe" 제목의 불필요한 콘솔 창이 캔버스/팔레트 창과 함께 하나 더
떠서, `pythonw.exe`로 바꿈 — 2026-08-15)

## 지원하는 위젯 (팔레트)

드롭박스, 누름 버튼, 텍스트 박스, 가로선, 세로선, URL 입력창(팝업으로도 입력 가능),
디렉토리 입력창(폴더 아이콘으로 선택), 라디오 버튼(그룹별 독립, 첫 옵션 기본 선택).

**알람 시계**와 **윈도우 현황**은 팔레트에 없음 — 각각 "alarm"/"윈도우 현황" 탭에 이미 고정
배치되어 있음 (사용자 요청으로 팔레트에서 뺌).

## 위젯 공통 기능

- 이동(드래그)/가장자리로 크기조절/러버밴드 다중선택/Delete 삭제/Ctrl+C·V 복사붙여넣기(탭 간 공유)
- 우클릭 메뉴: ID 표시, 동작 설정(자연어→코드), 색깔 변경, 이름 변경, 폰트 설정, 테두리 없애기,
  (라디오 버튼만) 옵션 추가/제거
- 탭: 이름 변경, 배경색, 우클릭으로 새 탭/삭제, 드래그로 순서 변경, 앱 종료 시 자동 저장 + "틀 저장"
  버튼으로 수동 저장

## 자연어 동작(화이트리스트 함수) 목록

`open_url`, `read_file`, `write_file`, `delete_file`, `list_dir`, `make_dir`, `move_file`,
`fetch_url`(429 자동 재시도 포함), `html_to_markdown`, `extract_images`, `download_file`,
`classify_image_with_claude`, 그리고 `QMessageBox`/`QInputDialog` 팝업. 전부 `code_binder.py`와
`exporter.py`(standalone용) 양쪽에 동일하게 구현되어 있음.

## 알람 시계 위젯 ("alarm" 탭)

일회성/주기적 알람 추가(달력+시간+커스텀 메시지), 등록된 알람 목록에 실시간 남은시간 + × 삭제 버튼,
위쪽 정렬된 달력 + 아날로그 시계, 알람 시간에 20cm×20cm 정사각형 팝업(현재 시각 + 24pt 굵은 글씨
메시지 표시). 구현은 `alarm_widget.py` (빌더/standalone 양쪽에서 같은 소스 파일을 그대로 사용).

**알람 목록 저장**: 아직 울리지 않은 알람은 추가/삭제/켜기끄기/발동 시점마다 `alarm_state.json`에
자동 저장되고 앱 재시작 시 복원됨 (이미 울린 일회성/끝난 주기적 알람은 저장에서 제외). 2026-08-12
구현 완료 — 아래 "알려진 미완/보류 항목"의 관련 항목은 해결됨.

## 윈도우 현황 위젯 ("윈도우 현황" 탭)

Windows 버전/CPU 모델 + CPU/메모리 사용률(3초마다 갱신, 막대그래프, 90% 이상이면 빨간색 경고) +
로컬 고정 디스크별 사용량(C/D/E는 없어도 항상 표시, "없음"으로) + 휴지통 현황(파일 개수/용량,
"목록"으로 상세 목록 확인, "휴지통 비우기"로 확인 후 비우기)을 보여주는 대시보드. 추가로 버튼
4개: **상위 프로세스**(CPU/메모리 Top5), **폴더 용량**(Temp/다운로드 폴더 크기), **시작 프로그램
목록**(레지스트리 Run키 + 시작프로그램 폴더), **시스템 변수 바로보기**(Windows 환경변수 편집창을
바로 띄움). `psutil` 같은 추가 패키지 없이 `ctypes`(+`winreg`/`subprocess`)로 Windows API를 직접
호출해서 구현했음 (`window_status_widget.py`, 빌더/standalone 양쪽에서 같은 소스 파일 그대로 사용).
Windows 전용 기능이라 다른 OS로 내보낸 앱에서는 동작하지 않음.

**구현 중 발견한 버그**: 휴지통 목록/시작 프로그램 목록 창에서 Stretch로 늘어나는 컬럼에 한글이
섞인 긴 문자열을 넣으면 `QTableWidgetItem` 기본 렌더러로는 "C:..."처럼 잘려 보이는 현상이 있었음
(데이터 자체는 정상 — `.text()`로는 전체 경로가 그대로 나옴, 순수 렌더링 버그). `QTableWidgetItem`
대신 그 셀에 `QLabel`을 `setCellWidget`으로 넣는 방식으로 우회함.

## git 위젯 ("git" 탭)

local/remote 저장소를 최대 6쌍까지 등록해두고(2열×3행) 각각 HEAD 커밋 비교("비교" 버튼,
`git ls-remote`만 써서 로컬 상태를 안 건드림) + 비교 결과를 초록/빨강으로 보여주는 "비교결과" 상태
버튼(클릭하면 마지막 결과 다시 봄) + 커밋 안 된 변경 파일의 원본/현재 버전을 백업하는 "stash" 버튼을
제공. "local drive 검색" 버튼을 누르면 C/D/E를 훑어서 찾은 git 저장소로 6개 local 칸을 (기존 값을
덮어써서) 채움(최대 6개, 백그라운드 스레드). "전체 status check" 버튼을 누르면 remote/local이 둘 다
입력된 상자를 전부 한 번에 비교(백그라운드 스레드) - 두 버튼은 서로 독립적임(검색은 local만 채우고
비교는 안 함, status check는 검색을 하지 않고 이미 채워진 것만 비교함). `git_widget.py`에 구현
(빌더/standalone 양쪽에서 같은 소스 파일 그대로 사용, 실행 환경에
`git` CLI 필요). 6쌍의 remote/local 입력값은 `git_panel_state.json`에 자동 저장됨. 2026-08-12 구현
완료 (드라이브 검색과 상태 비교 기능이 한 버튼에 합쳐졌다가, 최종적으로 "local drive 검색"/"전체
status check" 두 개의 독립된 버튼으로 정리됨).

## 브레인스토밍한 추가 아이디어 (미반영, 검토 대기)

"윈도우 현황" 탭 1차 구현 후 제안했던 목록 중 사용자가 고른 항목(경고 색상/상위 프로세스/폴더
용량/새로고침 주기/시작 프로그램/CPU 모델/정렬/C·D·E 항상 표시 + 요청받은 "시스템 변수 바로보기")은
전부 반영 완료. 아직 반영 안 한 나머지:

- 휴지통 개별 파일 **복원** 기능 (지금은 비우기만 가능, 목록에서 선택 복원 없음)
- CPU/메모리 **최근 추이 미니 그래프** (현재는 순간값만 표시)
- **네트워크 상태** (연결 여부, IP, 업/다운로드 속도)
- **배터리 상태** (노트북인 경우 잔량/충전 여부)
- **시스템 가동 시간(Uptime)** — 마지막 부팅 이후 경과 시간
- **화면 해상도/디스플레이 정보**

## 현재 탭 구성 (실사용 중인 내용)

- **git** — git 위젯 1개 (local/remote 비교·stash 6쌍 + 전체 status check)
- **wiki** — URL/디렉토리 입력창 + "가져와서 md로 변환" 버튼(웹 문서를 md로 저장, 이미지는 라디오
  버튼으로 자동/claude 분류 선택) + 라디오 버튼 2개
- **윈도우 현황** — 윈도우 현황 위젯 1개 (Windows 버전/CPU/메모리/디스크/휴지통)
- **alarm** — 알람 시계 위젯 1개
- **설명** — 버튼 4개: "전체 앱 설명"/"각 탭에 대한 설명"(둘 다 클릭 시점에 실제 탭 구성을 읽어서
  내용을 새로 만듦, `how_to_use.md` 6번 참고), "시작 프로그램 등록"/"시작 프로그램 삭제"(standalone
  파일을 Windows 로그인 시 자동 실행되도록 레지스트리 Run 키에 등록/제거). 2026-08-15 추가,
  "쉬었다 합시다" 탭을 대체함(노래/웹툰 버튼들은 제거)
- **link** — 3개 카테고리(claude/opencode/C++)로 나뉜 링크 모음. 각 카테고리는 색 있는 헤더
  입력창 + 버튼 여러 개(각 버튼이 `open_url`로 해당 사이트를 염), 카테고리 사이는 세로 구분선으로
  나뉨. C++ 카테고리 5개 링크(learncpp.com/cppreference.com/godbolt.org(Compiler Explorer)/
  cppinsights.io/isocpp.github.io)는 사용자가 직접 지정, claude(4개)/opencode(2개) 링크는 요청에
  따라 알아서 고름. 2026-08-15 추가

## 설명 탭 + 관련 화이트리스트 함수 추가 (2026-08-15)

"쉬었다 합시다" 탭을 지우고 "설명" 탭을 새로 만들면서, `code_binder.py`(빌더)와
`exporter.py`(standalone 내보내기) 양쪽에 화이트리스트 함수 6개를 동일하게 추가했다:
`show_text_dialog`/`app_overview_text`/`tab_usage_text`/`pick_startup_file`/`add_to_startup`/
`remove_from_startup` (자세한 시그니처는 `how_to_use.md` 6번/9번 참고, `ai_client.py`의
시스템 프롬프트에도 반영해서 앞으로 자연어로 동작을 생성할 때도 이 함수들을 쓸 수 있게 함).

- `app_overview_text`/`tab_usage_text`는 **버튼 클릭 시점에** `self.window().tabs`를 직접 읽어서
  탭 목록/각 탭의 위젯(직접 자식만, 라벨 텍스트 기준)을 그때그때 새로 조립한다 — 미리 캐싱된 텍스트가
  아니라서 탭을 추가/삭제하거나 위젯을 바꿔도 이 두 버튼을 다시 손볼 필요가 없다.
- `add_to_startup`/`remove_from_startup`은 `winreg`로 `HKCU\Software\Microsoft\Windows\
  CurrentVersion\Run`을 직접 조작한다 (등록 이름 = 파일명에서 확장자 제거한 값, 같은 파일 재등록 시
  덮어씀). `pick_startup_file`은 `standalone/` 디렉토리를 기본 위치로 하는 파일 선택 창.
- 헤드리스(`QT_QPA_PLATFORM=offscreen`) 스크립트로 다음을 모두 직접 검증함(스크래치 파일, 커밋 안 됨):
  `code_binder.compile_handler`로 4개 버튼 코드 컴파일, 실제 `builder_state.json` 복원 경로에서
  4개 핸들러 정상 바인딩, `exporter.generate_source`로 만든 소스가 `ast.parse`/`py_compile` 통과,
  레지스트리 등록/삭제 왕복(테스트용 이름 사용 후 정리함).

## 저장/내보내기 완전성 감사 (2026-08-15)

"틀 저장"(`palette_window.py`의 `_on_template_save_clicked` → `canvas_window.py`의 `save_template` →
`_save_state`, 54~95번 줄), "실행 py 저장"(`export_dialog` → `exporter.py`의 `export_to_file`),
"standalone 실행 파일 저장"(`export_exe_dialog` → `exporter.py`의 `build_exe`, 내부적으로 같은
`generate_source`를 씀) 세 버튼이 캔버스 구성/화면 크기를 빠짐없이 저장하는지 정적 코드 대조로
점검한 결과:

- **윈도우 크기**: 세 버튼 모두 `self.width()`/`self.height()`를 그 자리에서 읽어 넘김 — 틀 저장은
  `builder_state.json`의 `"window"`에, 실행 py/standalone exe 저장은 `generate_source`의
  `self.resize(width, height)`에 반영됨. 문제 없음.
- **탭별 제목/색깔/순서**: 세 버튼 모두 동일하게 `tabs_widget.tabText(i)` / `tab_bar.get_tab_color(i)`
  / `range(count)` 순서로 캡처. 문제 없음.
- **위젯별 kind/x/y/width/height/text/color/font_family/font_size/no_border**: 틀 저장은
  `_save_state`가 이 필드들을 직접 골라 담고, 실행 py/exe 저장은 `entries` 딕셔너리를 통째로 넘겨서
  `generate_source`가 `widget.pos()`/`widget.size()`/`widget.text()` 등 라이브 값을 그대로 읽음 —
  양쪽 다 빠진 필드 없음.
- **`instruction`(자연어 설명)**: 틀 저장(`builder_state.json`)에는 저장되지만 실행 py/exe 내보내기에는
  포함 안 됨 — 의도된 설계다. 내보낸 앱은 이미 생성된 `code`만 실행하면 되고, `instruction`은 빌더에서
  "동작 설정" 다이얼로그를 다시 열어 수정할 때만 필요한 편집용 메타데이터라 standalone 실행에는
  불필요함.
- **라디오 버튼 그룹 구성**: 그룹 멤버십(`entries[...]["group"]`)은 세 버튼 모두 정상 보존.
- **라디오 버튼의 현재 선택 상태(checked)**: 감사 당시엔 셋 다 저장 안 되고 항상 첫 옵션으로
  리셋됐음 — 2026-08-15에 수정 완료. `entries`를 만드는 `_create_widget`/`restore_widget`에
  `checked` 매개변수를 추가해 명시적으로 전달된 값이 있으면 그대로 반영하고(없을 때만 새 그룹의
  첫 멤버를 기본 선택), `_save_state`가 `entry["widget"].isChecked()`를 읽어
  `builder_state.json`에 함께 저장, `exporter.py`의 `generate_source`도 그룹별로 첫 멤버를 무조건
  체크하던 것을 그만두고 라이브 `widget.isChecked()`가 True인 멤버를 찾아 그걸 체크하도록 바꿈
  (없으면 첫 멤버로 폴백). 복사/붙여넣기(`_copy_selected_widgets`/`_paste_clipboard`)에도 동일하게
  `checked`를 실어 나르게 함. 헤드리스(`QT_QPA_PLATFORM=offscreen`) 스크립트로 저장→복원→내보내기
  세 경로 모두 직접 검증함 (스크래치 파일, 커밋 안 됨).
- **alarm/git 전용 합성 위젯의 런타임 상태**: `generate_source`가 `alarmclock` kind에서
  `_serialize_alarms(widget._alarms)`로 미발동 알람 목록을, `gitpanel` kind에서
  `[{"remote":..., "local":...} for box in widget.pair_boxes]`로 6쌍 값을 각각 내보내는 시점의
  라이브 상태 그대로 `initial_alarms`/`initial_pairs`에 심는다 — how_to_use.md 6-1 섹션 설명과 코드가
  정확히 일치함 (실행 py 저장/standalone exe 저장 둘 다, `generate_source`를 공유하므로 동일하게
  적용됨). 문제 없음.
- **틀 저장에 `alarm_state.json`/`git_panel_state.json`이 안 들어가는 것**: 버그 아님, 의도된 설계.
  두 파일은 각자 알람 추가/삭제/켜기끄기·git 6쌍 입력 시점마다 자기 자신의 로직으로 이미 자동
  저장되고 있어서 (how_to_use.md 3장/5장 참고) `builder_state.json`이 중복으로 떠안을 필요가 없음.

**결론**: 라디오 버튼의 현재 선택 상태 1건을 제외하면 세 저장 버튼 모두 캔버스 구성과 화면 크기를
빠짐없이 저장한다. 라디오 버튼 선택 상태 미보존은 코드 수정 없이 이번엔 기록만 해둔 상태 — 필요하면
`entries`에 `checked` 필드를 추가해 `_save_state`/`generate_source`/복원 로직 세 군데를 함께 고치는
후속 작업으로 진행할 수 있음.

## claude/git 서브프로세스 출력 한글 깨짐 수정 (2026-08-15)

자연어 알람 설정에서 메시지에 "꺄오" 같은 한글을 넣으면 글자가 깨져서 저장되는 버그를 발견해 수정함.
원인: `subprocess.run(..., text=True)` 호출에서 `encoding`을 지정하지 않으면 파이썬이
`locale.getpreferredencoding()`(이 머신에서는 `cp949`)로 stdout을 디코드하는데, `claude` CLI는
UTF-8로 출력하기 때문에 디코딩이 어긋나서 한글이 깨짐(예: "꺄오" → "爰꾩삤"). `encoding="utf-8",
errors="replace"`를 모든 `subprocess.run(text=True)` 호출에 추가해서 고침 — `alarm_widget.py`
(`_parse_alarm_with_claude`), `git_widget.py`(`_run_git`), `code_binder.py`/`exporter.py`
(`classify_image_with_claude`, 양쪽 동일), `ai_client.py`(`generate_handler_code`),
`exporter.py`의 PyInstaller 빌드 호출(`build_exe`)까지 전부 동일하게 적용함. 수정 전/후 동작을
UTF-8 문자열을 출력하는 자식 프로세스로 직접 재현해서 검증했고("꺄오" → "爰꾩삤" vs "꺄오" 그대로),
실제 `claude` CLI로 사용자가 보고한 문장("오늘부터 9월 1일까지 매일 "꺄오"...")을 그대로 호출해
`message` 필드가 `'꺄오'`로 정확히 나오는 것까지 확인함.

## 알람 목록 날짜 필터 + 모두 삭제 버튼 (2026-08-15)

`alarm_widget.py`의 알람 목록을 달력에서 선택한 날짜에 해당하는 알람만 보이도록 필터링했다
(`AlarmClockPanel._occurs_on_date`: 일회성은 날짜 정확히 일치, 주기적은 선택 날짜가 시작~끝
범위 안이면서 요일이 반복 요일에 포함될 때). 달력의 `selectionChanged`를 `_refresh_list`에 연결해
날짜를 바꾸면 즉시 갱신되고, 목록 제목에 `알람 목록 (YYYY-MM-DD)` 형식으로 현재 필터링 기준
날짜를 표시한다. **알람 발동/남은시간 계산 로직 자체는 날짜 필터와 무관하게 그대로 전체 알람을
대상으로 계속 돈다** — 화면에 안 보이는 날짜의 알람도 시간이 되면 정상적으로 울린다. 목록 제목
오른쪽에 확인 팝업이 있는 "알람 모두 삭제" 버튼도 추가함. 헤드리스 테스트로 오늘/내일 선택 시
표시되는 알람 개수가 정확히 필터링되는지, 모두 삭제가 확인 후 전체를 지우는지 직접 검증함.

## alarm/git 저장 데이터를 appData/ 하위로 이동 (2026-08-15)

`alarm_widget.py`/`git_widget.py`가 각각 저장하던 `alarm_state.json`/`git_panel_state.json`을
앱 폴더 바로 밑이 아니라 `appData/alarm_state.json`/`appData/git_panel_state.json`으로 옮겼다
(빌더든 standalone 내보내기든 자기 위치 기준 `appData/` 하위, 로직은 두 파일 모두 동일하게
`_STATE_DIR`에 `appData` 하나만 더 붙이는 식). 예전 방식(폴더 바로 밑)으로 이미 저장돼 있던
파일이 있으면 모듈이 처음 import될 때(앱 시작 시) 자동으로 `appData/` 안으로 옮기는 1회성
마이그레이션을 넣어서(`_migrate_legacy_alarm_state`/`_migrate_legacy_git_panel_state`) 기존
데이터가 사라지지 않게 했다. 실제로 이 저장소 루트에 있던 `alarm_state.json`(빈 배열)/
`git_panel_state.json`(6쌍 값)도 이 작업 중에 `appData/`로 정상 이전됨을 확인함.

## 탭 선택 밑줄 색 불일치 수정 (2026-08-15)

`tab_bar.py`(`ColorTabBar.paintEvent`)에 커스텀 배경색이 없는 탭(예: alarm/설명)은 네이티브 QSS
렌더링(`theme.py`의 `QTabBar::tab:selected { border-bottom: 2px solid #5b72e0; }`)을 타서 선택 시
파란 밑줄이 보이는데, 커스텀 색이 있는 탭(git/wiki/윈도우 현황/link)은 완전히 별도의 수동 페인팅
경로(`painter.fillPath`)를 타면서 이 밑줄을 전혀 그리지 않는 구조적 불일치가 있었다. 색 있는 탭
쪽 페인팅에도 선택된 탭이면 동일한 색(`#5b72e0`)/두께(2px)로 밑줄을 그리도록 고쳐서 색 유무와
무관하게 모든 탭이 선택 시 같은 밑줄을 보이게 함. `tab_bar.py`는 빌더/standalone 양쪽에서 같은
소스 파일을 그대로 쓰므로 한 번의 수정으로 양쪽 다 반영됨.

## 알려진 미완/보류 항목

- **Windows에서 `claude` CLI 호출**: `classify_image_with_claude`/`ai_client.py`가
  `subprocess.run(["claude", ...])`로 호출하는 부분이 Windows에 npm으로 깐 `claude`(.cmd 셸
  스크립트)를 `shell=True` 없이 잘 찾는지는 아직 실사용으로 직접 검증 안 됨 (나머지 Windows 이전
  자체는 완료, 위 "Windows 이전" 섹션 참고).
- **이미지 분류 로직**: `wiki` 탭의 "가져와서 md로 변환" 버튼 동작 코드에 이미 실제로 붙어 있음
  (`extract_images`/`download_file`/`classify_image_with_claude`/`move_file` 사용). 다만
  `classify_image_with_claude`는 이미지 개수만큼 `claude` CLI를 순차 호출하므로 이미지가 많은
  페이지에서는 느릴 수 있음 — 필요하면 배치 처리나 병렬화 고려 가능.
- **합성 위젯(알람 시계)의 이동/크기조절 한계**: 내부에 버튼/리스트가 꽉 차 있어서 위젯 내부를 클릭해
  드래그로 옮기기는 어려움 (러버밴드 선택 + 삭제/복사는 정상 동작). 필요하면 자식 위젯까지 이벤트를
  전달하는 방식으로 개선 가능.

## standalone 실행 파일(.exe) 내보내기 (2026-08-12)

팔레트에 "standalone 실행 파일 저장" 버튼 추가. 예전 "standalone 저장" 버튼은 "실행 py 저장"으로
이름만 바뀌었고 동작(.py 내보내기)은 그대로임. 새 버튼은 저장창(디폴트 파일명 `ai_tools.exe`)에서
위치/이름을 고르면 PyInstaller(`--onefile --windowed`)로 진짜 단일 실행 파일을 빌드해서 그 경로에
저장함 — 결과물은 파이썬/PySide6/빌더 없이도 그냥 실행 가능 (대신 파일 크기가 대략 50MB 안팎).
빌드는 1~2분 걸려서 `_ExeBuildWorker`(QThread)로 백그라운드 처리, 그동안 버튼이 "빌드 중..."으로
바뀌고 비활성화됨. `exporter.py`의 `build_exe()`가 핵심 로직 (임시 디렉토리에 `.py` 소스 생성 →
PyInstaller 서브프로세스 실행 → 결과 exe를 목적지로 복사). 빌더 자신의 `venv`에 `pyinstaller`가
새로 추가됨 (`requirements.txt`) — 이건 빌더 개발용 venv에만 필요하고, 내보낸 `.py`를 돌리는 쪽
venv 요구사항(PySide6+markdownify+beautifulsoup4)에는 영향 없음. 실제 빌드→복사→실행까지 전체
파이프라인 테스트 완료 (48.2MB exe 생성, 실행 후 창 뜨는 것까지 확인).

## 실행 py 내보내기 이력

기존 `standalone/` 디렉토리는 `executable_py/`로 이름이 바뀌었다 (2026-08-15). "실행 py 저장" 결과물이
`executable_py/` 밑에 날짜(+번호)별 폴더로 정리되어 있음: `2026_07_26`, `2026_08_09_#2`, `#3`, `#5`,
`#6`, `#7`, `#8`, `2026_08_12_#1`, `#2`, `#3`, `#5`, `#6`, `#7`. 앞으로도 이 규칙
(`executable_py/2026_MM_DD_#N/app.py`)을 따르면 됨. `standalone/`은 새로 빈 채로 만들어져
"standalone 실행 파일 저장"(.exe) 결과물을 위한 용도로 쓰인다. 두 저장 버튼 모두 저장 다이얼로그가
해당 디렉토리에서 기본으로 열리도록 코드에 연결되어 있음 (`canvas_window.py`의 `EXECUTABLE_PY_DIR`/
`STANDALONE_DIR`, `export_dialog`/`export_exe_dialog`, 2026-08-15).

## 파일 구성 요약

`main.py`(진입점) · `palette_window.py`(팔레트) · `canvas_window.py`(캔버스/탭/위젯 로직 대부분) ·
`behavior_dialog.py`(동작 설정 다이얼로그) · `ai_client.py`(claude CLI 호출, 코드 생성 프롬프트) ·
`code_binder.py`(화이트리스트 함수 + 안전한 exec) · `exporter.py`(standalone 내보내기) ·
`alarm_widget.py`(알람 시계) · `window_status_widget.py`(윈도우 현황) · `git_widget.py`(git) ·
`tab_bar.py`(탭바) · `theme.py`(빌더 전역 QSS) ·
`builder_state.json`(자동 저장되는 현재 작업 상태) · `md_files/`(문서) ·
`executable_py/`("실행 py 저장" 결과물) · `standalone/`(비어 있음, 다른 내보내기용으로 이름 비워둠).
