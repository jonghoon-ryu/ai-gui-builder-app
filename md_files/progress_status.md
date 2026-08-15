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

- **gvf** — gvf 위젯 3개 (2026-08-15 추가, 레이아웃만 있는 뼈대 상태). 왼쪽 위 "FPGA 자원 현황"
  그룹박스(`GvfPanel`) — 표시창 3개("FPGA #1/2/3", 너비 좁힘) + 각각 옆에 3자리 숫자 입력칸 + 옆에
  테두리 없고 여백을 꽉 채운, 가로로 넓힌 시작/종료 시간 디지털 시계 자리 + 줄 맨 오른쪽에 1.5배
  키운 "반납" 버튼. 오른쪽 위 "FPGA 자원 취득" 그룹박스(`FpgaAcquisitionPanel`, `GvfPanel`과 크기를
  맞춤) — "아이디" 문자열 입력, "FPGA 획득 마지막 시도" 시간 입력(`QTimeEdit`), "FPGA 취득 간격"
  분 단위 스핀박스(기본 120분), "max FPGA 취득" 스핀박스(기본 1, 최솟값 1), "명령어 입력 디렉토리"
  경로 입력(git local과 동일한 폴더 선택 방식), "FPGA 대기열 삭제" 버튼, 맨 아래 시작/중지 버튼
  한 쌍(시작을 누르면 "동작중", 이어서 중지를 누르면 "다시 시작"으로 시작 버튼 이름이 바뀜). 아래쪽
  "FPGA loading" 그룹박스(`FpgaLoadingPanel`) — 라디오 버튼 열 3개를 세로로 쌓아서 넉넉한 간격으로
  가로 나열(FPGA 버전 4개/FPGA 번호 3개("FPGA #1/2/3", 각각 옆에 3자리 숫자 입력칸이 하나씩 붙음)/
  메모리 타입 4개) + 맨 오른쪽에 1.5배 키운 "시작" 버튼. **세 위젯 모두** 입력값이 바뀔 때마다
  `appData/gvf_state.json`에 자동 저장되고(각자 다른 키를 써서 서로의 데이터를 안 덮어씀) 재시작 시
  복원됨. 실제 데이터/시간 연결, 주기적 자동 획득, 명령어 실행, 시작/중지/대기열 삭제/loading "시작"
  로직은 모두 다음에 이어서 함 (지금은 값 입력/저장/버튼 이름 토글만 동작)
- **git** — git 위젯 1개 (local/remote 비교·stash 6쌍 + 전체 status check)
- **wiki** — URL/디렉토리 입력창 + "가져와서 md로 변환" 버튼(웹 문서를 md로 저장, 이미지는 라디오
  버튼으로 자동/claude 분류 선택) + 라디오 버튼 2개
- **윈도우 현황** — 윈도우 현황 위젯 1개 (Windows 버전/CPU/메모리/디스크/휴지통)
- **alarm** — 알람 시계 위젯 1개
- **설명** — 버튼 4개: "전체 앱 설명"/"각 탭에 대한 설명"(둘 다 클릭 시점에 실제 탭 구성을 읽어서
  내용을 새로 만듦, `how_to_use.md` 7번 참고), "시작 프로그램 등록"/"시작 프로그램 삭제"(standalone
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

## 팝업/다이얼로그가 탭·위젯 색을 상속하던 버그 수정 (2026-08-15)

"각 탭에서 창을 열면(예: 설명 탭의 '전체 앱 설명') 이전에 있던 바탕색이 그대로 뜬다"는 리포트로
근본 원인을 찾음: 색이 지정된 탭 페이지/위젯에 `setStyleSheet(f"background-color: {color};")`처럼
**바로 값(선택자 없는) 스타일시트**를 주면, Qt는 이를 `* {{ background-color: X }}`로 취급해서
그 위젯의 모든 자손에 상속시킴 — 자손이 실제로는 별도 top-level 창(QDialog/QMessageBox 등)이어도
Qt의 스타일시트 상속은 "같은 OS 창인가"가 아니라 **위젯 부모-자식 관계**를 따라가기 때문에 그대로
전파됨. 헤드리스로 실제 재현(색 있는 페이지 위에서 `show_text_dialog`를 띄우면 다이얼로그 배경이
탭 색 그대로 나옴)하고, 여러 해결책을 직접 실험/비교해서 최종안을 정함:
- app 전역 스타일시트에 `QDialog {{ ... }}` 규칙을 추가하는 방법 → 실패 (조상의 스타일시트가
  앱 전역 스타일시트보다 우선순위가 높아서 안 먹힘)
- 부모 위젯 스타일시트를 타입 선택자로 스코프(`QPushButton {{ background-color: X }}`) → 위젯
  자신과 다이얼로그 배경은 고쳐지지만, 그 다이얼로그 **내부에 같은 타입의 위젯**(예: 색 있는
  버튼에서 연 팝업 안의 "확인" 버튼)까지 색이 새는 부작용 발견 → 기각
- **id 선택자로 스코프**(`#objectName {{ background-color: X }}`, 위젯마다 고유
  objectName 부여) → 자기 자신의 배경은 정확히 칠해지고, 다이얼로그/QMessageBox 등 자손에는
  전혀 상속되지 않으며, 같은 타입의 내부 위젯도 영향 없음 — 채택.

`canvas_window.py`에 `_apply_scoped_background(widget, color_hex)` 헬퍼를 만들어 위젯 색 지정
(`_create_widget`, "색깔 변경" 메뉴)과 탭 바탕색 지정(`_restore_from_state`, "바탕색" 메뉴) 4곳
전부 이걸로 통일함. `exporter.py`도 같은 방식(각 위젯/페이지에 `setObjectName` 후 id 선택자
스타일시트)으로 미러링해서 standalone 내보내기도 동일하게 고쳐짐. `code_binder.py`/`exporter.py`의
`show_text_dialog` 자체는 건드릴 필요 없었음(원인이 다이얼로그 쪽이 아니라 색을 주는 쪽이었으므로
소스 쪽만 고치면 모든 다이얼로그·QMessageBox·QInputDialog가 한 번에 해결됨 — 처음에는 개별
다이얼로그마다 배경을 강제 지정하는 방식으로 13곳을 고쳤다가, 이 근본 원인을 찾은 뒤 전부
되돌리고(git checkout) 이 방식으로 교체함, `QMessageBox`/`QInputDialog`는애초에 static
메서드라 개별 패치가 불가능했던 것도 이 방식을 택한 이유). 헤드리스로 실제 `builder_state.json`의
wiki 탭(#f9f06b) 위 실제 버튼(#aaaaff)에 물린 `QMessageBox`가 정확히 기본 배경(#f4f5f8)으로
뜨는 것까지 확인함.

## git 위젯: local drive 검색도 예/아니오 확인 + 기존 정보 초기화 (2026-08-15)

"local drive 검색" 버튼의 안내창이 `QMessageBox.information`(확인 버튼 하나)이라 사실상 그냥
넘기는 용도였는데, **아니오**로 취소할 수 있게 해달라는 요청으로 `QMessageBox.question`(예/아니오,
기본값 예)으로 바꿈 — 아니오를 누르면 검색 자체가 시작되지 않음. 안내 문구에도 "기존 정보는 모두
지워집니다."를 추가하고, 실제로 그렇게 동작하도록 `_on_scan_succeeded`를 고침: 예전엔 새로 찾은
저장소 개수(`repos`)만큼만 `zip(self.pair_boxes, repos)`로 덮어썼기 때문에, 이전 검색보다 적게
찾으면 남는 상자에 옛날 값이 그대로 남아있는 버그가 있었음(예: 이전에 6개를 찾아 채웠다가 이번엔
2개만 찾으면 3~6번 상자는 예전 2차 결과가 계속 남음). 이제 검색이 성공하면 **6개 상자 전부를
먼저 지운 뒤** 새로 찾은 만큼만 채우도록 해서, 못 찾은 나머지는 항상 빈 칸으로 남게 함. 헤드리스로
예/아니오 각 분기와, "6개 중 2개만 찾은" 시나리오에서 3~6번 상자가 옛 값 대신 빈 문자열이 되는
것까지 확인함.

## git 위젯: 주요 버튼 강조색 + status check 확인 다이얼로그 (2026-08-15)

- **버튼 강조**: "local drive 검색"/"전체 status check" 두 버튼이 다른 흰색 버튼들과 똑같아서
  눈에 안 띈다는 피드백으로, 진한 파란색(`#5b72e0`, 배경) + 흰 글씨 + 굵게 스타일(`_PRIMARY_BUTTON_STYLE`
  상수)을 만들어 이 둘에만 적용함. hover/pressed/disabled 상태도 각각 더 어둡게/연하게 정의해서
  disabled(스캔·확인 중) 상태에서도 다른 버튼과 구분됨. 헤드리스로 두 버튼 다 배경이 정확히
  `#5b72e0`로 렌더링되는 것을 픽셀 단위로 확인함.
- **"전체 status check" 확인 다이얼로그**: 기존엔 버튼을 누르면(입력된 쌍이 있을 때) 곧바로
  비교가 시작됐는데, "local repo와 remote repo와의 차이를 확인합니다." 확인창을 먼저 띄우고
  **예**를 눌러야 실제로 시작하도록 바꿈(**아니오**면 아무 일도 안 일어남). "입력된 상자가 없음"
  안내 팝업 체크는 그대로 먼저 하고, 그 다음에만 이 확인창이 뜸. 헤드리스로 예/아니오 각각의
  분기(워커 시작 여부, 버튼 활성/비활성 상태)를 직접 확인함.

## git 위젯: local drive 검색 깊이 제한 + 안내 팝업, 상자 배경 투명화 (2026-08-15)

**local drive 검색 깊이 제한**: `find_git_repos`가 기존엔 C/D/E 드라이브 전체를 무제한으로
`os.walk`하던 것을, 드라이브 루트 기준 3단계 하위 폴더까지만(`DRIVE_SEARCH_MAX_DEPTH = 3`) 훑도록
바꿈 — `os.walk`의 `topdown=True` 콜백에서 현재 `dirpath`의 깊이가 `max_depth` 이상이면
`dirnames[:] = []`로 더 이상 못 내려가게 가지치기함(깊이 계산은 `dirpath`/`root` 각각의
`os.sep` 개수 차이). 깊이 3인 디렉토리 자체는 여전히 검사 대상이라("3단계까지는" 포함), 4단계
이상만 제외됨. 버튼을 누르면 검색을 시작하기 전에 "각 드라이브의 최상위 폴더 기준 3단계 하위
폴더까지만 검색합니다" 안내 팝업이 먼저 뜸. 합성 디렉토리 트리(깊이 1~4에 각각 `.git` 배치)로
헤드리스 테스트해서 깊이 1~3은 찾고 깊이 4는 제외되는 것을 직접 확인함.

**GitPanel/상자 배경 투명화**: 앱 전역 스타일시트(`theme.py`)가 모든 `QWidget`에 회색(`#f4f5f8`)
배경을 강제로 입히기 때문에, git 탭 배경색을 바꿔도(`#ddebe2` 등) `GitPanel`과 그 안의 6개
`_RepoPairBox` 상자는 계속 회색으로 보이고 있었음. 두 클래스 모두 `WA_StyledBackground` +
`background-color: transparent`를 인스턴스 스타일시트로 줘서 탭의 실제 배경색이 그대로 비쳐
보이게 함 (하드코딩된 색 값 대신 투명 처리라서 탭 배경색을 나중에 또 바꿔도 자동으로 따라감).
`_RepoPairBox`는 스타일시트를 하나라도 주면 `setFrameShape`의 네이티브 테두리가 무시되는 Qt
특성 때문에 테두리(`#ced2db`, 다른 컨트롤들과 같은 색)도 같은 스타일시트에 명시적으로 같이 줌.
헤드리스로 페이지를 렌더링해서 상자 내부/빈 공간 픽셀이 둘 다 탭 배경색과 정확히 일치하고,
테두리 픽셀은 여전히 `#ced2db`로 구분되는 것을 확인함.

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

## git 위젯: git clone 버튼 추가 (2026-08-15)

"stash" 버튼 오른쪽에 **git clone** 버튼을 추가. 누르면 그 상자의 local 폴더를 통째로 비우고
remote를 새로 clone한다: `git ls-remote`로 remote 주소를 먼저 검증(실패 시 에러만 띄우고 아무것도
안 건드림) → local이 없으면 바로 clone, 있고 dirty하면 "저장할까요?" 확인 후 (예 선택 시 stash와
같은 방식으로 `.orig`/`.current` 백업) 진행, clean하면 "전부 삭제하고 clone합니다" 확인 → local
폴더를 비우고 새로 clone. 구현 중 겪은 문제와 해결:

- **파일이 잠겨서 삭제 안 되는 경우** — Restart Manager API(`rstrtmgr.dll`, ctypes로
  `RmStartSession`/`RmRegisterResources`/`RmGetList`/`RmEndSession` 호출)로 그 파일을 잡고 있는
  프로세스(PID/이름)를 찾아서 "해당 프로세스를 중단할까요?"로 사용자에게 확인 후 `OpenProcess`+
  `TerminateProcess`로 종료. 실제 subprocess로 파일을 열어놓고 테스트해서 검증함 — 이 과정에서
  `sys.executable`(venv python.exe)이 런처 스텁을 거쳐 실행되어 `Popen.pid`가 실제 파일을 잠근
  PID와 다르다는 것을 발견했지만, Restart Manager는 항상 실제로 파일을 잠근 PID를 정확히 찾아내므로
  이건 테스트 스크립트에서만 신경 쓸 부분이고 프로덕션 코드엔 영향 없음.
- **`.git` 폴더가 프로세스 잠금 없이도 삭제 안 되는 경우** — 처음엔 이것도 프로세스 잠금인 줄
  알았으나 Restart Manager가 빈 목록을 반환함. 실제 원인은 git이 pack/object 파일을 읽기 전용
  속성으로 만들어두는 Windows 특성이었음. `os.chmod(path, stat.S_IWRITE)` 후 재시도하는
  `_clear_readonly_and_retry`로 해결.
- **`TerminateProcess()` 직후 재시도가 실패하는 레이스 컨디션** — 프로세스가 종료돼도 OS가 파일
  핸들을 즉시 놓아주지 않을 수 있어서, 종료 성공 후 바로 1회 재시도하면 여전히 실패할 때가 있었음.
  최대 10회, 0.2초 간격 백오프 재시도로 해결.
- **clone 대상 폴더가 비어있어야 하는 git 제약과 방금 만든 백업 폴더가 충돌하는 문제** — 백업
  위치로 local 폴더 자신을 고른 경우, 그 백업 폴더만 남기고 나머지를 비운 뒤 바로 그 자리에
  clone하면 "target not empty" 에러가 남. `tempfile.mkdtemp()`로 임시 디렉토리에 먼저 clone한 뒤
  그 안의 내용물을 `shutil.move`로 local 폴더 안으로 옮기는 방식으로 우회.

6가지 실제 시나리오(잘못된 remote / local 없음 / local 있고 clean / local 있고 dirty+백업 자기
자신에 저장 / dirty+백업 거부 / 실제 프로세스 잠금+종료 동의)를 실제 로컬 git 저장소와 실제
subprocess 잠금으로 헤드리스 테스트해서 전부 통과 확인. standalone 내보내기(`exporter.py`)에도
동일 기능이 포함되어 있는지 생성된 소스에 `git clone`/`find_locking_processes`/`RmStartSession`
문자열이 들어있고 `ast.parse`/`py_compile`이 통과하는 것으로 확인함.

## gvf 탭 추가: "FPGA 자원 현황" 뼈대 (2026-08-15)

사용자가 빌더에서 직접 새 탭을 만들고 "gvf"로 이름 붙인 뒤, 그 탭에 "오늘은 껍데기만" 만들어달라는
요청으로 `gvf_widget.py`(`GvfPanel`)를 새로 추가함 — 기존 git/alarm/윈도우 현황 위젯과 같은 패턴
(팔레트에 없는 전용 복합 위젯을 `WIDGET_FACTORIES`에 `kind` 하나로 등록해 그 탭에 직접 배치)을
그대로 따름. 일반 팔레트 위젯(버튼/입력창 등)은 캔버스에 낱개로 놓이는 평면 모델이라 "제목 있는
사각형 안에 여러 하위 위젯"처럼 중첩 구조를 표현할 수 없어서, git/alarm/윈도우현황과 마찬가지로
전용 위젯 모듈로 구현하는 쪽을 택함.

구성: 왼쪽 위 "FPGA 자원 현황" 제목의 `QGroupBox` 안에 표시창 3개(`_DisplayRow`)가 세로로 나열되고,
각 표시창 오른쪽에 시작/종료 시간을 보여줄 테두리 없는 디지털 시계 스타일 표시(`_DigitalTimeBox`,
검은 바탕+초록 모노스페이스 글씨)가 붙는다. 지금은 표시창에 "FPGA 번호 N", 시계에 "00:00:00" 고정값만
있는 뼈대 상태 — 실제 자원 데이터를 채우거나 시간을 실시간으로 계산/갱신하는 로직은 다음에 이어서 구현.
그룹박스 제목("gvf 자원 현황" → "FPGA 자원 현황")/표시창 라벨("표시창 N" → "FPGA 번호 N")/시계
테두리 제거는 첫 구현 직후 사용자 피드백으로 바로 수정함 (테두리는 `border: none`만으로는 안 지워질
가능성을 대비해 `setFrameShape(QFrame.Shape.NoFrame)` + `setLineWidth(0)`도 같이 명시).

`canvas_window.py`(import, `WIDGET_FACTORIES["gvfpanel"]`, `LINE_DEFAULT_SIZE["gvfpanel"] = (340,
200)`)와 `exporter.py`(라벨/설명 텍스트, 코드 생성 분기, 소스 임베딩 조건부 포함)에 git/alarm/
윈도우현황과 동일한 자리마다 짝을 맞춰 추가해서 standalone 내보내기에서도 그대로 동작하도록 함.
헤드리스로 다음을 확인: `GvfPanel` 단독 렌더링(표시창/시계 텍스트 정상), `canvas_window`의
`WIDGET_FACTORIES`/`LINE_DEFAULT_SIZE` 등록 확인, `exporter.generate_source`가 만든 소스가
`ast.parse`/`py_compile` 통과 + 실제로 그 소스를 실행해서 만든 standalone 앱에서 "gvf" 탭에
`GvfPanel`이 표시창 3개와 함께 정상 생성되는 것, 그리고 실제 `builder_state.json`(gvf 탭에
`gvfpanel_1` 엔트리 추가)을 그대로 복원한 캔버스 페이지를 렌더링해서 레이아웃(그룹박스 좌상단,
표시창 3개 + 시계 3개)이 의도대로 나오는 것.

## gvf 탭: "FPGA 자원 취득" 패널 + 시작/중지 버튼 추가 (2026-08-15)

기존 `GvfPanel`(좌상단) 옆에 두 번째/세 번째 전용 위젯 `FpgaAcquisitionPanel`/`FpgaControlButtons`를
같은 `gvf_widget.py`에 추가함. 사용자가 한 요청을 여러 번에 걸쳐 보내면서 필드 이름/기본값이
중간에 바뀌었음 — 처음엔 "FPGA 획득 주기"(기본 5분) 하나만 있었다가, 이어진 요청으로 "FPGA 취득
간격"(기본 120분)으로 이름/기본값이 바뀌고 "max FPGA 취득" 필드가 새로 추가됨. 최종 상태:

`FpgaAcquisitionPanel` — "FPGA 자원 취득" 제목의 `QGroupBox` 안에 다섯 줄:
- "FPGA 획득 마지막 시도" + `QTimeEdit`(기본값 = 위젯 생성 시점의 현재 시각, HH:mm:ss, 직접 조절
  가능) — 이전의 `_DigitalTimeBox`(정적 표시 전용)와 달리 실제 입력 위젯을 요청받아서 `QLabel` 대신
  `QTimeEdit`을 씀.
- "FPGA 취득 간격" + `QSpinBox`(1~1440분 범위, 기본값 120분, " 분" 접미사, 조절 가능).
- "max FPGA 취득" + `QSpinBox`(최솟값 1, 최댓값 999, 기본값 1, 조절 가능).
- 디렉토리 입력창(placeholder "명령어 입력 디렉토리") — `git_widget.py`의 `_RepoPairBox.local_edit`과
  똑같은 패턴(`QLineEdit` + 트레일링 `SP_DirIcon` 액션 + `QFileDialog.getExistingDirectory`)을
  그대로 재사용.
- 토글형 "자원 계속 사용" 버튼(`setCheckable(True)`) — 눌린 상태(`toggled` 시그널)에 따라 자기
  글자가 "자원 계속 사용" ↔ "FPGA 계속 사용중"으로 바뀜.

`FpgaControlButtons` — "FPGA 자원 취득" 사각형 오른쪽에 놓이는 시작/중지 버튼 한 쌍. 시작 버튼을
누르면 자기 글자가 "동작중"으로 바뀌고, 중지 버튼을 누르면 (자기 글자는 그대로 "중지"인 채로)
시작 버튼 글자가 "다시 시작"으로 바뀜 — 두 버튼이 서로 다른 상대방 상태를 갱신하는 단순 토글
쌍으로 구현.

`canvas_window.py`에 `kind="fpgaacquisition"`/`"fpgacontrol"`로 등록(`WIDGET_FACTORIES`,
`LINE_DEFAULT_SIZE`는 각각 (360, 180)/(170, 36)), `exporter.py`에도 라벨/설명 텍스트/코드 생성
분기를 짝 맞춰 추가하고 `uses_gvf_panel` 플래그를 `gvfpanel`/`fpgaacquisition`/`fpgacontrol` 중
하나라도 쓰이면 `gvf_widget.py` 소스를 통째로 임베드하도록 바꿈(같은 파일에 세 클래스가 있으므로).
세 위젯을 가로로 나란히 놓다 보니 기존 창 너비(821px)로는 좁아서, 실제 `builder_state.json`의
`window.width`를 821 → 1000으로 늘리고(다른 탭들의 위젯은 전부 821 안에 들어가 있어서 창을
넓히는 것만으로는 다른 탭에 영향 없음을 먼저 확인), gvf 탭에 `fpgaacq_1`(x=441, y=20, 360×180)과
`fpgactrl_1`(x=811, y=20, 170×36) 엔트리를 추가/조정함. 헤드리스로 확인: `FpgaAcquisitionPanel`/
`FpgaControlButtons` 단독 렌더링(입력값 기본값·조절·토글 동작 정상), `canvas_window`/`exporter`
등록 확인, `exporter.generate_source`로 만든 소스가 `ast.parse`/`py_compile` 통과 + 실행해서 세
패널이 모두 정상 생성되고 시작/중지·자원 계속 사용 버튼 클릭이 실제로 텍스트를 토글하는 것, 실제
`builder_state.json` 복원 결과를 렌더링해서 세 사각형이 가로로 겹치지 않고 배치되는 것.

## gvf 탭 정리 + appData 자동 저장 추가 (2026-08-15)

이어진 요청들로 gvf 탭 레이아웃을 재정리함:
- **시작/중지 버튼을 "FPGA 자원 취득" 사각형 안으로 이동**: 별도 위젯이던 `FpgaControlButtons`를
  통째로 삭제하고, 그 버튼 두 개를 `FpgaAcquisitionPanel` 안의 한 줄(`control_row`)로 옮김.
  `canvas_window.py`/`exporter.py`의 `fpgacontrol` kind 등록을 전부 되돌리고, 그만큼 필요 없어진
  창 너비(1000 → 821)도 다시 줄임(다른 탭 위젯이 전부 821 안에 들어가는 것을 재확인 후 진행).
- **"자원 계속 사용" 버튼 제거**: 요청으로 "FPGA 계속 사용" 이름으로 바꿨다가, 바로 다음 요청으로
  버튼 자체(및 토글 핸들러)를 완전히 삭제함.
- **"FPGA 대기열 삭제" 버튼 추가 후 위치 조정**: 처음엔 시작/중지 버튼 줄 아래(맨 끝)에 추가했다가,
  요청으로 명령어 디렉토리 입력창 바로 아래·시작/중지 버튼 줄 바로 위로 옮김.
- **"아이디" 입력창 추가**: `FpgaAcquisitionPanel` 맨 위에 문자열 입력창(`QLineEdit`) 한 줄을
  새로 추가.
- **`GvfPanel`의 표시창/시계 재구성**: "FPGA 번호 N" 표시창을 `setFixedWidth(90)`으로 좁히고, 그
  오른쪽의 `_DigitalTimeBox`(시작/종료 시계) 오른쪽에 "반납" 버튼을 새로 추가.
- **시계 테두리 재단순화**: 사용자가 실제 앱 스크린샷을 보내며 "테두리가 너무 두껍다"고 재차
  지적함 — `border-width: 0; border-style: none; border-radius: 4px;`처럼 border-radius를 남겨둔
  상태였는데, 작은 박스에서 둥근 모서리 자체가 두꺼운 테두리처럼 보일 수 있다고 판단해 아예
  `border: none;`만 남기고 `border-radius`를 제거함(완전히 각진 사각형으로 단순화).

**appData 자동 저장**: `gvf_widget.py`에 alarm/git 위젯과 같은 패턴(`_STATE_DIR`/`_APP_DATA_DIR`
계산, `GVF_STATE_FILE = appData/gvf_state.json`, `_load_gvf_state`/`_save_gvf_state`)을 추가함.
`FpgaAcquisitionPanel`의 "아이디"/"FPGA 획득 마지막 시도"/"FPGA 취득 간격"/"max FPGA 취득"/"명령어
입력 디렉토리" 다섯 개 입력값을 생성 시점에 파일에서 복원하고, 이후 각 위젯의 변경 신호
(`editingFinished`/`valueChanged`, 디렉토리는 폴더 선택 직후에도 명시적으로 저장 호출)에 맞춰
자동으로 다시 저장함. alarm/git과 달리 이 상태 파일은 처음 만드는 것이라 레거시 마이그레이션
로직은 필요 없었음. 헤드리스로 값을 바꾸고 재생성한 인스턴스가 그대로 복원되는 왕복을 확인했고,
standalone 내보내기로 만든 앱도 빌더와 별도인 자기 폴더의 `appData/gvf_state.json`에 저장되는
것을 실행까지 해서 확인함.

## gvf 탭: "FPGA loading" 패널 추가 + 콤보박스 전역 스타일 개선 + 크기/여백 정리 (2026-08-15)

**"FPGA loading" 패널 추가**: `gvf_widget.py`에 세 번째 전용 위젯 `FpgaLoadingPanel`을 추가해서
gvf 탭 아래쪽에 배치함. "FPGA loading" 제목의 `QGroupBox` 안에 드롭박스 3개가 가로로 나란히 있고,
그 아래 "시작" 버튼:
- 첫 번째: 고정 목록("FPGA v18.0"/"FPGA v19.0"/"FPGA v24.0"/"FPGA v25.0").
- 두 번째(`_FpgaNumberComboBox`): **다른 위젯(`GvfPanel`)의 상태를 동적으로 읽는 드롭박스** —
  `showPopup()`을 오버라이드해서 열릴 때마다 `self.window().findChild(GvfPanel)`로 같은 창 안의
  `GvfPanel`을 찾고, 그 `rows`의 `display_label` 텍스트("FPGA 번호 N")를 다시 읽어 채움(비어있는
  표시창은 목록에서 빠짐). 전용 위젯끼리는 `canvas_window.py`가 자동으로 서로를 연결해주지 않으므로
  (그건 "동작 설정" 자연어 코드가 `self.<id>`로 쓰는 방식에서만 됨), `self.window()` 기반 탐색으로
  같은 창 안 어디에 있든 찾아내는 방식을 택함 — 어느 탭에 있든, 위젯 생성 순서에도 안 흔들림.
- 세 번째: 고정 목록("TLC"/"QLC"/"SLC/QLC"/"TLC/QLC").
`canvas_window.py`(`kind="fpgaloading"`, `LINE_DEFAULT_SIZE`)/`exporter.py`(라벨/설명/코드 생성
분기, `uses_gvf_panel` 조건에 추가)에도 짝을 맞춰 등록함. 헤드리스로 두 `GvfPanel` 표시창 하나를
비웠을 때 드롭박스 아이템이 실제로 2개로 줄어드는 것, standalone 내보내기 실행 결과에서도 동일하게
동작하는 것을 확인함.

**콤보박스 전역 스타일 개선**: "실제 상용 코드에서 쓰이는 것처럼 드롭박스 모양을 바꿔달라"는
요청으로 `theme.py`의 `QComboBox` 스타일을 `QLineEdit`/`QTextEdit`와 공유하던 뭉뚱그린 규칙에서
분리해 전용 블록으로 새로 만듦: hover/focus/disabled 상태, 오른쪽에 테두리로 구분된 드롭다운 버튼
영역(하늘색 배경, hover 시 진하게), 팝업 목록(`QComboBox QAbstractItemView`)에 둥근 테두리·아이템
패딩·앱 강조색(`#5b72e0`) 선택 표시를 추가함. `theme.py`는 항상 내보내기에 통째로 포함되는 파일이라
(탭바와 마찬가지로 `uses_X` 플래그로 안 걸러짐) 이 변경 하나로 빌더와 standalone 양쪽, 그리고 gvf
말고도 앱 전체의 모든 드롭박스에 한 번에 적용됨. 헤드리스로 콤보박스 자체와 팝업 목록 렌더링을
각각 캡처해서 확인함.

**"FPGA 자원 현황"/"FPGA 자원 취득" 크기 통일 + "FPGA loading" 여백 정리**: `GvfPanel`의
`LINE_DEFAULT_SIZE`를 `FpgaAcquisitionPanel`과 동일한 (360, 250)으로 맞추고, 실제
`builder_state.json`의 `gvfpanel_1` 크기도 그에 맞게 조정함. `FpgaLoadingPanel`의 내부 여백은
기본값(레이아웃 마진 미지정)으로는 위쪽만 유독 넓었음(헤드리스 픽셀 측정: 왼쪽/오른쪽 10px, 위
29px, 아래 16px) — `QGroupBox`가 제목 글자를 위해 위쪽에 항상 별도 공간을 추가로 예약하는 스타일
특성 때문. `form.setContentsMargins(13, 0, 13, 10)`으로 위쪽 마진을 명시적으로 줄여 제목이 차지하는
공간과 합쳐졌을 때 네 방향이 비슷하게 보이도록 맞춤(완전히 동일한 픽셀 값은 제목이 있는 그룹박스
구조상 불가능 - 위쪽은 항상 제목 높이만큼 더 필요함).

## "FPGA loading" 드롭박스 → 라디오 버튼 전환 + 시계 패딩/반납 버튼 크기 조정 (2026-08-15)

**드롭박스 3개 → 라디오 버튼 열 3개**: 콤보박스 3개를 없애고 라디오 버튼으로 바꿔달라는 요청으로
`FpgaLoadingPanel`을 다시 씀. 처음엔 라디오 버튼 11개(4+3+4)를 전부 한 줄로 나열했더니 헤드리스로
측정한 `sizeHint`가 가로 1576px까지 벌어져서(각 라디오 버튼 사이 spacing이 계속 누적됨), 그룹별로
세로로 쌓은 좁은 열 3개를 만들고 그 열들을 가로로 배치하는 방식으로 바꿔 552px까지 줄임 - 실사용
가능한 폭으로 돌아옴. 최종 구성: 첫 번째 열(FPGA 버전 4개), 두 번째 열(FPGA 번호 - "FPGA #1"/"FPGA
#2"/"FPGA #3"로 명명, 옆에 `QIntValidator(0, 999)` + `setMaxLength(3)`로 숫자 3자리까지만 받는
입력칸), 세 번째 열(메모리 타입 4개), 맨 오른쪽에 "시작" 버튼(이전엔 별도 줄 맨 아래였는데 요청으로
같은 줄 맨 오른쪽으로 이동). 이전 버전에 있던 "`GvfPanel`의 FPGA 번호 표시창을 열 때마다 다시
읽어서 채우는" 동적 드롭박스(`_FpgaNumberComboBox`)는 라디오 버튼으로 바뀌면서 고정 라벨("FPGA
#1/2/3")로 단순화되어 완전히 제거함.

**시계 패딩/반납 버튼 크기**: "FPGA 자원 현황"의 시작/종료 디지털 시계 테두리가 여전히 두껍다는
반복된 피드백 — 이전에 `border: none`/`border-radius` 제거까지 했는데도 재차 지적받고 나서야,
"테두리"로 지칭한 게 실제 border 속성이 아니라 `_DigitalTimeBox` 내부의 넉넉한 padding(가로 10px/
세로 6px)이 검은 배경과 초록 글씨 사이에 두꺼운 여백처럼 보였던 것이라고 재해석함. `layout.
setContentsMargins(10, 6, 10, 6)` → `(6, 2, 6, 2)`, `spacing(2)` → `spacing(0)`으로 글자에 바짝
붙는 크기로 줄임. 같은 요청 묶음에서 "반납" 버튼은 반대로 기본 크기(38×18)의 가로·세로 각각
1.5배(57×27)로 키움 — `sizeHint()`를 애플리케이션 스타일시트가 적용된 뒤에 읽어야 정확하다는 점을
standalone 내보내기 테스트 중 재확인함(스타일시트 적용 전에 읽으면 Qt 기본 크기가 나와서 배율 계산이
어긋남 - 실제 내보낸 앱은 `app.setStyleSheet(...)`가 창 생성보다 먼저 실행되므로 문제 없음, 테스트
스크립트에서 그 순서를 안 지켰을 때만 재현되는 착시였음).

## gvf 탭: 라벨/레이아웃 세부 조정 + 전체 위젯 appData 저장 확대 (2026-08-15)

**`GvfPanel`("FPGA 자원 현황")**: `_DisplayRow`의 표시창 라벨을 "FPGA 번호 N" → "FPGA #N"으로
바꾸고, 그 오른쪽에 3자리 숫자 입력칸(`QIntValidator(0, 999)` + `setMaxLength(3)`, "FPGA loading"의
숫자 입력칸과 같은 패턴)을 새로 추가함. `_DigitalTimeBox`는 `setMinimumWidth(210)`으로 가로를
넓히고, 레이아웃 순서를 `[표시창][숫자입력][시계][stretch][반납 버튼]`로 바꿔서 "반납" 버튼이 줄
맨 오른쪽 끝(진짜 여백을 두고 밀려난 위치)에 오도록 함 — 이전엔 시계 바로 뒤에 붙어 있고 stretch가
그 뒤에 있어서 실제로는 오른쪽 끝이 아니었음.

**`FpgaLoadingPanel`("FPGA loading")**: 내부 여백을 `GvfPanel`의 표시창 3개 사이 간격(10px)에
맞춰 좌/우/아래를 10으로 통일(위쪽은 이전과 같이 0 - 그룹박스 제목이 이미 별도 공간을 차지하므로).
라디오 버튼 열 3개 사이 간격을 24 → 40으로 늘림. "FPGA #1/#2/#3" 라디오 버튼 옆에 공유 입력칸
하나만 있던 것을, 각 라디오 버튼마다 자기 전용 3자리 숫자 입력칸이 붙도록 바꿈(`number_value_edits`
리스트로 관리). "시작" 버튼도 "반납" 버튼과 같은 방식(생성 시점 `sizeHint()` × 1.5)으로 키움.

**appData 저장을 세 위젯 전부로 확대**: 지금까지는 `FpgaAcquisitionPanel`만
`_save_gvf_state(dict)`로 파일 전체를 덮어써서 저장했는데, 이 방식은 `GvfPanel`/`FpgaLoadingPanel`도
같은 파일에 저장하게 되면 서로의 데이터를 지워버리는 문제가 있었음. `_update_gvf_state(key, value)`
헬퍼(파일을 읽고 → 그 키만 갱신 → 다시 씀)를 추가하고, 세 위젯이 각자 다른 최상위 키를 쓰도록
정리함: `GvfPanel`은 `"display_numbers"`(숫자 입력칸 3개 값의 리스트), `FpgaAcquisitionPanel`은
`"acquisition"`(기존 5개 필드를 감싼 dict로 스키마 변경 - 아직 실사용 데이터가 없어서 마이그레이션
불필요), `FpgaLoadingPanel`은 `"loading"`(라디오 3그룹의 선택된 텍스트 + 숫자 입력칸 3개 값).
헤드리스로 세 위젯을 각각 다른 값으로 바꾸고 저장 → 파일 내용에 세 키가 모두 온전히 남아있는지 →
새 인스턴스 3개가 각자 정확히 복원되는지까지 왕복 확인했고, standalone 내보내기에도
`_update_gvf_state`가 포함되어 `ast.parse`/`py_compile`이 통과하는 것을 확인함.

## gvf/git 탭 세부 레이아웃 6건 일괄 반영 (2026-08-15, 야간 배치)

토큰 리필 시각(19:51 KST) 이후 자동 실행하도록 예약해둔 6개 요청을 이어서 한 번에 반영함:

1. **"FPGA loading" 하단 여백 확대**: 라디오 버튼 열 3개(version/number/memory)의 세로 spacing을
   4→2로 줄여 자연스러운 콘텐츠 높이를 108로 낮추고, `fpgaload_1` 캔버스 높이를 184→110으로 줄임
   (내부 top/left/right/bottom 여백 비율은 그대로 유지 - 이전 세션에서 이미 "top=0 처리해도
   시각적으로 다른 방향과 비슷해짐"을 확인한 설계를 그대로 씀). 결과: 박스 자체는 작아지고, 박스
   아래쪽부터 탭 경계까지의 여백은 13px→84px로 크게 늘어남.
2. **"max FPGA 취득"을 "FPGA 취득 간격" 오른쪽으로 이동**: 두 줄이던 것을 한 줄로 합침(항목
   7개→6개). `form`의 남은 6개 항목에 `setStretch(i, 1)`을 균등하게 줘서, 사각형 세로 길이(245)는
   그대로 두고 남는 공간이 6개 항목에 고르게 분배되도록 함.
3. **"FPGA #1/#2/#3" 표시창 폭 축소 + "소유중" 버튼 추가**: 폭을 90→86으로 줄임("조금 짧게"라는
   요청과 별개로, "FPGA #1" 텍스트가 실제로 84px가 필요해서 이보다 더 줄이면 텍스트가 잘림 - 여러
   폭을 시도해보며 QFontMetrics로 실측 확인함). "반납" 버튼 왼쪽에 크기가 완전히 동일한("반납"의
   1.5배 크기를 그대로 재사용) "소유중" 버튼을 추가.

   **물리적 공간 충돌과 트레이드오프**: 2번(줄 병합)과 3번(버튼 추가)을 문자 그대로 적용하면
   "FPGA 자원 현황"/"FPGA 자원 취득" 두 사각형에 필요한 최소 폭 합이 820px 창 폭을 초과함(약
   847px, 그룹 여백을 최대한 줄여도). "FPGA 취득 간격"/"max FPGA 취득" 두 라벨의 폰트만 11px로
   살짝 줄이고, 스핀박스 폭/간격을 최대한 줄이고, 두 그룹의 좌우 여백을 10→6으로 줄인 뒤에도 최종
   필요 폭 합이 801px이라 사용자가 요청하지 않은 부분(창 크기)은 건드리지 않고, 두 사각형의 좌우
   여백만 6/6으로 동일하게 유지한 채(이전 세션 요청 "왼쪽 여백=오른쪽 여백"은 지킴) 폭 자체는
   420/381로 달라짐 - "정확히 같은 크기" 요구는 이번 변경들과 물리적으로 양립 불가능해서 포기함.
   최종 좌표: `gvfpanel_1`(6,20,420,245), `fpgaacq_1`(433,20,381,245).
4. **link 탭 좌우 여백 통일**: claude 헤더 왼쪽 여백(20)과 C++ 헤더 오른쪽 여백(50)이 달랐던 것을,
   모든 위젯의 x좌표에 +15를 일괄 적용해서 양쪽 다 35로 맞춤(내부 3열 배치/구분선 간격은 그대로,
   전체를 오른쪽으로 15px 평행이동한 것뿐).
5. **git 탭 remote/local 입력창 크기 통일**: `_RepoPairBox`의 "remote:"/"local:" 라벨 폭이 서로
   달라서(문자 수 차이) 그 뒤에 오는 `QLineEdit`(stretch=1)의 실제 폭이 서로 달랐던 것을, 두 라벨에
   동일한 `setFixedWidth(둘 중 더 긴 쪽)`를 줘서 두 입력창의 시작 x좌표와 폭이 완전히 같아지도록 함.
6. **git 탭 저장소 사각형 아래쪽 여백 + 버튼 위치**: `GitPanel`의 트레일링 `outer.addStretch()`가
   패널에 할당된 캔버스 높이(420)의 남는 공간을 전부 떠안아서 체감 아래쪽 여백이 좌우 여백(12)보다
   훨씬 커 보였던 것을 발견 - `addStretch()`를 없애고 `outer.setContentsMargins`를
   `(12,10,12,10)`→`(12,4,12,12)`로 바꿔(위쪽은 버튼을 살짝 위로 올리려고 축소, 아래쪽은 좌우와
   동일하게) `gitpanel_1` 캔버스 높이 자체를 새 콘텐츠의 자연 크기(356)에 맞춰 420→360으로 줄임.
   헤드리스로 최종 bottom gap(12)이 left margin(12)과 정확히 같아지고 `scan_button`이 y=4로
   올라간 것을 확인함.

전부 헤드리스로 (`CanvasWindow` 복원 경로 기준) `geometry() >= minimumSizeHint()`를 확인해 클리핑
없음을 검증했고, `exporter.generate_source`로 만든 소스도 `ast.parse` 통과 확인함. 화면 스크린샷은
gvf 탭만 성공적으로 확인함(1~3번 항목 육안 확인 완료) - git/link 탭은 스크린샷 시도 중 이 머신의
디스플레이 DPI 가상화 때문에 PowerShell `GetWindowRect`/`CopyFromScreen`/마우스 좌표가 서로 다른
좌표계를 가리키는 문제가 반복돼 캡처에 실패함(각 새 PowerShell 프로세스마다 `SetProcessDPIAware`를
먼저 안 부르면 좌표가 어긋남) - 기능적으로는 헤드리스 검증으로 충분히 확인됐으나, 다음에 이
머신에서 다시 스크린샷 검증이 필요하면 PowerShell 스크립트 맨 앞에 `SetProcessDPIAware()`를 반드시
먼저 호출해야 함을 기록해둠.

## gvf 탭: 사각형 크기/여백 통일 + 시계 "테두리" 버그 근본 원인 수정 (2026-08-15)

**"FPGA 자원 현황"/"FPGA 자원 취득" 사각형 크기·여백 통일**: 두 사각형을 정확히 같은 크기로,
"FPGA 자원 취득" 오른쪽 여백을 "FPGA 자원 현황" 왼쪽 여백과 같게 맞춰달라는 요청으로 계산해보니
반납 버튼 등 다른 요소는 그대로 두고 시계 폭만 줄이는 걸로는 820px 창 폭 안에서 물리적으로 불가능함을
확인(자세한 계산은 이번 대화 기록 참고 - 헤드리스로 각 요소의 styled sizeHint를 직접 측정해서
검증함). 사용자에게 트레이드오프를 확인받아(반납 버튼/여백도 같이 줄이는 쪽 선택) 시계 폭을
420(기존 여유분 포함) → 156으로 우선 줄여 두 사각형을 395×245로 통일, 여백 10px로 맞춤.

**시계 "테두리" 재발 - 진짜 원인 발견**: 위 조정 후에도 사용자가 "시계 테두리가 여전히 남아있다"를
세 번째로 지적함 - 헤드리스 픽셀 검사(`grab()`)로는 문제를 못 찾았는데(그랩한 픽스맵 자체는
border:none이 맞음), 실제 화면을 PowerShell(`System.Drawing` Bitmap + `CopyFromScreen`)으로
스크린샷 찍어서 확대해보고서야 진짜 원인을 발견함: `theme.py`의 전역 규칙
(`QMainWindow, QWidget { background-color: #f4f5f8; }`)이 `_DigitalTimeBox` **내부의 `QLabel`
자식**(`start_label`/`end_label`)에도 적용되는데, 이 라벨들의 스타일시트가 `color`/`font-family`/
`font-size`만 지정하고 `background-color`는 지정하지 않아서, 전역 회색 배경이 라벨 영역을 덮어버리고
`_DigitalTimeBox` 자신의 진짜 배경(#101418)은 라벨 주위 여백(레이아웃 margin) 부분에서만 얇게
비쳐 보였던 것 - 이게 사용자에게 "두꺼운 검정 테두리"로 보인 진짜 정체였음(GitPanel 상자 배경
투명화 때 겪었던 것과 같은 종류의 "전역 QWidget 배경 상속" 버그, 이번엔 프레임이 아니라 프레임
**내부의 자식 위젯**에서 발생). 라벨 스타일시트에 `background-color: transparent;`를 명시해서
해결 - 스크린샷으로 실제로 회색 프레임이 사라진 것까지 눈으로 확인함.

**추가 축소 + 최종 재배치**: 시계 텍스트의 이중 공백("시작  00:00:00") 제거, 내부 레이아웃 여백
(6,2,6,2) → (4,2,4,2) 축소, `setMinimumWidth`에 매직넘버 대신 `layout.sizeHint().width()`를 그대로
써서 텍스트가 바뀌어도 값이 낡지 않게 함 - 시계 실제 최소 폭이 140px까지 더 줄어듦. 이만큼 줄어든
폭을 두 사각형(380×245)과 여백(10→20px) 쪽으로 재분배함. "FPGA loading"은 지난 세션에 라디오 그룹
간격을 2배(80px)/시작 버튼을 3배로 키운 상태라 실제 필요 최소 폭이 790px이라, 800→794px로만 살짝
줄이고 여백도 10→13px로만 늘림(내용 잘림 없이 줄일 수 있는 한계) - 사용자에게 이 한계를 명시적으로
알림. 최종 좌표: `gvfpanel_1`(20,20,380,245), `fpgaacq_1`(420,20,380,245),
`fpgaload_1`(13,278,794,184). 헤드리스로 실제 `CanvasWindow`를 restore해서 세 위젯 모두
`geometry() >= sizeHint()`(잘림 없음)인 것과 겹침 없음을 재확인함.

**작업 중 재확인한 함정**: `builder_state.json`을 손으로 고칠 때, 앱이 아직 실행 중인 상태에서 먼저
JSON을 편집하고 나중에 앱을 닫으면 `closeEvent`가 예전 in-memory 상태로 방금 고친 JSON을 덮어써버림
(1회 실제로 겪음 - 20/380 값이 10/395로 되돌아감). 반드시 "먼저 그래스풀하게 닫기 → JSON 편집 →
재실행" 순서를 지켜야 함([[feedback-no-taskkill]] 메모리에 이미 있던 경고인데 이번에 순서를 한 번
어겨서 직접 재확인됨). 창 스크린샷은 `GetWindowRect`가 DPI 가상화로 부정확할 수 있어서, 전체 화면을
찍은 뒤 필요한 영역만 크롭하는 방식이 더 안정적이었음.

## 알려진 미완/보류 항목

- **gvf 위젯 상세 구현**: `gvf_widget.py`는 입력값 저장(appData) 말고는 아직 레이아웃 뼈대뿐 —
  표시창 3개가 실제로 어떤 자원을 보여줄지, 시작/종료 시간을 어떻게 계산·갱신할지, "아이디"를
  어디에 쓸지, "FPGA 취득 간격"/"max FPGA 취득" 값에 맞춰 실제로 주기적 자동 획득을 시도하는
  타이머 로직, "명령어 입력 디렉토리"에서 실제로 명령어를 실행하는 로직, "반납"/"FPGA 대기열
  삭제"/시작·중지 버튼이 실제로 무엇을 하는지는 다음 세션에서 이어서 정의/구현해야 함.
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

## link/git 탭 세부 정렬 마무리 + gvf 탭 대규모 반복 조정 (2026-08-15)

**link 탭**: 헤더 입력창 폭을 버튼과 동일하게(230→220) 맞추고, 두 세로 구분선을 칼럼 사이 여백 정중앙(양쪽 10px씩)으로 옮김 - 이전엔 한쪽 15px/반대쪽 5px로 치우쳐 있었음.

**git 탭**: `GitPanel`의 좌우 여백(10)보다 아래쪽 여백(66)이 훨씬 컸던 것을 `gitpanel_1` 높이를 늘려(360→416) 10=10=10으로 맞춤. `_RepoPairBox`의 "remote:"/"local:" 라벨 폭을 12px 더 넓히고(입력창은 그만큼 자동으로 좁아짐) 가운데 정렬로 바꿔서 "local:"이 넓어진 라벨 박스 안에서 한쪽으로 쏠려 보이던 것도 고침.

**gvf 탭**: 이 세션에서 가장 많이 반복 조정된 영역. 시계 폭(30~50%씩 여러 차례 조정, 최종 시분만 표시 "00:00"+16px 폰트)/FPGA #N 표시창·소유중·반납 버튼 크기(10%씩 축소)/FPGA 취득의 "max FPGA 취득" 줄 위치/FPGA loading OS 라디오 그룹(linux/windows/test) 추가 등 수많은 요청을 순차 반영하는 과정에서 두 가지를 배움:
- **`_DigitalTimeBox`는 `setFixedWidth`가 필수**: `setMinimumWidth`만 쓰면 이 위젯이 행(row) 안에서 유일하게 최대 폭이 없는 항목이라, 패널이 자기 콘텐츠보다 넓게 배정되면 남는 폭을 전부 이 시계 혼자 흡수해버려서 "폭을 N%만큼 줄인다"는 요청이 반영 안 되고 도로 커지는 버그가 있었음.
- **`QVBoxLayout.setStretch`로 항목 높이를 맞추는 방식은 위험함**: `FpgaAcquisitionPanel`의 6개 항목에 동일 stretch factor만 주고 패널을 자기 최소 높이(188)까지 줄였더니, 개별 위젯에 최소 높이가 명시돼 있지 않아 버튼 2개가 6px까지 짜부라져 사실상 안 보이는 버그가 발생함(사용자가 "제일 밑 두 칸이 안 보인다"고 리포트). 6개 항목 전부에 `setFixedHeight(26)`을 명시적으로 줘서 근본적으로 해결 - 이제 패널이 아무리 딱 맞게 줄어도 절대 찌그러지지 않음.

최종적으로 세 사각형(FPGA 자원 현황/취득/loading)은 서로 크기가 같거나(현황=취득, 397×250) 여백이 서로 대응하도록(loading 왼쪽=현황 왼쪽, loading 오른쪽=취득 오른쪽, loading 아래쪽=자기 좌우, 전부 8px) 맞춰졌음. 이 과정에서 "여백/간격을 N배로" 요청이 여러 개 동시에 겹치면 820px 고정 창 폭 안에 물리적으로 다 못 들어가는 경우가 여러 번 있었고, 그때마다 어느 요청을 얼마나 타협했는지 사용자에게 명시적으로 설명하는 방식으로 처리함 (예: 라디오 그룹 간격 30%→최소 증가만 반영, 시작 버튼 세로 2배 요청은 폭 예산 확보를 위해 한 차례 롤백). 매 변경마다 헤드리스로 `geometry() >= minimumSizeHint()` 클리핑 검증 + standalone 내보내기 컴파일 확인을 거침.

## 개발자용 레이아웃 검사 스크립트 추가 (2026-08-15)

`md_files/future_work_for_poor_developer.md`(개인용 도구 관점의 향후 작업 문서)의 1순위 항목으로
`tools/inspect_layout.py`를 추가했다. `builder_state.json`을 헤드리스로 복원해서 지정한 탭(또는
전체)의 모든 위젯 x/y/width/height, 탭 경계까지의 좌우상하 여백, 그리고 **각 위젯의 가장 가까운
오른쪽/아래쪽 이웃과의 간격**을 표로 찍어준다:

```powershell
$env:PYTHONIOENCODING = "utf-8"   # 한글 깨짐 방지 (PowerShell 콘솔 코드페이지 이슈)
venv\Scripts\python.exe tools\inspect_layout.py gvf   # 특정 탭만, 인자 없으면 전체 탭
```

이 세션 내내 "여백을 같게", "간격을 동일하게" 같은 요청을 처리할 때마다 매번 새로 짰던 임시
헤드리스 스크립트를 하나로 정리한 것 - 앞으로 같은 종류의 요청은 이 스크립트 실행 한 번으로 현재
상태를 파악할 수 있다. 처음엔 모든 위젯 쌍의 간격을 다 찍었더니 실제로 인접하지 않은 위젯 쌍까지
전부 나와서(위젯 16개짜리 link 탭에서 수십 줄) 노이즈가 심했음 - 각 위젯마다 "가장 가까운" 오른쪽/
아래쪽 이웃 하나씩만 남기도록 고쳐서 실사용 가능한 수준으로 정리함. 7개 탭 전부(gvf/git/wiki/윈도우
현황/alarm/link/설명, 합성 위젯 포함) 대상으로 크래시 없이 정상 동작 확인함.

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
