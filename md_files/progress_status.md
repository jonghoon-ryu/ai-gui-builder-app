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

## 윈도우 현황 세부 레이아웃 조정 + 폴더 용량 버튼 제거 (2026-08-15)

레이아웃 깨짐 수정에 이어 세부 조정 3가지를 더 반영함:
- **자원 사용률 막대 높이 축소**: CPU/메모리/디스크 막대(`QProgressBar`) 전부 `setFixedHeight(12)`로
  통일 (이전엔 스타일 기본값, 더 두꺼웠음).
- **디스크 막대를 CPU/메모리와 같은 그리드로 병합**: 원래 `info_grid`(CPU/메모리)와 `disk_grid`
  (디스크)가 별도 `QGridLayout`이라 각자 컬럼 폭 계산이 미세하게 달라서 막대 끝 위치가 어긋났음.
  디스크 행을 `info_grid`에 그대로 이어붙이는 방식으로 바꿔서(가운데에 "디스크" 제목 행을 3열
  병합으로 끼워넣음) 완전히 같은 컬럼을 공유하게 해 픽셀 단위로 정렬되도록 함.
  헤드리스로 `cpu_bar`/`disk_bar`의 x좌표·너비가 정확히 일치하는 것을 확인함.
- **"확인"/"휴지통, temp 파일 제거" 박스를 자원 사용률 밑에 절반씩 나란히 배치**: 원래 세로로
  쌓여 있던 것을 `QHBoxLayout`(stretch 1,1)으로 좌우 배치함. "확인" 박스는 버튼 4개짜리 한 줄
  대신 2x2 그리드로 바꾸고, "휴지통, temp 파일 제거" 박스의 각 줄(아이콘+라벨+버튼 2개)도
  아이콘+라벨 줄/버튼 줄 2줄로 나눠서 절반 너비 안에 자연스럽게 들어가게 함 (한 줄로 두면 필요
  너비가 두 배 가까이 벌어져서 정확히 반씩 안 나뉘었음 — 헤드리스로 각 박스의
  `minimumSizeHint`를 재보면서 312px vs 576px → 312px vs 342px로 줄인 뒤, 실제 렌더링에서
  364px/364px로 정확히 50/50 분할되는 것까지 확인함).

**"폴더 용량" 버튼 제거**: 사용자 요청으로 "확인" 박스에서 삭제. 더 이상 아무 데서도 안 쓰는
`get_folder_sizes()`/`_show_folder_sizes()`도 같이 지웠고(죽은 코드 방치 안 함), `code_binder.py`/
`exporter.py`의 "설명" 탭용 `_PANEL_DESCRIPTIONS["windowstatus"]` 설명 문구에서도 "폴더 용량"
언급을 빼고 temp 파일 관련 문구로 갱신함 (안 지웠으면 exporter가 만드는 standalone 소스에
존재하지 않는 기능을 언급하는 문구가 남을 뻔함 - 실제로 내보내기 테스트 중 `assert '폴더 용량'
not in src`가 처음엔 실패해서 발견하고 고침).

## 확인↔휴지통,temp 가로 간격을 자원사용률↔확인 세로 간격과 맞춤 (2026-08-15)

"확인" 박스와 "휴지통, temp 파일 제거" 박스 사이 가로 간격(`bottom_row.setSpacing`, 기존 8px)을
바로 위 "자원 사용률"↔"확인" 세로 간격(현재 캔버스 크기 기준 약 36px)과 같게 맞춰달라는 요청으로
`bottom_row.setSpacing(36)`으로 변경함. 이 변경만으로는 가로 폭 예산이 부족해져서(전체 필요 폭이
패널 폭 800px을 12px 넘어서 "휴지통, temp 파일 제거" 박스 오른쪽이 실제로 잘리는 문제가 헤드리스
측정에서 드러남 — `cleanup_group`이 자기 최소 폭까지 줄어들어도 모자랐음) `check_layout`/
`cleanup_layout`의 좌우 여백(10→6)과 `cleanup_layout`의 칸 사이 가로 간격(8→6)을 같이 줄여서 그
만큼의 폭을 다시 확보함. 헤드리스로 최종 가로 간격(37px)이 세로 간격(36px)과 사실상 같고,
"휴지통, temp 파일 제거" 박스가 자기 최소 폭보다 10px 여유 있게(더 이상 잘리지 않고) 들어가는
것까지 확인함.

## 윈도우 현황 세부 마감 (temp 제목 제거 / 버튼 열 정렬 / 줄 간격) (2026-08-15)

이어진 세부 다듬기 3건:
- **"temp 파일" 부제 라벨 제거**: `cleanup_layout`에서 `temp_title` `QLabel`을 완전히 삭제함 (temp
  줄 자체의 `self.temp_label`이 "temp 파일: ..."로 이미 내용을 설명하고 있어 중복이었음).
- **휴지통/temp 두 줄의 "목록"·비우기 버튼 열 정렬**: 두 줄을 별도 `QHBoxLayout`으로 두면 "휴지통:
  ..."과 "temp 파일: ..." 라벨 길이가 달라서 그 뒤에 오는 버튼들의 x 위치가 어긋났음. `bin_row`/
  `temp_row`를 없애고 `cleanup_layout` 자체를 `QGridLayout`(0=아이콘, 1=라벨-stretch, 2=목록,
  3=비우기)으로 바꿔서 CPU/디스크 막대 정렬 때와 같은 방식으로 해결 — 헤드리스로 두 "목록" 버튼과
  두 "비우기" 버튼이 각각 정확히 같은 x(357, 445)에 오는 것을 확인함.
- **줄 간격 확대**: "시스템 정보" 박스 안 두 줄(Windows 버전/CPU 모델) 간격을 `sys_layout.
  setSpacing(2→6)`으로, "자원 사용률" 박스 안 각 줄(CPU/메모리/디스크) 간격을 `info_grid.
  setVerticalSpacing(4→10)`으로 넓힘. "시스템 정보"~"자원 사용률" 간격과 "자원 사용률"~"확인" 간격은
  기존처럼 `outer.addStretch(1)` 두 곳이 동일 가중치로 나머지 공간을 나눠 가지므로, 줄 간격이
  늘어나 그룹 높이가 커진 뒤에도 두 간격은 계속 서로 같게 유지됨(재측정: 37px vs 36px, 반올림
  오차) — 그룹 내부 spacing과 그룹 사이 spacing이 서로 다른 메커니즘(고정 spacing vs 동일 가중치
  stretch)이라 한쪽을 조정해도 다른 쪽의 "같음" 속성이 깨지지 않음.

## 윈도우 현황 하단 배치 재조정: 절반 분할 → 콘텐츠 기준 분할 (2026-08-15)

바로 전에 "확인"/"휴지통,temp" 박스를 정확히 50/50으로 나눴던 것을, "휴지통/temp 각 줄의
목록·비우기 버튼을 라벨 오른쪽 한 줄로 되돌려달라"는 요청으로 다시 조정함:
- `bin_row`/`temp_row`를 (아이콘+라벨 줄, 버튼 줄) 2줄 구성에서 원래의 한 줄(아이콘+라벨+버튼
  2개) 구성으로 되돌림 — 그 결과 `cleanup_group`의 최소 필요 폭이 다시 커짐(약 576px).
- 대신 폭 분할 방식을 "50/50 stretch"에서 "확인 박스는 stretch 없이 자기 콘텐츠 최소 폭만,
  나머지는 전부 휴지통·temp 박스"로 바꿈 (`bottom_row.addWidget(check_group)`,
  `bottom_row.addWidget(cleanup_group, 1)`). "확인" 박스의 버튼 3개가 세로로 쌓여 있어서
  최소 폭이 172px밖에 안 되므로, 자연히 "확인은 좁게, 휴지통·temp는 넓게" 요청과 맞아떨어짐.
- 그래도 폭이 모자라서(필요 폭 합 780px대인데 패널은 760px) `windowstatus_1` 캔버스 크기를
  `x=30,width=760` → `x=10,width=800`으로 넓힘 (git 탭의 `gitpanel_1`과 동일하게 우측 끝이
  810에 오도록 맞춤 — 그쪽은 이미 문제 없이 표시되고 있어서 안전한 폭 기준으로 씀).
- **"시스템 정보"~"자원 사용률" 간격을 "자원 사용률"~"확인" 간격과 같게**: 두 구간 다
  `outer.addStretch(1)`(동일 가중치)로 바꿔서, 패널에 남는 세로 여백이 두 구간에 균등하게
  나뉘도록 함 — 헤드리스로 재보면 54px vs 53px(반올림 오차)로 사실상 동일함을 확인.
- 헤드리스로 최종 레이아웃 전부 재검증: 두 간격 동일, 확인 박스 3버튼 세로 배치 유지, 휴지통/temp
  버튼들이 각 라벨 오른쪽 한 줄에 위치, 패널이 탭 콘텐츠 영역(약 480px)과 패널 자체 필요 크기
  (`sizeHint` 772×347) 양쪽 다 여유 있게 들어가는 것까지 확인.

## 윈도우 현황 하단 배치 세부 조정 (2026-08-15)

"확인"/"휴지통, temp 파일 제거" 박스를 자원 사용률 박스에서 좀 더 아래로 떨어뜨리고, 여백을
정리해달라는 요청 반영:
- `outer`(패널 전체 레이아웃)의 좌/우/아래 여백을 모두 8px로 통일(이전엔 좌우 12px, 아래 8px로
  달랐음) — "확인 박스의 왼쪽 여백"="휴지통,temp 박스의 오른쪽 여백"="둘의 아래쪽 여백"이 되도록.
- `resource_group`과 `bottom_row`(확인/휴지통,temp가 든 가로 배치) 사이에 `outer.addStretch(1)`을
  넣고, 대신 맨 끝에 있던 트레일링 stretch는 제거함 — 패널에 남는 세로 공간이 이제 중간(자원
  사용률 밑)으로 흡수되면서 두 박스가 패널 아래쪽으로 밀려 내려가고, 바닥 여백은 outer의
  contentsMargins(8px)로 고정됨. 헤드리스로 좌/우/아래 여백이 8~9px(반올림 오차) 안에서 실제로
  일치하는 것을 확인함.
- "확인" 박스는 `QGridLayout`(2x2) 대신 `QVBoxLayout`으로 바꿔 버튼 3개(상위 프로세스/시작
  프로그램 목록/시스템 변수 바로보기)를 세로로 한 줄씩 나열하고, 전부 `setFixedHeight(28)`로
  높이를 통일함(너비는 그룹 폭에 맞춰 자동으로 동일해짐) — 헤드리스로 세 버튼의 geometry가 모두
  342×28로 동일한 것을 확인함.

## 알람 탭 버튼 실동작 검증 (2026-08-15)

"버튼 클릭해서 실제로 잘 되는지 확인해봐" 요청으로 헤드리스에서 실제 `QPushButton.click()`을
호출해 전체 플로우를 검증함(단순히 코드가 연결돼 있는지가 아니라 실제로 눌렀을 때 상태가 맞게
바뀌는지). 날짜/시간 선택 다이얼로그(`_DatePickerDialog`/`_TimePickerDialog`/
`_RecurringRangeDialog`)는 `.exec()`를 패치해서 팝업 없이 기본값으로 자동 수락되게 함.

**검증 중 발견한 버그성 함정(테스트 스크립트 쪽 문제, 실제 앱 버그는 아님)**: 일회성 알람의
시간 선택 다이얼로그 기본값이 "현재 시각"이라, 테스트에서 그대로 두면 알람을 추가하자마자
`_refresh_list()`가 즉시 발동 조건을 만족해 `_fire_alarm()`이 진짜 `_AlarmPopup`(`QDialog.exec()`)을
띄우면서 헤드리스 환경에서 영원히 멈춰버림(사용자 입력을 받을 수 없으니 아무도 안 닫아줌). 이
자체는 "지금 시각으로 알람을 잡으면 바로 울린다"는 올바른 동작이라 앱 버그는 아니지만, 테스트에서는
`_AlarmPopup.exec`도 함께 패치하고 일회성 알람 시간은 오늘 23:59처럼 미래 시각으로 지정해서 우회함.

**검증 결과 (21개 항목 전부 통과)**:
- 일회성 알람 추가 → 알람 생성/저장 호출/목록 표시(오늘 날짜 필터) 정상
- 주기적 알람 추가 → 알람 생성/목록 표시 정상
- 목록의 "끄기/켜기" 버튼 → `enabled` 상태 정확히 반전
- 목록의 "×" 삭제 버튼 → 해당 알람만 정확히 삭제
- "알람 모두 삭제" 버튼(확인 팝업 Yes) → 전체 삭제
- "자연어로 알람 설정" 버튼 → 실제 `claude` CLI를 호출하는 백그라운드 스레드까지 끝까지 기다려서
  검증("내일 오전 9시에 팀 회의 알람 설정해줘" → `type=once`, 날짜=내일, `message='팀 회의'`로
  정확히 파싱되어 등록됨, 입력창/상태 라벨도 정상 초기화됨)

## 윈도우 현황 창 레이아웃 깨짐 수정 (2026-08-15)

QGroupBox 4개로 재구성한 뒤 "창이 깨져 보인다"는 피드백으로 확인해보니, 그룹박스 4개(각각 테두리+
제목 여백) + 새로 추가된 temp 파일 줄까지 더해져서 패널이 실제로 필요로 하는 세로 크기
(`sizeHint` 기준 458px)가 캔버스에 할당된 높이(400px)보다 커서 내부 콘텐츠 일부가 잘려나가고
있었음 — 알람 탭에서 겪었던 것과 같은 종류의 버그(이번엔 "위젯이 자기 콘텐츠보다 작음" 방향).
`theme.py`의 `QGroupBox` 여백(margin-top 10→8, padding-top 12→6)과 각 그룹의 내부 레이아웃
margin/spacing을 줄여서 필요 높이를 458→420으로 줄이고, `builder_state.json`의 `windowstatus_1`을
y=52/height=400 → y=20/height=440으로 조정해 실제 필요 크기(420)보다 넉넉하게 잡음. 헤드리스로
`sizeHint`와 실제 탭 콘텐츠 영역(480) 대비 위젯 위치를 재확인해서 내부 클리핑도, 탭 경계 클리핑도
없는 것을 확인함(탭 경계까지 여유 21px).

## 윈도우 현황 탭 그룹박스 4개로 재구성 + temp 파일 관리 추가 (2026-08-15)

`window_status_widget.py`의 `WindowStatusPanel` 레이아웃을 제목 있는 테두리 박스(`QGroupBox`) 4개로
재구성했다: **시스템 정보**(Windows 버전/CPU 모델) / **자원 사용률**(CPU/메모리/디스크) / **확인**
(상위 프로세스/폴더 용량/시작 프로그램 목록/시스템 변수 바로보기 버튼 4개) / **휴지통, temp 파일
제거**(휴지통 줄 + 그 밑에 같은 포맷의 temp 파일 줄). `theme.py`에 `QGroupBox` QSS를 새로 추가해서
다른 컨트롤들과 톤이 맞는 테두리/제목 스타일을 줌(빌더/standalone 양쪽에 자동 반영, 파일 공유
방식이라).

**temp 파일 관리(신규 기능)**: 휴지통과 동일한 포맷(아이콘 + "N개 파일, 용량" 라벨 + 목록/비우기
버튼 2개)으로 `%TEMP%` 폴더를 관리할 수 있게 됨. `get_temp_folder_summary`/`list_temp_files`는
`get_folder_sizes`와 같은 방식(재귀적 `os.walk`)으로 temp 폴더를 스캔하고, `empty_temp_folder`는
최상위 파일/폴더를 삭제 시도하되 사용 중이라 실패하는 항목은 `OSError`를 잡아 건너뛰고 개수를
세서 돌려준다(휴지통과 달리 temp 폴더는 Windows/실행 중인 프로그램이 파일을 잠그고 있는 경우가
흔해서 일부 실패를 정상 케이스로 취급). 건너뛴 게 있으면만 "N개 삭제, M개는 사용 중이라 건너뜀"
안내 팝업이 뜸. temp 요약은 디스크/CPU처럼 8초 주기에 끼워 넣지 않고 탭 진입(construct/showEvent)
시점에만 계산함 — 파일시스템 walk라 recycle bin 조회(네이티브 API)보다 느려서 8초마다 반복하기엔
부담스러움. 실제 이 컴퓨터의 temp 폴더(5867개 파일, 5.2GB)로 목록/개수 일치를 직접 확인함.

## 윈도우 현황 갱신 주기 3초→8초 + 탭 선택 시에만 갱신 (2026-08-15)

`window_status_widget.py`의 `WindowStatusPanel.REFRESH_INTERVAL_MS`를 3000에서 8000으로 늘리고,
`__init__`에서 곧바로 타이머를 돌리던 것을 그만두고 `showEvent`/`hideEvent`에서 타이머를
시작/정지하도록 바꿨다 — "윈도우 현황" 탭이 실제로 선택되어 화면에 보이는 동안에만 CPU/메모리/
디스크를 갱신하고, 다른 탭을 보는 동안은 완전히 멈춘다(탭으로 돌아오면 즉시 한 번 새로고침 후 다시
8초 주기 시작). QTabWidget이 선택 안 된 탭의 페이지를 hide()하는 것을 그대로 활용한 것이라 별도로
현재 탭을 추적하는 코드가 필요 없었다. 헤드리스 테스트로 탭 전환에 따라 `_timer.isActive()`가
정확히 True/False로 바뀌는 것을 직접 확인함.

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
(2026-08-15 추가 수정: 알람 목록과 패널 하단 사이 여백이 사실상 없어 보이던 진짜 원인은 outer
레이아웃 margin이 아니라, `alarmclock_1` 위젯 자체(세로 476px)가 실제 탭 콘텐츠 영역(헤드리스
측정 기준 세로 약 480px)보다 커서 하단이 화면 밖으로 잘려나가고 있었던 것 — margin을 아무리
늘려도 잘린 영역 안에 있어 안 보였음. `builder_state.json`의 `alarmclock_1` 높이를 476→420으로
줄이고, `alarm_widget.py`의 outer 레이아웃 margin을 좌우와 동일한 `(12, 10, 12, 12)`로 맞춰서
해결. 헤드리스로 실제 `CanvasWindow`를 띄워 탭 콘텐츠 영역 크기와 위젯 하단 위치를 직접 측정해서
더 이상 밖으로 안 나가는 것을 확인함(수정 전 gap -17 → 수정 후 gap +39).

추가로 그 +39 gap과 list 크기가 여전히 커 보인다는 피드백을 받아 한 번 더 조정함: `list_widget`을
`setMaximumHeight`(가변) 대신 `setFixedHeight(90)`으로 바꿔 항상 고정된 짧은 높이를 갖게 하고,
`alarmclock_1` 높이를 420→440으로 다시 올림 — 반직관적이지만, list가 이제 고정 크기라 패널이
커져도 list가 아니라 상단(달력/버튼) 쪽 여유 공간만 늘어나고 list 바로 아래 간격은 outer 레이아웃
margin(12)에 그대로 고정된다는 걸 헤드리스로 패널 높이를 여러 값(340~476)으로 스윕하며 확인한 뒤
결정함. 결과: 캔버스 레벨 gap 39→19, list-패널 내부 gap은 그대로 12(=좌우 margin과 동일), list
자체 높이는 항상 90으로 고정(이전엔 패널 높이에 따라 84~160 사이에서 자동으로 늘어났었음).

또 한 번 더 조정함: "목록이 너무 아래에 있다, 다른 아이템 크기는 그대로 두고 목록만 위로 올리고
키워달라"는 요청으로 진짜 원인을 찾아보니 `buttons_col`(왼쪽 버튼 컬럼)에 걸려 있던
`addStretch()`가 패널이 커질 때마다 상단(버튼/달력/시계) 영역 전체를 계속 늘려서 목록을 아래로
밀어내고 있었음(달력/시계는 `Qt.AlignTop`이라 실제 크기는 안 바뀌지만, 컨테이너인 `top_row`
자체의 높이 요구량이 커짐). 이 `addStretch()`를 제거하고, `list_widget`을 `setFixedHeight(90)`
대신 `setMinimumHeight(90)`(바닥값만 있고 위로는 확장 가능)으로 바꿔서, 패널의 남는 세로 공간이
더 이상 상단 영역이 아니라 목록 쪽으로 가도록 함. 헤드리스로 패널 높이를 스윕하며 목록의 y 좌표가
항상 304(고정, 버튼/달력/시계 영역의 실제 최소 높이)로 안정되고 높이는 남는 공간만큼(예: 패널
440일 때 124) 자라는 것을 확인했고, 실제 `builder_state.json`을 복원한 캔버스에서도 동일하게
동작하는 것까지 검증함. 버튼/달력/시계/자연어 입력칸 등 다른 아이템은 크기·코드 변경 없음
(단순히 그 옆의 빈 스트레치 공간을 없앤 것뿐).

한 번 더: "일회성/주기적/자연어/모두 삭제" 버튼 4개의 세로 길이를 늘리고(36→44), "일회성"↔"주기적"
사이·"주기적"↔자연어 입력칸 사이 간격을 줄여달라는 요청(20→12)도 반영함. 버튼이 커진 만큼 버튼
영역의 최소 높이(위에서 알아낸 "floor")가 304→336으로 올라가서, 캔버스 높이(440)를 그대로 두면
list 자체 높이는 124→92로 줄어든다 — 물리적으로 쓸 수 있는 세로 공간이 늘어난 게 아니라 버튼이
차지하는 몫이 커진 만큼 list 몫이 줄어드는 트레이드오프라 그대로 반영함 (list는 여전히 최소
90(`setMinimumHeight`) 이상 유지, 클리핑 없음 - 헤드리스로 재확인함).

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
