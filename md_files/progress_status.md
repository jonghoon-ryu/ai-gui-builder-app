# progress_status.md — 현재까지 진행 상황 (다음에 이어서 시작할 때 참고)

기준 시점: 2026-08-16 밤. 이 문서는 "지금 뭐가 되어 있고, 다음에 뭘 더 할 수 있는지"를 빠르게
파악하기 위한 스냅샷이다. 아래 두 섹션(이 섹션, "현재 탭 구성")은 항상 최신 상태를 유지하고, 그
밑으로는 뭘 언제 왜 바꿨는지 날짜순으로 쌓아둔 작업 로그다(과거 항목은 당시 기준으로 정확했던
서술이므로 나중에 그 내용이 또 바뀌어도 과거 항목 자체는 고쳐 쓰지 않음 - 최신 사실은 항상 이
요약과 "현재 탭 구성"만 본다). 자세한 사용법은 `how_to_use.md`, 지금까지의 요구사항 변경 이력은
`tool_requirement.md` 참고.

## 지금 상태 (한 줄 요약)

빌더(`main.py`)는 완성도 있게 동작 중이고, 실제로 사용자가 7개 탭(gvf/git/wiki/윈도우 현황/alarm/
link/설명)에 위젯을 채워서 쓰고 있다. 위젯 종류(체크 박스·템플릿 사각형 컨테이너 포함), 저장/복원,
standalone 내보내기, 자연어 동작 생성용 화이트리스트 함수, 전용 "알람 시계"/"윈도우 현황"/"git"/
"gvf" 위젯, 되돌리기(Ctrl+Z, 삭제부터 이동/크기/색깔/이름/폰트/동작 설정/일괄 정렬까지) 전부 구현
완료 상태.

**2026-08-16에 저장 구조가 `builder_framework/` 기반으로 전면 재구성됨** - 자세한 내용은 각각의
아래 로그 섹션 참고, 요약만 하면:
- 저장 파일들이 저장소 루트에서 `builder_framework/default/`(기본 틀) 밑으로 옮겨짐
  (`builder_state.json`, `appData/{alarm,git_panel,gvf}_state.json` 전부). "다른 이름으로 틀
  저장"/"저장된 틀 불러오기"/"새 틀 시작하기"로 `builder_framework/<이름>/` 형태의 여러 "틀"을
  독립적으로 관리 가능.
- **활성 틀(active layout)** 추적 도입 - 창 제목("나만의 tool - <틀 이름>")에 항상 표시되고, "틀
  저장"/"실행 py 저장"/"standalone 실행 파일 저장"/alarm·git·gvf 위젯의 appData 저장이 전부 이
  활성 틀 폴더를 따라감(예전엔 alarm/git/gvf만 항상 고정 위치였음 - 지금은 통일됨).
  `builder_state.autosave.json`(90초 크래시 안전망)만 예외적으로 활성 틀과 무관하게 항상 레포
  루트에 고정.
- 2026-08-16 이전 내보내기 결과물이 쌓이던 `executable_py/`/`standalone/`은 정리됨(참고용 최소
  예제 하나만 `examples/website_link_button/app.py`로 옮겨 보존).

**2026-08-17에 파이썬/터미널을 전혀 모르는 사람을 위한 `md_files/beginner_guide.md` 추가됨** -
Claude Code가 이미 설치되어 있다는 전제로, 완성된 standalone `.exe`가 있으면 그냥 실행하는 법을,
없으면 빌더를 켜서(파이썬/venv 설치까지 Claude에게 말로 시키면 됨) 만드는 법을 안내. `how_to_use.md`
0번 섹션/`CLAUDE.md` 파일 구성 표에서 서로 연결됨. 같은 날 로컬 전용(`.gitignore`에 걸려 커밋 안 됨)
Claude Code 스킬 `run-ai-gui-builder-app`(`.claude/skills/`)도 만들어짐 - `launch`시 venv 없으면
자동으로 만들고 패키지 설치까지 하는 부트스트랩 로직 포함, 이 가이드가 실제로 동작함을 뒷받침.

Windows에서 직접 실행/검증됨 (아래 "Windows 이전" 참고).

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
디렉토리 입력창(폴더 아이콘으로 선택), 라디오 버튼(그룹별 독립, 첫 옵션 기본 선택),
**체크 박스**(그룹 없이 독립적으로 켜고 끔 — 2026-08-16 추가),
**템플릿**(제목 있는 빈 사각형을 한 번에 1~3개 놓는 프리셋 7종 — 2026-08-16 추가, 아래
"레이아웃 템플릿(사각형 컨테이너) 기능" 참고). 팔레트 자체도 세로 4칸(템플릿 절반씩 담은 칸 2개 /
나머지 위젯 / 저장 버튼)으로 구성됨, 템플릿 두 칸과 위젯 칸은 각각 독립적으로 스크롤됨. 저장 버튼
칸은 가로 구분선으로 세 그룹(틀 저장/다른 이름으로 틀 저장/저장된 틀 불러오기 — 새 틀 시작하기 —
실행 py 저장/standalone 실행 파일 저장)으로 나뉨(2026-08-16).

**알람 시계**와 **윈도우 현황**은 팔레트에 없음 — 각각 "alarm"/"윈도우 현황" 탭에 이미 고정
배치되어 있음 (사용자 요청으로 팔레트에서 뺌).

## 위젯 공통 기능

- 이동(드래그)/가장자리로 크기조절/러버밴드 다중선택/Delete 삭제/Ctrl+C·V 복사붙여넣기(탭 간 공유)
- **Ctrl+Z** — 가장 최근 작업 하나 되돌리기(삭제/이동/크기조절/색깔/이름/폰트/동작 설정 저장/일괄
  정렬까지 전부, 단일 슬롯 - 2026-08-16)
- 우클릭 메뉴: ID 표시, 동작 설정(자연어→코드), 색깔 변경, 이름 변경, 폰트 설정, 테두리 없애기,
  (라디오 버튼만) 옵션 추가/제거
- 탭: 이름 변경, 배경색, 우클릭으로 새 탭/삭제, 드래그로 순서 변경. **"틀 저장" 버튼을 눌러야만
  저장됨**(2026-08-16부터 - 앱 종료 시 자동 저장은 없어짐, 대신 90초마다 별도의 크래시 복구용
  자동저장이 항상 돎)

## 자연어 동작(화이트리스트 함수) 목록

`open_url`, `read_file`, `write_file`, `delete_file`, `list_dir`, `make_dir`, `move_file`,
`fetch_url`(429 자동 재시도 포함), `html_to_markdown`, `extract_images`, `download_file`,
`classify_image_with_claude`, `show_text_dialog`, `app_overview_text`, `tab_usage_text`,
`pick_startup_file`, `add_to_startup`, `remove_from_startup`(마지막 6개는 "설명" 탭용, 2026-08-15
추가 - `pick_startup_file`의 기본 파일 선택 위치는 2026-08-16부터 `builder_framework/`), 그리고
`QMessageBox`/`QInputDialog` 팝업. 전부 `code_binder.py`와 `exporter.py`(standalone용) 양쪽에
동일하게 구현되어 있음.

## 알람 시계 위젯 ("alarm" 탭)

일회성/주기적 알람 추가(달력+시간+커스텀 메시지), 등록된 알람 목록에 실시간 남은시간 + × 삭제 버튼,
위쪽 정렬된 달력 + 아날로그 시계, 알람 시간에 20cm×20cm 정사각형 팝업(현재 시각 + 24pt 굵은 글씨
메시지 표시). 구현은 `alarm_widget.py` (빌더/standalone 양쪽에서 같은 소스 파일을 그대로 사용).

**알람 목록 저장**: 아직 울리지 않은 알람은 추가/삭제/켜기끄기/발동 시점마다 `alarm_state.json`에
자동 저장되고 앱 재시작 시 복원됨 (이미 울린 일회성/끝난 주기적 알람은 저장에서 제외). 2026-08-12
구현 완료 — 아래 "알려진 미완/보류 항목"의 관련 항목은 해결됨.

## 윈도우 현황 위젯 ("윈도우 현황" 탭)

Windows 버전/CPU 모델 + CPU/메모리 사용률(탭이 화면에 보이는 동안 8초마다 갱신, 막대그래프, 90%
이상이면 빨간색 경고) + 로컬 고정 디스크별 사용량(C/D/E는 없어도 항상 표시, "없음"으로) + 휴지통·
temp 파일 현황(파일 개수/용량, "목록"으로 상세 목록 확인, "비우기"로 확인 후 비우기)을 보여주는
대시보드. "확인" 박스에 버튼 3개: **상위 프로세스**(CPU/메모리 Top5), **시작 프로그램 목록**
(레지스트리 Run키 + 시작프로그램 폴더), **시스템 변수 바로보기**(Windows 환경변수 편집창을
바로 띄움) — "폴더 용량" 버튼은 2026-08-15에 제거됨. `psutil` 같은 추가 패키지 없이
`ctypes`(+`winreg`/`subprocess`)로 Windows API를 직접 호출해서 구현했음 (`window_status_widget.py`,
빌더/standalone 양쪽에서 같은 소스 파일 그대로 사용).
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
  지금 활성 틀의 `appData/gvf_state.json`(2026-08-16부터 - 예전엔 레포 루트 고정)에 자동 저장되고
  (각자 다른 키를 써서 서로의 데이터를 안 덮어씀) 재시작 시 복원됨. 실제 데이터/시간 연결, 주기적
  자동 획득, 명령어 실행, 시작/중지/대기열 삭제/loading "시작" 로직은 모두 다음에 이어서 함 (지금은
  값 입력/저장/버튼 이름 토글만 동작)
- **git** — git 위젯 1개 (local/remote 비교·stash 6쌍 + 전체 status check). 6쌍 값도 마찬가지로
  지금 활성 틀의 `appData/git_panel_state.json`에 저장됨
- **wiki** — URL/디렉토리 입력창 + "가져와서 md로 변환" 버튼(웹 문서를 md로 저장, 이미지는 라디오
  버튼으로 자동/claude 분류 선택) + 라디오 버튼 2개
- **윈도우 현황** — 윈도우 현황 위젯 1개 (Windows 버전/CPU/메모리/디스크/휴지통)
- **alarm** — 알람 시계 위젯 1개 (알람 목록도 지금 활성 틀의 `appData/alarm_state.json`에 저장됨,
  2026-08-16부터)
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

## 여백/정렬 관계를 JSON에 선언식으로 기술하는 "anchor" 필드 추가 (2026-08-15)

`future_work_for_poor_developer.md`의 2순위 항목. `builder_state.json`의 위젯 항목에 선택적
`"anchor"` 필드를 추가했다 - 예: `"anchor": {"left": "gvfpanel_1", "right": "fpgaacq_1"}`. 이렇게
선언해두면 `canvas_window.py`의 새 함수 `_apply_anchors(page)`가 탭 복원 직후(각 탭의 위젯을 전부
만든 다음) 한 번 실행되어, 그 위젯의 왼쪽/오른쪽 여백이 참조된 위젯의 같은 쪽 여백과 항상 같아지도록
x(와 필요하면 width까지)를 다시 계산한다. `top`/`bottom`도 동일한 방식으로 y/height에 적용됨.
**왼쪽+오른쪽(또는 위+아래)이 동시에 지정되면 폭(또는 높이) 자체가 두 기준선 사이 간격에 맞게
자동으로 늘어나거나 줄어든다** - 이번 세션에서 gvf 탭 크기를 조정할 때마다 반복됐던 "FPGA loading의
왼쪽 여백을 FPGA 자원 현황과, 오른쪽 여백을 FPGA 자원 취득과 맞춰달라" 패턴을 정확히 이 기능으로
해결함.

페이지 폭/높이를 몰라도 동작하도록 설계함(같은 축의 여백을 서로 빼면 페이지 크기 항이 소거되므로
위젯-대-위젯 앵커는 page.width()/height()가 필요 없음 - 탭이 아직 화면에 그려지기 전이라 이 값들이
부정확할 수 있는 시점에도 안전하게 계산 가능). 실제로 `gvf` 탭의 `fpgaload_1`에 이 앵커를
적용해서(`left: gvfpanel_1, right: fpgaacq_1`) 기존 정적 x/width 값과 정확히 같은 결과(x=8,
width=804)가 나오는 것을 확인했고, `fpgaacq_1`의 위치를 임시로 20px 오른쪽으로 옮겨보는 시뮬레이션
으로 `fpgaload_1`의 JSON을 전혀 건드리지 않아도 오른쪽 가장자리가 자동으로 따라오는 것까지 확인함
(824=832, 832=832 정확히 일치). `_save_state`도 이 필드를 함께 저장/보존하도록 갱신했고, 앵커가
없는 기존 위젯들(이번 세션 내내 만든 모든 탭)은 동작에 전혀 영향 없음을 헤드리스로 재확인함(회귀
없음). 내보내기(`exporter.py`)는 앵커를 모르는 채로 그대로 두었음 - export 시점엔 이미 앵커가
해석된 라이브 좌표(`widget.pos()`/`size()`)를 읽어서 절대값으로 굽기 때문에 별도 대응이 필요 없음
(`instruction` 필드와 같은 성격의 "빌더 전용" 메타데이터).

## 자동 저장(크래시 복구) 추가 (2026-08-15)

`future_work_for_poor_developer.md`의 3순위 항목. 기존엔 `_save_state`가 정상 종료
(`CanvasWindow.closeEvent`)나 "틀 저장" 버튼을 눌렀을 때만 실행돼서, 강제 종료·크래시가 나면 마지막
저장 이후 작업이 전부 사라지는 문제가 있었다.

`CanvasWindow.__init__`에 `QTimer`(90초 간격, `AUTOSAVE_INTERVAL_MS`)를 추가해서
`builder_state.autosave.json`(`AUTOSAVE_STATE_FILE`, `.gitignore`에도 추가함)에 주기적으로 저장한다.
`_save_state`는 `target_file` 인자를 받도록 확장해서 이 두 번째 파일에 쓸 수 있게 됨. 정상
종료(`closeEvent`)는 기존처럼 진짜 `builder_state.json`에 저장한 뒤, 이번엔 이 autosave 파일을 지운다
- 그래서 다음 실행 시 이 파일이 남아있다는 것 자체가 "직전 실행이 비정상 종료됐다"는 신호가 됨.

시작 시점(`CanvasTabs.__init__`)에 새 함수 `_check_and_offer_autosave_recovery()`를 먼저 호출한다 -
autosave 파일이 없으면 조용히 넘어가고(다이얼로그 없음), 있으면 "이전 실행이 정상적으로 종료되지
않았습니다. 복구할까요?" 확인창을 띄워서 예/아니오에 따라 그 내용을 쓸지 기존 `builder_state.json`을
쓸지 결정한다. 어느 쪽이든 확인 후에는 이 autosave 파일을 지워서, 비정상 종료 흔적이 한 번 물어본
뒤에는 다시 안 나타나게 함.

헤드리스로 5가지 시나리오(autosave 없음/복구=예/복구=아니오/타이머로 실제 파일 쓰기/정상 종료 시
정리)를 전부 확인함(`QMessageBox.question`을 패치해서 팝업 없이 예/아니오 분기 검증). 실제
`builder_state.json`을 대상으로도 앱을 재실행해서 autosave 파일이 없을 때 조용히 넘어가는 것까지
확인함.

**발견한 함정**: 이 기능이 생긴 뒤로는, 실제 빌더 앱이 켜져 있는 동안(타이머가 실제
`builder_state.autosave.json`을 주기적으로 만들어냄) 헤드리스 스크립트로 `CanvasWindow()`를 또
생성하면 `_check_and_offer_autosave_recovery()`가 진짜 `QMessageBox.question`을 띄우는데,
`QT_QPA_PLATFORM=offscreen`에서는 클릭할 방법이 없어 그 프로세스가 영원히 멈춰버림(실제로 한 번
겪어서 `TaskStop`으로 정리함). 앞으로 헤드리스 검증 스크립트를 돌릴 땐 실제 앱을 먼저 끄거나, 남아있는
`builder_state.autosave.json`을 먼저 지우거나, `test_autosave.py`처럼 `STATE_FILE`/
`AUTOSAVE_STATE_FILE`을 임시 경로로 monkeypatch해야 함 - memory에도 기록해둠.

## 방향키로 위젯 미세 이동 추가 (2026-08-15)

`future_work_for_poor_developer.md`의 4순위 항목. `CanvasPage.keyPressEvent`에 화살표 키 처리를
추가했다 - 선택된 위젯(들)을 방향키로 1px, Shift+방향키로 10px씩 이동시킨다(`_nudge_selected_widgets`).
마우스 드래그만으로는 1px 단위 정밀 배치가 사실상 불가능해서, 이번 세션 내내 정확한 좌표가 필요할
때마다 `builder_state.json`을 직접 편집해야 했던 문제를 해결함. 기존 드래그 이동과 동일하게 캔버스
경계를 벗어나지 못하도록 클램프 처리함. 다중 선택 상태에서는 선택된 위젯 전부가 같이 움직인다.

헤드리스로 5가지 시나리오(오른쪽 1px 이동/Shift+아래 10px 이동/왼쪽 경계 클램프/오른쪽 경계 클램프/
선택 없을 때 무동작)를 실제 `QKeyEvent`를 만들어 `keyPressEvent`에 직접 전달하는 방식으로 검증함.

이 항목을 검증하다가 자동 저장 기능의 함정(실제 앱이 켜져 있는 동안 헤드리스 스크립트로 또
`CanvasWindow()`를 만들면 복구 확인창에서 멈춤, memory에 이미 기록됨)을 두 번째로 직접 겪음 - 앞으로
헤드리스 검증 전에는 항상 실제 앱을 먼저 끄는 습관을 들임.

## 겹침 순서(z-order) 제어 추가 (2026-08-15)

`future_work_for_poor_developer.md`의 5순위 항목. 위젯 우클릭 메뉴에 **"맨 앞으로"**/**"맨 뒤로"**를
추가했다(`_bring_widget_to_front`/`_send_widget_to_back`, `widget.raise_()`/`lower()` 호출). 지금까지는
위젯이 겹치면 나중에 놓인 게 항상 위였고 바꿀 방법이 없었다.

`entries`가 (Python 3.7+ 딕셔너리의 삽입 순서 보장 특성 덕분에) `_save_state`/`_restore_from_state`
양쪽에서 이미 "위젯이 만들어진 순서 = 겹침 순서"로 취급되고 있었다는 걸 활용해서, 별도 z-index 필드
없이 `raise_()`/`lower()`를 호출할 때마다 `entries` 딕셔너리에서 그 항목을 꺼냈다가 끝(맨 앞으로) 또는
맨 앞(맨 뒤로)에 다시 넣는 것만으로 겹침 순서가 저장/복원에도 그대로 반영되게 함.

헤드리스로 두 가지를 확인함: (1) `entries` 딕셔너리 순서가 예상대로 재배치되는지(3개 위젯으로
맨앞/맨뒤 각각 확인, 없는 id는 무동작), (2) `raise_()`/`lower()`가 실제로 화면 렌더링 순서를 바꾸는지
- 겹치는 두 색상 위젯을 그려서 픽셀을 직접 찍어 파란색→빨간색으로 전환되는 것을 확인함(`QPushButton`
자체 스타일 레이어 때문에 버튼으로 테스트했을 땐 픽셀이 이상하게 나와서, 순수 `QWidget` + 배경색
스타일시트로 다시 테스트해 원인이 z-order 로직이 아니라 버튼 렌더링 쪽임을 확인함).

## 위젯 위치/크기 숫자 직접 입력 추가 (2026-08-15)

`future_work_for_poor_developer.md`의 6순위 항목(포기한 "속성 패널" 5~8시간짜리의 축소판 - 색상/
폰트까지 통합하는 패널 대신 X/Y/폭/높이 입력 하나만). 위젯 우클릭 메뉴에 **"위치/크기..."**를
추가했다(`_edit_widget_geometry`) - 기존 "이름 변경" 다이얼로그와 같은 패턴으로 `QFormLayout` +
`QSpinBox` 4개(X/Y/폭/높이)를 보여주고 Yes/No로 확정한다. 마우스 드래그만으로는 정확한 픽셀에 맞추기
어려워서 이번 세션 내내 `builder_state.json`을 직접 편집해야 했던 문제를 없앰.

적용 시 기존 드래그/방향키 이동과 동일한 규칙으로 보정한다: 폭/높이는 20px 미만으로 못 내려가고
(`_MIN_SIZE`, 리사이즈 핸들 드래그와 동일 기준), X/Y는 캔버스 경계를 벗어나지 않도록 클램프됨(입력한
폭/높이가 반영된 뒤의 경계 기준으로 계산).

헤드리스로 4가지 시나리오를 확인함 - `QDialog.exec`를 패치해서 팝업 없이: (1) 입력값 그대로 적용,
(2) 캔버스 밖으로 나가는 값을 넣었을 때 경계에 맞게 클램프, (3) 취소(No)하면 아무 변화 없음,
(4) 스핀박스 자체의 최솟값이 20으로 설정되어 있는지.

## 정렬 가이드 + 스냅(단순 버전) 추가 (2026-08-15)

`future_work_for_poor_developer.md`의 7순위 항목(제안했던 전체 버전 4~6시간 대신, 가이드선/균등배분
없이 스냅만 있는 축소판 3~4시간짜리로 구현). 드래그 중인 위젯의 가장자리가 다른 위젯이나 캔버스
경계와 3px 이내로 가까워지면 그 값으로 딱 달라붙는다(`_snap_position`, `_SNAP_THRESHOLD = 3`) -
좌우/상하 축을 독립적으로 계산하고, 각 축마다 모든 후보(다른 위젯들의 좌우/상하 가장자리 + 캔버스
자체의 0/너비/높이)를 놓고 이 위젯의 시작 가장자리와 끝 가장자리 중 어느 쪽이든 가장 가까운 후보에
맞춘다.

**이번 세션 전체가 겪었던 병목("여백을 좌우와 같게 해줘" 요청마다 헤드리스로 픽셀을 재고
`builder_state.json`을 손으로 고치던 것)을 가장 직접적으로 줄이는 항목** - 이제 위젯을 마우스로
끌기만 해도 근처 위젯/캔버스 경계에 자동으로 맞춰짐.

기존 `eventFilter`의 드래그 처리(`obj is self._drag_widget`) 안에서, 캔버스 경계 클램프를 마친 뒤에
스냅을 적용하도록 한 줄만 추가해서 끼워 넣었다. 헤드리스로 두 단계에 걸쳐 검증함:
(1) `_snap_position` 자체를 7가지 시나리오(다른 위젯의 오른쪽 가장자리에 왼쪽 붙이기/자기 오른쪽
가장자리를 다른 위젯의 왼쪽에 붙이기/캔버스 좌측·우측 경계에 붙이기/근처에 아무것도 없으면 무변화/
세로축 스냅/임계값 정확히 3px에서는 붙고 4px에서는 안 붙는 경계값)로 단위 테스트함,
(2) 실제 `QMouseEvent`(press→move→release)를 `eventFilter`에 직접 전달하는 통합 테스트로 스냅이 실제
드래그 흐름에도 정확히 반영되는지, 그리고 근처에 아무것도 없는 평범한 드래그는 기존과 똑같이 정확한
위치에 그대로 놓이는지(회귀 없음)까지 확인함.

## 삭제 전용 실행취소(Undo) 추가 (2026-08-15)

`future_work_for_poor_developer.md`의 8순위이자 마지막 항목(전체 Undo/Redo 4~7시간짜리 대신, "위젯
삭제"만 되돌리는 축소판 1~2시간짜리로 구현 - 이동/리사이즈/색상 실수는 손으로 금방 되돌릴 수 있지만,
삭제는 연결된 "동작 설정" 코드까지 통째로 날아가는 게 훨씬 아팠기 때문에 이것만 우선 해결). 완전한
undo/redo 스택이 아니라 **딱 1단계짜리 슬롯**(`self._last_deleted`) - 삭제할 때마다 그 위젯(들)의
전체 데이터(id/kind/좌표/코드/색상/폰트/anchor/라디오 그룹·선택상태까지 전부)를 스냅샷해서 이 슬롯에
저장하고, Ctrl+Z를 누르면 그 스냅샷으로 `restore_widget`을 다시 호출해 **같은 id로** 복원한다(다른
위젯이 `self.<id>`로 참조하던 것도 그대로 다시 맞음). 슬롯은 쓰고 나면 바로 비워지고, 그 사이에 또
삭제가 일어나면 이전 삭제 내용은 덮어써져서 잊혀진다(요청받은 대로 "완전한 스택 불필요").

헤드리스로 6가지 시나리오 확인: (1) 삭제 후 undo가 코드/색상/anchor까지 완전히 복원, (2) undo 후
슬롯이 비어서 두 번째 Ctrl+Z는 무동작, (3) A 삭제 → B 삭제 → undo하면 B만 돌아오고 A는 그대로
잃어버림(단일 슬롯 설계 확인), (4) 아무것도 안 지운 상태에서 undo해도 크래시 없음, (5) 라디오
버튼을 지웠다 되돌리면 그룹 소속과 체크 상태까지 정확히 복원, (6) 여러 개 선택해서 한 번에
지운 뒤 undo하면 전부 같이 돌아오고 다시 선택됨. 추가로 실제 `QKeyEvent`(Ctrl+Z)를
`keyPressEvent`에 전달하는 통합 테스트로 키 바인딩 자체도 확인함.

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

## 레이아웃 템플릿(사각형 컨테이너) 기능 (2026-08-16)

`gvf` 탭처럼 제목 있는 사각형(QGroupBox 틀) 여러 개를 매번 손으로 배치하던 반복 작업을 줄이려고,
팔레트에 "템플릿" 프리셋 6종을 추가하고 캔버스에 **이 앱 최초로 진짜 Qt 부모-자식 포함
(containment) 모델**을 도입했다. 사용자가 요구사항 8개 + 결정 사항 5개(A~E)를 먼저 정하고
(`C:\Users\nulls\.claude\plans\purrfect-knitting-simon.md`에 계획 기록), 4단계로 나눠 각 단계마다
헤드리스 검증 → 실제 앱 재시작 확인 → 사용자 승인 → 커밋+푸시 순서로 진행했다.

**핵심 설계**: 새 `kind`는 `"rect_group"`(QGroupBox) 하나뿐 - 6개 템플릿은 새 kind가 아니라
`rect_group` 1~3개를 미리 정해둔 상대좌표(`layout_templates.py`의 `TEMPLATE_SPECS`, 드롭 시점
캔버스 크기에 대한 비율)에 배치하는 프리셋 데이터일 뿐이다. 모든 위젯 entry에 `parent_id` 필드가
추가되어 컨테이너 소속을 기록하고, `builder_state.json`에도 그대로 저장된다.

**컨테이너 안팎 드래그(요구사항 4, 결정 B)의 핵심 트릭 - "드래그 중엔 항상 페이지로 임시로
끌어올림"**: 컨테이너 자식을 그대로 자기 부모 기준으로 드래그 클램프하면 밖으로 못 빼게 되고,
클램프를 없애면 부모 영역 밖으로 나간 순간 Qt가 그 부분을 그리지 않아 안 보이게 된다. 그래서
드래그가 시작되는 순간(임계값을 실제로 넘는 첫 이동) 위젯을 일단 페이지로 재부모화하고, 드래그가
끝나는 순간(release)에만 최종 위치가 어느 `rect_group` 위인지(z-order 맨 위 우선, 결정 D) 판정해서
그 컨테이너로 다시 자식이 되거나(요구사항 4) 페이지에 남는다(결정 B). 새 팔레트 드롭도 같은 판정
함수(`_container_at`)를 재사용. 이 부분은 실제 `QTest` 마우스 press/move/release 이벤트를
`eventFilter`에 직접 흘려보내는 통합 테스트로 검증했다(내부 메서드를 직접 호출하는 게 아니라 진짜
Qt 이벤트 디스패치 경로를 그대로 태움).

**검증 중 실제로 발견한 버그**: 리사이즈 로직(`_apply_resize`)이 원래 위치(x/y)만 페이지/부모
경계에 클램프하고 **크기(width/height) 자체는 클램프하지 않아서**, 오른쪽 아래 모서리를 끌어
아무리 키워도 막는 게 없었다(기존에도 있던 문제인데, 페이지가 커서 잘 안 보였을 뿐 - 작은
`rect_group` 컨테이너가 생기면서 실제 리사이즈 드래그 테스트로 확 드러남). 크기 자체도 고정된
가장자리를 기준으로 부모 경계를 못 넘게 클램프하도록 고침 - 이것도 실제 QTest 리사이즈 드래그로
재현·수정·재검증했다.

**단계별 요약**:
- **1단계**: 사각형 1개짜리 템플릿만으로 팔레트 드롭 → 컨테이너 생성 → 자식 드래그 인/아웃 →
  캐스케이드 삭제+Undo(결정 A) → 저장/재시작 복원 → standalone 내보내기(exporter.py도 부모 먼저
  emit하는 2-pass로 수정, `QGroupBox` unknown-kind 크래시 방지) → 내보낸 앱 실제 실행까지 끝까지
  검증.
- **2단계**: 복사/붙여넣기 캐스케이드 - 컨테이너를 선택해 복사하면 자식도 같이 복사되어 붙여넣은 새
  컨테이너에 재연결, 자식만 단독 복사하면 평범한 독립 위젯으로 붙여넣어짐(페이지 기준 좌표로 캡처).
- **3단계**: 나머지 5개 템플릿 연결. 6개 미리보기가 한꺼번에 쌓이면서 팔레트 창 자체가
  화면(4221px)보다 커지는 문제를 발견해 `QScrollArea`로 감쌈 + 긴 라벨 word-wrap.
- **4단계**: "선택한 사각형들 정렬"(요구사항 5)/"내부 위젯 정렬"(요구사항 8) 우클릭 메뉴 추가 -
  `layout_templates.equalize_margins` 하나(엣지 종류별 독립 클러스터링, 허용오차 16px, 캔버스/
  컨테이너 경계가 클러스터에 있으면 그 값 우선)를 좌표공간만 바꿔 재사용. 컨테이너의
  자식-bounding-box 최소 크기 제약(결정 C)도 정렬 시 그대로 지켜짐.
- **최종 점검**: 요구사항 3(독립 선택/리사이즈)·6(사각형별 색깔)·7(내부 위젯 수동 이동/리사이즈)이
  1단계의 범용 로직에서 실제로 이미 다 되고 있는지 재확인(새 코드 아님, 확인만).

**알려진 범위 밖(의도적으로 안 건드림)**: 컨테이너 재중첩(사각형 안에 또 사각형) 금지 - 결정 E로
스코프 확정. `anchor` 필드(다른 위젯 기준 여백 자동 유지)는 중첩 자식과 같이 쓰면 좌표계가 섞여서
틀어질 수 있어 이번 범위에서 제외.

## 레이아웃 템플릿 후속: 세로 3개 템플릿 + 체크 박스 + 팔레트 3칸 재구성 (2026-08-16)

5단계 완료 직후 이어진 요청 3건:

- **직사각형 3개(세로) 템플릿 추가**: `layout_templates.py`의 `TEMPLATE_SPECS`에 `"three_stacked"`
  추가 - 기존 "직사각형 3개(가로)"(`three_across`)와 대칭. 이제 템플릿 7종.
- **체크 박스 위젯 추가**: 새 kind `"checkbox"`(`QCheckBox`). 라디오 버튼과 달리 그룹/배타성/
  "첫 옵션 기본 선택" 로직 없이 독립적으로 켜고 끔. 라디오 버튼의 `checked` 상태 저장 로직을
  `entry["kind"] == "radiobutton"` 개별 체크 대신 새 `CHECKABLE_KINDS = ("radiobutton",
  "checkbox")` 상수로 일반화해서 저장/삭제-스냅샷/복사 3곳에 동일하게 적용 - 체크 상태가 저장/
  재시작 복원/복사·붙여넣기/standalone 내보내기 전부에 반영됨. "동작 설정"도 `clicked` 시그널로
  바로 지원(`code_binder.SIGNAL_BY_KIND`에 추가), "이름 변경"은 `QCheckBox`가 이미 `setText`를
  가지고 있어 기존 범용 로직이 자동으로 커버함(별도 분기 불필요).
- **팔레트 세로 3칸 재구성**: 기존엔 템플릿까지 전부 한 세로줄에 쌓여 있었는데, 왼쪽=템플릿 전용/
  가운데=나머지 위젯(체크 박스 포함)/오른쪽=저장 버튼(기존 그대로) 세 칸으로 나눔. 스크롤 영역
  생성 로직을 `make_scrollable_column()` 헬퍼로 뽑아내 왼쪽·가운데 칸 각각에 독립 적용(칸 하나가
  전체 화면 높이를 넘을 수 있는 건 여전해서, 칸별로 각자 스크롤되게 함).

헤드리스로 새 템플릿의 3개 사각형이 위→아래로 겹치지 않게 쌓이는지, 체크 박스의 체크 상태가
저장→재시작 복원/복사·붙여넣기/standalone 내보내기(생성된 소스에 `setChecked(True)` 라인이
찍히고 `py_compile` 통과) 전부에서 유지되는지, 기존 라디오 버튼의 "첫 옵션 기본 선택" 동작이
`CHECKABLE_KINDS` 일반화 이후에도 그대로인지 확인함. 앱을 재시작해서 팔레트가 실제로 3칸으로
나뉘어 보이는 것도 스크린샷으로 확인.

## 정렬 알고리즘 재작업: "비슷한 값끼리 스냅" → "여백 하나로 통일" (2026-08-16)

4단계에서 만든 `equalize_margins`(엣지 종류별로 가까운 값끼리만 스냅하는 클러스터링)가 실제
요구사항과 어긋난다는 지적을 받았다: "사각형이건 사각형 내부 위젯이건 정렬 버튼을 누르면
좌우상하 여백이 동일하도록 해야해"(원래 요구사항 5·8 문구인 "좌우 상하 여백이 모두 일치"를
다시 확인한 것) - 즉 여러 여백값이 서로 "가까우면" 맞춰주는 게 아니라, 캔버스/컨테이너를
둘러싼 좌·우·상·하 여백과 사각형(또는 위젯) 사이 간격 **전부가 하나의 같은 숫자**가 되어야
한다는 뜻이었다. 기존 구현은 이걸 만족 못 함(예: 왼쪽 여백 10px짜리와 위쪽 여백 80px짜리가
있으면 그 둘은 서로 다른 "엣지 종류"라 아예 비교조차 안 되고 각자 따로 스냅됨).

**새 알고리즘**(`layout_templates.py`, `equalize_margins` 전면 재작성):
1. `_cluster_into_rows`로 사각형들을 세로 겹침 기준으로 행(row)으로 묶음(예: "큰 것 1개 위 +
   작은 것 2개 아래"는 자동으로 1행짜리 row + 2행짜리 row로 나뉨 - 깔끔한 격자를 가정하지 않고
   불규칙한 배치도 처리).
2. 지금 상태의 모든 바깥 여백 + 행 사이 간격 + 행 안에서 사각형 사이 간격을 다 모아서 그
   중앙값을 여백 M으로 삼음(사용자가 대충 잡아놓은 크기감을 존중하되 정확한 값으로 통일).
3. 각 행의 자식-bounding-box 최소 크기(결정 C) 제약 하에서 M이 음수 예산을 만들지 않도록
   상한을 계산해 clamp.
4. 세로: 행들의 전체 높이 예산(`outer.height - M*(행수+1)`)을 현재 각 행 높이 비율대로
   나눠서 재배분(전체 높이는 유지, 큰 행이 계속 비례해서 더 크게 유지됨). 가로도 각 행 안에서
   동일하게 사각형 너비 비율대로 재배분.
5. 결과: 위치뿐 아니라 **크기도** 같이 조정되어야만 "모든 여백이 정확히 같은 숫자"가 실제로
   달성됨 - 단순 재배치만으로는 대부분의 경우 불가능해서(현재 크기 합이 우연히 딱 맞아떨어지지
   않는 한), 이번엔 크기 재조정이 알고리즘의 필수 부분이 됨(기존엔 여백이 안 맞으면 위치만 옮기고
   크기는 그대로 뒀었음).

호출부(`canvas_window.py`의 `_align_containers`/`_align_container_children`)는 함수 시그니처가
그대로(`outer_rect, rects, min_sizes`)라 손댈 필요 없었음 - `tolerance` 매개변수만 없어짐.

헤드리스로 5가지 시나리오 검증: (1) 사각형 1개 - 4방향 여백이 전부 똑같이 나옴(중앙 정렬),
(2) 사각형 2개 좌우 배치 - 왼쪽 여백=사이 간격=오른쪽 여백=위 여백=아래 여백 전부 동일, 둘의
top/height도 맞춰짐, (3) "큰 것 1개 + 작은 것 2개" 불규칙 배치 - 바깥 4방향 여백이 전부 같고,
행 사이 간격과 작은 것 둘 사이 간격도 그 여백과 정확히 같은 값, 작은 두 사각형의 top/height도
서로 맞춰짐, 큰 사각형은 존치(0으로 쪼그라들지 않음), (4) 여백 최소 크기 제약이 타이트한 상황에서
결정 C가 여전히 지켜짐, (5) 빈 리스트를 넣어도 크래시 없음. 기존 4단계 테스트 스크립트 중
"비슷한 값끼리만 스냅되고 먼 값은 안 된다"는 옛 동작을 전제로 한 단언 1개는 새 동작(여백이
자동으로 하나의 값으로 통일됨)에 맞게 다시 씀 - 나머지 회귀 테스트 전부 그대로 통과.

## 우클릭 = 선택 + 그룹 선택/이동/일괄 정렬 (2026-08-16)

우클릭이 이제 메뉴를 여는 동시에 그 위젯(또는 사각형의 빈 공간이면 사각형 자체)을 선택 상태로
만든다 - 사각형이든 사각형 안 위젯이든 동일하게 동작(요구사항 1·2). 새 `_apply_selection_click`
헬퍼가 규칙을 담당: 이미 선택돼 있던 위젯을 다시 우클릭하면 그 선택을 그대로 유지하고, 아니면
방금 우클릭한 위젯 하나로 선택을 교체한다 - 단, 메뉴의 새 **"그룹 선택"** 항목을 고르면 교체 대신
**추가**된다(요구사항 3). "이미 선택된 위젯을 다시 우클릭하면 유지" 규칙 덕분에, 2개 이상 모인
그룹 중 하나를 우클릭해도 그룹이 깨지지 않고 그 상태에서 새로 추가된 두 메뉴 항목 **"모든 위젯
상하좌우 크기를 동일하게 함"**/**"모든 위젯의 열을 맞춤"**(요구사항 4, 우클릭한 위젯이 기준값)이
뜬다 - 크기는 폭/높이를 그대로 복사(각자 자기 부모 경계는 넘지 않게 clamp), 열 맞춤은 X좌표만
기준 위젯에 맞추고 Y는 그대로 둔다(왼쪽 가장자리 기준으로 확정 - 처음엔 가운데 정렬 기준도
후보였으나 사용자가 왼쪽 가장자리 기준을 선택함).

**그룹 드래그 이동(요구사항 5)**: `eventFilter`의 기존 "드래그 중엔 페이지로 임시로 끌어올림"
메커니즘(1단계에서 만든 것)을 확장 - 드래그 중인 위젯이 2개 이상 선택된 그룹의 일원이면, 첫
실제 이동 시점에 그룹의 다른 멤버들도 같이 페이지로 끌어올려서 각자의 시작 위치를 스냅샷해두고,
매 프레임마다 주(主) 위젯이 실제로 적용된 최종 delta(스냅/클램프 반영 후)를 나머지 멤버들에게
그대로 적용해서 그룹 전체가 상대 위치를 유지한 채 한 덩어리로 움직인다. 자기 부모가 이미 그룹에
포함된 멤버(예: 컨테이너와 그 자식을 동시에 선택)는 건너뜀 - Qt가 부모를 옮기면 자식은 이미 같이
따라오므로 중복 이동 방지. 마우스를 놓으면 주 위젯뿐 아니라 그룹 멤버 전부 각자
`_resolve_drop_parent`로 최종 컨테이너 소속을 다시 판정함(서로 다른 사각형에 떨어져도 됨).

**검증 중 겪은 함정**: `QMenu.exec()`를 헤드리스로 테스트하려고 `unittest.mock`으로 클래스 메서드를
패치하는 방식과, `QTimer.singleShot`으로 열린 메뉴를 찾아 액션을 트리거하는 방식을 둘 다 시도했으나
`offscreen` QPA 플랫폼에서 `QMenu.exec()`의 중첩 이벤트 루프가 제대로 안 돌아서(팝업 자체가 제대로
안 뜨는 것으로 추정) 두 번 다 무한 대기로 멈춤(테스트 프로세스를 직접 종료해야 했음) - 메뉴 UI를
거치는 대신, 선택 규칙(`_apply_selection_click`)과 실제 동작(`_match_selected_sizes`/
`_match_selected_columns`)을 메뉴 밖에서 직접 호출하는 방식으로 검증 경로를 바꿔서 우회함(이
분리 자체가 프로덕션 코드에도 그대로 반영됨 - 선택 규칙을 별도 메서드로 뽑아내서 메뉴 디스패치
로직과 분리한 게 이번 리팩터). 실제 `QTest` 마우스 드래그로 그룹 이동(두 위젯이 정확히 같은 delta로
이동)과, 선택 안 된 위젯을 드래그했을 때 그 위젯 혼자만 움직이고 기존 그룹은 안 건드리는 것까지
확인함.

## "틀 저장" 눌러야만 저장 + 선택 표시 버그 수정 + 간격 지정/Escape/Ctrl+클릭 (2026-08-16)

바로 앞 세션에서 "빌더 앱 다시 띄워서 드래그해볼게"라며 테스트하다가 gvf 탭이 의도치 않게 망가진
사고가 있었다(다행히 강제 종료로 저장 전에 막음). 그 경험에서 나온 후속 요청 5가지를 처리:

**1. 자동 저장 제거(요구사항 1)**: `CanvasWindow.closeEvent`가 지금까지 무조건 `_save_state`를
불러서 창을 그냥 닫기만 해도 `builder_state.json`을 덮어썼음 - 이게 바로 위 사고의 근본 원인
(망가진 상태로 닫으면 그대로 저장됨). 이제 `closeEvent`는 크래시 복구용 `builder_state.autosave.json`
정리만 하고, 실제 `builder_state.json` 저장은 팔레트의 **"틀 저장" 버튼을 눌렀을 때만** 일어난다.
90초 주기 자동 저장(`_autosave`)은 그대로 유지 - 이건 별도 파일(`builder_state.autosave.json`)에만
쓰고, 크래시 났을 때만 복구 여부를 물어보는 안전망이라 "틀 저장 전엔 저장 안 됨" 원칙과 상충하지
않음.

**2. 그룹 선택 시 파란 점선이 안 보이던 버그(요구사항 2)**: 원인은 z-order - 지금까지 선택 표시는
`CanvasPage.paintEvent`가 직접 그렸는데, Qt는 부모의 paintEvent를 자식보다 먼저 그리기 때문에
사각형(컨테이너) 안에 중첩된 위젯을 선택하면, 페이지가 그린 점선 위에 컨테이너 자신의 배경이
그대로 덮어써서 안 보였음(최상위 위젯은 옆에 아무것도 안 덮는 빈 공간이라 우연히 괜찮아 보였을
뿐). 해결: 점선을 페이지의 paintEvent가 아니라, 항상 맨 위에 떠 있는 별도의 투명 오버레이 위젯
(`_SelectionOverlay`, 마우스 이벤트는 그냥 통과시킴)에서 그리도록 옮김 - 어떤 위젯이 새로 생기거나
z-order가 바뀌어도(`_create_widget`, `_bring_widget_to_front`, 드래그 중 raise_() 등) 항상 다시
맨 위로 올려줌. 실제로 픽셀을 읽어서(`grab()` + `pixelColor`) 중첩된 위젯을 선택했을 때 파란
점선이 실제로 화면에 보이는지, 선택 해제하면 사라지는지까지 확인함(이전엔 이 버그를 코드만 읽어서는
못 잡았을 것 - 실제 렌더링 결과를 픽셀 단위로 봐야 드러나는 종류의 버그였음).

**3. "위젯 간격 지정..." 메뉴(요구사항 3)**: 2개 이상 선택된 상태에서 우클릭하면 뜨는 세 번째 배치
메뉴. 숫자 입력 다이얼로그(기존 "위치/크기..." 패턴 재사용)에서 픽셀 값을 입력하면, 정렬 기능이
쓰는 것과 같은 행(row) 클러스터링(`layout_templates._cluster_into_rows`)으로 위젯들의 배치 구조를
파악한 뒤, 크기는 그대로 두고 위젯 사이 간격만 정확히 그 값이 되도록 재배치함(맨 왼쪽 위 위젯 위치가
기준점, 서로 다른 사각형에 속한 위젯이 섞여 있어도 페이지 좌표 기준으로 계산 후 각자의 부모 기준
좌표로 변환해서 적용).

**4. Escape로 선택 해제(요구사항 4)**: `keyPressEvent`에 한 줄 추가 - 사각형/위젯 구분 없이 동일하게
동작(선택은 애초에 종류 구분 없는 하나의 `_selected_ids` 집합이라 자연히 둘 다 해당).

**5. Ctrl+클릭으로 그룹 선택(요구사항 5)**: `eventFilter`의 `MouseButtonPress` 분기 맨 앞에 Ctrl
모디파이어 체크 추가 - 우클릭 메뉴의 "그룹 선택"과 동일하게 선택에 추가만 하고(교체 아님), 이어서
드래그가 시작되는 것도 막지 않아서 Ctrl+클릭한 채로 바로 끌면 그룹 이동도 됨.

헤드리스로 5개 항목 전부 검증: (1) `closeEvent`/`save_template` 소스에 `_save_state` 호출이 있는지
없는지 직접 읽어서 확인(정적 검사가 딱 맞는 종류의 검증 - "이 코드 경로가 존재하는가"), (2) 위에서
설명한 실제 픽셀 검사, (3) 3개 위젯(2개는 한 행, 1개는 다음 행)에 간격 지정 적용 후 실제 gap이
정확히 지정값과 같은지, 기준 위젯이 안 움직였는지, (4) `QKeyEvent`로 실제 Escape 키 이벤트를
`keyPressEvent`에 전달해서 선택이 비워지는지, (5) Ctrl 모디파이어가 걸린 가짜 마우스 press 이벤트를
`eventFilter`에 직접 전달해서 선택 집합이 확장되는지. 기존 회귀 테스트 11개 스크립트도 전부 다시
통과(`self.update()` 호출부 전체를 `self._refresh_selection_overlay()`로 교체한 리팩터가 기존
동작을 하나도 안 깼는지 재확인).

## Ctrl+클릭이 사각형에서는 그룹 선택이 안 되던 버그 수정 (2026-08-16)

바로 위에서 구현한 "Ctrl+클릭으로 그룹 선택" 기능이 버튼에서는 되는데 **사각형(rect_group,
QGroupBox)에서는 안 된다**는 리포트를 받아 원인을 찾음. `QTest.mouseClick`으로 직접 재현해보니
버튼은 되고 사각형은 계속 실패 - 처음엔 "사각형에는 이벤트 필터 자체가 안 걸리나?"로 의심했는데,
`CanvasPage.eventFilter`를 몽키패치해서 추적하는 방식으로는 사각형에 대해 아예 호출 자체가 안
잡혀서 더 헷갈렸음(나중에 이 추적 방식 자체가 잘못된 단서였다는 게 밝혀짐 - 별도의 새 프로브
필터를 그 자리에서 바로 설치해보니 정상적으로 호출됨, 즉 이벤트 필터 자체는 문제 없었음).

**진짜 원인**: `QGroupBox`는 기본적으로 일반 마우스 눌림을 "받아들이지(accept)" 않는 위젯이다
(`QPushButton`은 자기 클릭 동작을 위해 받아들임). Qt는 자식 위젯이 받아들이지 않은 마우스 이벤트를
부모에게 그대로 전파하는데, `CanvasPage.mousePressEvent`가 Ctrl 여부와 무관하게 왼쪽 버튼 눌림마다
무조건 `self._selected_ids = set()`로 초기화하고 있었다 - 그래서 사각형을 Ctrl+클릭하면: (1)
`eventFilter`가 먼저 실행되어 선택에 정상적으로 추가됨 → (2) 사각형 자신은 이 눌림을 받아들이지
않아서 Qt가 그대로 페이지(부모)로 전파 → (3) `CanvasPage.mousePressEvent`가 방금 추가된 선택을
그대로 지워버림. 버튼은 클릭을 스스로 받아들여서 (2)·(3) 단계 자체가 안 일어나 문제가 없었던 것.

**수정**: `CanvasPage.mousePressEvent`에서 Ctrl이 눌려있으면 선택 초기화와 러버밴드 드래그 준비를
모두 건너뛰도록 함(어차피 "그룹 선택에 추가"가 목적인 클릭이라, 무언가를 지우거나 새로 드래그
선택을 시작할 이유가 없음). 이 처리는 `eventFilter`가 실제로 사각형에 무언가 추가했는지와 무관하게
동작 - 빈 캔버스를 Ctrl+클릭해도 그냥 아무 일도 안 일어남(기존 선택 유지, 러버밴드도 안 뜸), 이것도
합리적인 기본값으로 봄.

헤드리스로 실제 `QTest.mouseClick`(진짜 Qt 이벤트 디스패치 경로, 가짜 이벤트 아님)을 이용해:
사각형→버튼→사각형 순서로 Ctrl+클릭해서 서로 다른 종류가 섞인 그룹이 정상적으로 쌓이는지, Ctrl 없는
일반 클릭은 여전히 사각형에서도 선택을 교체하는지(회귀 없음), 빈 캔버스를 일반 클릭하면 여전히
선택 해제+러버밴드가 시작되는지, 빈 캔버스를 Ctrl+클릭하면 기존 선택이 그대로 유지되고 러버밴드도
안 뜨는지까지 확인함. 기존 회귀 테스트 13개 스크립트 전부 재통과.

## "선택해야만 이동 가능" - 클릭만으로 위치 이동되던 것 막음 (2026-08-16)

지금까지는 선택 여부와 무관하게 아무 위젯이나 왼쪽 버튼으로 누른 채 끌면 바로 이동됐는데, "사각형이건
위젯이건 마우스로 클릭한다고 해서 위치 이동이 되면 안 되고, 반드시 그룹 선택을 하고 나서야 위치
이동이 가능해야 함"이라는 요청으로 이 동작을 바꿨다. `eventFilter`의 `MouseButtonPress`에서 드래그를
준비(`self._drag_widget = obj`)하기 전에 `obj.toolTip() in self._selected_ids` 체크를 추가 - 선택
안 된 위젯은 드래그가 아예 준비되지 않아서 끌어도 안 움직이고, 대신 그 클릭은 평소처럼 위젯
자신에게 전달된다(버튼 클릭·"동작 설정" 핸들러·콤보박스 열기 등은 선택 여부와 무관하게 그대로 동작).
**가장자리를 끄는 리사이즈는 이 제약에서 제외** - 요청이 명시적으로 "위치 이동"만 얘기했고, 리사이즈까지
막으면 오히려 불편해질 뿐이라 그대로 둠.

바로 앞에서 고친 Ctrl+클릭(선택에 추가)은 `MouseButtonPress` 안에서 먼저 실행되므로, Ctrl을 누른 채
누르자마자 그 위젯이 즉시 선택되고 - 뒤이은 같은 손동작으로 계속 끌면(Ctrl+클릭+드래그를 한 번에)
그 즉시 이동까지 된다. 즉 "누르기 전에 미리 선택해두기"뿐 아니라 "Ctrl 누른 채 누르고 바로 끌기"도
여전히 한 동작으로 가능함.

헤드리스에서 실제 `QTest` 드래그로: 선택 안 된 사각형/버튼을 끌어도 안 움직이는지, 우클릭으로
선택한 뒤에는 똑같은 드래그가 실제로 이동시키는지, Ctrl+누르기+바로끌기가 한 번에 되는지,
리사이즈는 선택 여부와 무관하게 여전히 되는지, 선택 안 된 버튼도 "동작 설정" 클릭 핸들러는 여전히
실행되는지까지 확인함. 기존 `phase1_qtest_drag.py`(컨테이너로 자식 드래그해 넣는 테스트)는 이제
드래그 전에 먼저 선택해야 하므로 테스트 스크립트를 새 동작에 맞게 업데이트 - 나머지 회귀 테스트
13개는 그대로 통과.

## gvf 탭 세부 조정: "자동 시간 연장" 체크 박스 + 소유중 버튼/시계 폰트 (2026-08-16)

`gvf_widget.py`(빌더 전용 캔버스 시스템이 아니라 "gvf" 탭에 직접 짜 넣은 합성 위젯 코드) 두 군데
수정:

- **`FpgaAcquisitionPanel`에 "자동 시간 연장" 체크 박스 추가**: "FPGA 획득 마지막 시도" 줄의
  오른쪽 끝에 붙임. "그 아래 줄의 max FPGA 취득과 오른쪽 정렬을 맞춰달라"는 요청 - 두 줄 다
  `addStretch(1)` 다음에 위젯을 하나만 놓아 각자 자기 행의 오른쪽 끝에 딱 붙게 하는 기존
  `interval_row`의 패턴을 그대로 재사용했더니, 같은 `QGroupBox` 콘텐츠 폭/여백을 공유하는 두 행이라
  별도 픽셀 계산 없이 오른쪽 끝이 정확히 일치함(헤드리스로 `mapToGlobal` 기준 diff=0px 확인). 체크
  상태는 다른 입력값들과 같은 방식(`appData/gvf_state.json`의 "acquisition" 키)으로 자동 저장/복원.
- **`GvfPanel`의 소유중 버튼 10% 확장 + 시계 폰트 1px 축소**: "소유중" 버튼만 폭을 10% 늘림(왼쪽
  위치는 그대로, `QHBoxLayout` 안에서 이 위젯 뒤의 "반납" 버튼이 그만큼 밀려남 - "반납" 버튼 자체
  크기는 안 건드림). 시작/종료 디지털 시계 라벨 폰트는 16px→15px로 한 단계 낮춤.

**검증 중 발견한 함정**: 헤드리스로 각 패널을 `resize(397, 250)`(캔버스에 저장된 실제 폭)한 뒤
`sizeHint()`로 여유를 확인했더니 두 패널 다 캔버스 폭을 60~90px 넘는 것으로 나와서 "잘림"을
의심했는데, 실제로 빌더 앱을 재시작해 화면으로 보니 전혀 잘리지 않고 깔끔하게 렌더링됨 - `QVBoxLayout`이
붙은 위젯은 Qt가 그 레이아웃의 최소 필요 크기보다 작게 강제로 줄이는 걸 허용하지 않아서, 저장된
`width` 값보다 실제 렌더링 폭이 자연스럽게 조금 더 커진 것뿐이었음(주변에 여유 공간이 있어서 다른
요소와 안 겹침). `sizeHint()` 기반 자동 검사만으로는 이 케이스를 정확히 판단할 수 없어서, 최종
판단은 실제 스크린샷으로 함 - "실제 앱을 켜서 확인해야 한다"는 원칙이 다시 한 번 유효했던 사례.

## gvf 탭 세부 조정 2차: 시계 폰트 한 단계 더, 라디오 열 간격 50%, 시작 버튼은 보류 (2026-08-16)

- **시작/종료 디지털 시계 폰트 한 단계 더 축소**: 바로 위에서 16px→15px로 낮춘 데 이어 15px→14px로
  한 번 더 낮춤(누적 -2px).
- **FPGA loading의 라디오 버튼 열 사이 가로 간격 50% 확대**: `row.setSpacing(29)` → `44`(반올림).
- **시작 버튼 세로 2배(자연 크기 6배→12배) 요청은 보류**: 실제로 적용해보니(코드 자체는
  정상 반영, `setFixedSize`로 실측 240x240까지 정확히 커짐) 캔버스에 남은 세로 공간이 부족해서
  버튼이 화면에서 잘려 보임 - 창 크기(`builder_state.json`의 `window.height`)는 사용자가 직접
  요청하지 않는 한 안 바꾼다는 원칙이 있어서, 적용 전에 사용자에게 확인함(창을 늘릴지/다른 요소를
  줄여서 공간을 만들지/일단 잘린 채로 둘지). **"버튼 크기는 그냥 놔둬"**로 답변받아 기존 6배로
  되돌림 - 코드에는 시도했던 배율과 되돌린 이유를 주석으로 남겨둠.

이번에도 `appData/gvf_state.json`에 저장된 "자동 시간 연장" 체크 상태가 어느 시점엔가 `true`로
바뀌어 있는 걸 발견했는데(내 테스트 스크립트는 전부 임시 파일로 리다이렉트해서 이 파일을 직접 건드릴
방법이 없었음 - 정확한 원인은 못 찾음), 사용자가 그 사이 직접 눌렀을 가능성을 배제할 수 없어서
실사용 데이터를 추측만으로 덮어쓰지 않고 그대로 둠.

## 위젯 팔레트 1.5배 확대 + 템플릿 드롭 시 자동 여백 정렬 + 이름/폰트 변경 시 크기 변경 버그 수정 (2026-08-16)

- **위젯 팔레트 세로 길이 1.5배**: `palette_window.py`의 `max_column_height` 산식(`(화면 높이-120)*1.5`)
  자체는 처음부터 맞았지만, 실제 창 크기에는 전혀 반영되지 않는 버그가 있었다 — `QScrollArea.sizeHint()`는
  내용이나 `maximumHeight()`와 무관하게 거의 고정값(~384px)을 반환하고, 이 값만 부모 `QHBoxLayout`의
  창 크기 계산에 쓰였기 때문에 `setMaximumHeight`만으로는 창이 커질 일이 없었다(빈 진단 스크립트로
  직접 확인). `setMinimumHeight`도 같은 값으로 같이 걸어줘야 그 값이 부모 레이아웃의 sizeHint 계산에
  반영된다는 걸 확인하고 수정 — 이제 팔레트 창 sizeHint가 실제로 1329px(기존 산식의 1.5배) 근처로
  나옴(`make_scrollable_column` 안, 두 스크롤 컬럼 모두 적용).
- **템플릿 드래그&드롭 시 여백 자동 정렬**: `canvas_window._drop_template`이 템플릿의 사각형들을
  다 만든 뒤 곧바로 `_align_containers`(기존 "선택한 사각형들 정렬" 메뉴가 쓰던 것과 동일 로직)를
  호출하도록 변경 — 이제 드롭 직후부터 캔버스 여백/사각형 사이 간격이 전부 하나의 값으로 맞춰진
  상태로 놓인다(반올림 오차로 어긋나던 것 포함).
- **버그 수정 — 위젯 이름/폰트를 바꾸면 크기가 같이 바뀌던 문제**: `_rename_widget`/`_pick_widget_font`가
  `setText`/`setFont` 뒤에 `widget.adjustSize()`를 호출하고 있어서, 예를 들어 버튼 텍스트를 길게/짧게
  바꾸거나 폰트 크기를 키우면 그 새 sizeHint에 맞춰 버튼 크기 자체가 같이 변해버렸다(위치/크기는
  드래그나 "위치/크기..." 입력으로만 바뀌어야 한다는 원칙 위반). 두 곳 모두 `adjustSize()` 호출을
  제거 — 이제 이름/폰트를 바꿔도 크기·위치는 그대로 유지된다. 색깔 변경(`_pick_widget_color`)과
  동작 설정(`_open_behavior_dialog`)은 애초에 이 문제가 없었음(코드 확인함).
- 화면 스크린샷으로 팔레트 창 확인을 시도했으나, 이 세션 환경에서 새로 띄운 `pythonw.exe`/`python.exe`
  프로세스가 전부 `python3xx.dll`조차 로드하지 못한 채(윈도우 하나도 못 만든 채) 멈춰 있는 현상을
  발견함 — 기존에 떠 있던 프로세스(PID 1316, 훨씬 전부터 실행 중이던 것)도 동일한 상태였음. 이 세션의
  프로세스 실행 환경 자체 문제로 보이며(코드 문제가 아님), 이번 검증은 헤드리스 Qt 진단(`sizeHint`/
  `minimumHeight`/`maximumHeight` 직접 조회)으로 대체함 - 다음에 이어서 할 때 실제 화면으로 한 번
  재확인 필요.

## 팔레트 세로 크기조절 잠김 버그 수정 + 템플릿 썸네일 70% 축소 (2026-08-16)

- **버그 수정 — 팔레트 창을 위쪽 가장자리로 크기조절할 수 없던 문제**: 바로 위 항목("팔레트 1.5배
  확대")에서 `QScrollArea`마다 `setMinimumHeight(max_column_height)`를 **영구적으로** 걸어둔 게
  원인이었다 — `maximumHeight`와 같은 값으로 최소/최대가 동시에 고정되면 Qt/Windows가 그 축의
  드래그 크기조절 자체를 비활성화한다(그래서 창 테두리를 잡아도 커서가 안 바뀌고 안 움직였음).
  수정: `__init__` 끝에서 딱 한 번, 원하는 초기 크기를 만들기 위해 `minimumHeight`를 잠깐
  `max_column_height`로 걸었다가 `self.resize(self.sizeHint())`로 그 크기를 창에 확정 적용한
  직후 바로 `setMinimumHeight(0)`으로 풀어준다 - 시작할 때는 여전히 1.5배 크기로 뜨지만, 그 뒤로는
  위/아래/전체 어느 가장자리로든 자유롭게 다시 크기조절할 수 있다. 헤드리스로 `minimumSizeHint()`와
  `maximumHeight()`가 더 이상 같은 값이 아님을 확인(`phase14_palette_resizable_and_template_size.py`),
  실제 앱 스크린샷으로도 재확인함.
- **템플릿 썸네일 크기 70%로 축소**: `DraggableTemplate`의 고정 크기(가로 194×세로 90 → 가로
  136×세로 63, 반올림)만 줄였다 - 다른 팔레트 항목들이 공유하는 `ITEM_WIDTH`(194)는 그대로 둬서
  드롭박스/버튼/입력창 등 나머지 항목 폭에는 영향 없음. 미리보기 사각형은 `paintEvent`가 위젯
  크기에 대한 비율로 그리므로 별도 좌표 수정 없이 자동으로 비례 축소됨.

## 팔레트에 템플릿 전용 칸 하나 더 추가 (2026-08-16)

템플릿 7개가 세로 한 칸에 다 들어있어 스크롤이 잦았다는 피드백으로, 템플릿 칸을 하나 더 늘려
2칸으로 나눴다(`make_scrollable_column()`을 두 번 호출해 `template_scroll_a`/`template_scroll_b`
생성, `TEMPLATE_SPECS`를 앞 4개/뒤 3개로 절반씩 나눠 각각에 채움). 팔레트는 이제 왼쪽부터
템플릿1 / 템플릿2 / 나머지 위젯 / 저장 버튼, 총 4칸. 반복되던 구분선 생성 코드는
`add_vertical_divider()` 헬퍼로 정리. 헤드리스 테스트(`phase15_two_template_columns.py`)와 실제
앱 스크린샷으로 7개 템플릿이 4/3으로 나뉘어 스크롤 없이 거의 다 보이는 것 확인함.

## 팔레트 시작 크기를 사용자가 직접 조정한 크기로 고정 (2026-08-16)

팔레트 위쪽 가장자리 크기조절이 가능해진 뒤 사용자가 직접 편한 크기로 줄여봤고, "그 크기를 기본값으로
쓰자"는 요청을 받음. 실제 창을 GetClientRect(단, 이 크기를 재는 PowerShell 프로세스 자체가
DPI-unaware라 Windows가 좌표를 이미 96 DPI 기준으로 가상화해서 돌려줌 - 별도 DPI 배율 계산 없이 그
값 그대로가 Qt 논리 픽셀과 일치함, "나만의 tool" 창을 같은 방식으로 재서 `builder_state.json`에 저장된
820×499와 정확히 일치하는 것으로 검증함)로 측정한 값 897×845(가로×세로)를 `palette_window.py`의
`DEFAULT_WIDTH`/`DEFAULT_HEIGHT` 상수로 못박았다. 기존에 있던 "화면 높이 기반 1.5배 공식 +
minimumHeight 임시 고정 후 해제" 트릭은 완전히 제거하고 `self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)`
한 줄로 단순화함 - `max_column_height`(화면 기반 1.5배 공식)는 그대로 남겨뒀지만 이제 창의 시작
크기와는 무관하고, 나중에 사용자가 창을 더 크게 늘렸을 때 각 스크롤 칸이 무한정 커지지 않도록 막는
상한선 역할만 한다. 실제 앱 재시작 후 측정해서 897×845로 정확히 뜨는 것 확인함.

## 그룹 선택 후 좌우 화살표 이동 안 되던 버그 수정 + 팔레트 열 너비 80% 축소 (2026-08-16)

- **버그 수정 — 그룹 선택 후 화살표 좌우 이동이 안 되던 문제**: 원인은 오른쪽/Ctrl+클릭으로 위젯을
  선택해도 키보드 포커스가 페이지로 넘어오지 않고 마지막으로 포커스를 가졌던 위젯(예: `QLineEdit`류)에
  그대로 남아 있었기 때문. 포커스가 `QLineEdit`에 있으면 좌우 화살표는 그 위젯이 자기 텍스트 커서를
  옮기는 데 써버려서(소비) `CanvasPage`까지 안 올라오지만, 상하 화살표는 한 줄짜리 입력창이 아무것도
  안 하고 그냥 흘려보내서(bubble up) `CanvasPage.keyPressEvent`까지 도달해 정상 동작했던 것 — "상하는
  되는데 좌우만 안 됨"이 정확히 이 비대칭에서 나온 증상이었음. 두 갈래로 수정:
  1. `_apply_selection_click`(우클릭 선택의 실제 효과) 맨 앞에 `self.setFocus()` 추가 - 우클릭으로
     선택할 때마다 페이지가 포커스를 다시 가져감.
  2. `eventFilter`에 화살표 키 가로채기 추가 - 선택된 게 하나라도 있으면, 어느 자식 위젯이 포커스를
     들고 있든 상관없이(1번이 놓친 경우까지 포함) 화살표 키를 페이지의 `_nudge_selected_widgets`로
     바로 넘기고 그 자식 위젯 자신의 처리를 막음. 모든 배치된 위젯은 이미 `self`(페이지)를
     `installEventFilter`로 걸어둔 상태라 별도 배선 없이 바로 적용됨.
  - 선택된 게 하나도 없을 때는 이 가로채기가 발동하지 않으므로, 평소 텍스트박스에서 화살표로 커서
    옮기는 동작은 그대로 유지됨(헤드리스 테스트로 확인).
- **팔레트 각 열 너비 80%로 축소**: `ITEM_WIDTH`를 194 → `round(194 * 0.8)` = 155로 변경. 드롭박스/
  버튼/입력창/저장 버튼 등 이 상수를 공유하는 모든 항목과, 여기서 파생되는 템플릿 썸네일
  (`DraggableTemplate.PREVIEW_WIDTH = round(ITEM_WIDTH * 0.7)`)까지 자동으로 비례 축소됨. 팔레트
  창 자체의 너비(`DEFAULT_WIDTH`)는 바로 위 항목에서 사용자가 직접 맞춘 값이라 이번엔 손대지 않아서,
  창 오른쪽에 여백이 좀 더 생긴 채로 열들만 좁아진 모습(스크린샷으로 확인).
- 헤드리스 테스트(`phase16_arrow_nudge_horizontal_fix.py`) 19개 스크립트 전부 통과, 실제 앱
  스크린샷으로 팔레트 열 너비 축소 확인.
- **팔레트 기본 크기 재조정**: 열 너비를 줄인 뒤 사용자가 팔레트 창 자체도 다시 수동으로 조정했고,
  그 크기(723×834)를 `DEFAULT_WIDTH`/`DEFAULT_HEIGHT`로 다시 캡처해서 반영함(이전 897×845에서
  갱신). 재시작 후 정확히 723×834로 뜨는 것 확인.

## "설명" 탭 텍스트 보강 + 실습 예제 문서 추가 (2026-08-16)

- **`app_overview_text`/`tab_usage_text` 대폭 보강** (`code_binder.py`, `exporter.py`의 동일 로직
  둘 다 수정 - 후자는 standalone 내보내기용 문자열 템플릿이라 따로 유지보수해야 함, 두 파일 다르게
  건드릴 때 주의):
  - 전체 앱 설명: 탭별로 위젯 종류별 개수 breakdown("버튼 2개, 체크 박스 1개, ..."), 앱 전체 위젯
    수, 그중 클릭 등 동작이 연결된 위젯 수까지 표시하도록 확장.
  - 탭별 설명: 템플릿 사각형(컨테이너) 안에 들어있는 위젯들을 부모-자식 관계(`parent_id`)를 따라
    들여쓰기로 중첩 표시(이전엔 flat 목록이라 어떤 위젯이 어느 사각형 안에 있는지 안 보였음), 체크
    박스/라디오 버튼의 현재 체크 상태("(체크됨)"/"(체크 안 됨)") 표시, 위젯에 지정된 색깔 표시.
  - `checkbox`/`rect_group`/`gvfpanel`/`fpgaacquisition`/`fpgaloading` kind가 라벨 매핑에 아예
    빠져있던 것도 이번에 발견해서 채움(이전엔 raw kind 문자열이나 빈 설명으로 나왔음). gvf 3패널
    설명은 현재 실제 구현(자동 시간 연장 체크박스, 소유중/반납 버튼, 시작/중지 텍스트 전환 등)에
    맞춰 다시 씀 - 예전 "뼈대 상태" 문구가 남아있었음.
  - **버그 발견 겸 수정**: standalone으로 내보낸 앱은 런타임에 빌더의 `entries` 메타데이터가 없어서
    (`hasattr(tab_page, "entries")`가 항상 False) 실제로는 `_describe_page_widgets`(단순 fallback)만
    타는데, 이 함수가 캔버스 페이지의 **직계 자식만** 보고 있어서 템플릿 사각형 **안에 든 위젯들이
    통째로 설명에서 빠지는** 문제가 있었음(내보낸 앱을 직접 실행해서 재현 확인). `_describe_one_widget`로
    분리하고 `QGroupBox`의 직계 자식을 한 단계 더 들여다보도록 고쳐서 해결 - 사각형 재중첩 금지
    규칙(결정 E) 덕분에 딱 한 단계만 더 보면 충분함. `QGroupBox.title()`/`QComboBox.currentText()`도
    이번에 같이 채움(전엔 `.text()`만 봐서 둘 다 빈 텍스트로 나왔음).
  - 헤드리스로 검증: 빌더 쪽은 `phase17_explain_tab_detail.py`, exporter.py 쪽은 실제로
    `generate_source`로 만든 소스를 `exec`해서 진짜 뜬 `GeneratedApp` 인스턴스에 대고
    `app_overview_text`/`tab_usage_text`를 직접 호출해 확인하는 `phase18_export_explain_tab_detail.py`
    (컴파일만 확인하는 것보다 훨씬 신뢰도 높음 - 실제로 이 방식으로 위 버그를 발견함).
- **`how_to_use.md`에 "13. 실습 예제" 절 추가**: 새 탭 만들기(탭바 빈 공간 우클릭) → 템플릿 드래그 →
  이름 변경 → URL 입력창/버튼을 사각형 안에 채워 넣기 → 자연어로 "열기" 버튼에 동작 연결(URL 입력창
  값을 `open_url`로 열기) → 틀 저장 → `.py`/`.exe` 내보내기 → 내보낸 결과물 실행 확인까지, 마우스
  왼쪽/오른쪽 클릭과 정확한 메뉴 항목 이름까지 단계별로 서술. 처음 쓰는 사람이 그대로 따라 하면
  실제로 동작하는 최소 도구 하나를 처음부터 끝까지 완성해볼 수 있도록 함.

## "설명" 탭 "예제" 버튼 복사-붙여넣기 버그 수정 (2026-08-16)

사용자 실사용 데이터(`builder_state.json`)의 "설명" 탭에 이미 있던 `button_5`("예제", 주황색)가
`button_3`("각 탭에 대한 설명")과 `instruction`/`code`가 완전히 똑같이 복사되어 있어서, 둘 다
`tab_usage_text(self)`를 호출해 같은 메시지가 뜨던 버그를 발견/수정함(복사-붙여넣기 흔적으로 보임 -
이 두 버튼은 내가 만든 게 아니라 이미 저장돼 있던 사용자 데이터였음). `button_5`의 `code`를 새로
작성해서, 이제 "새 탭 만드는 방법"(탭바 빈 공간 우클릭 → 즉시 새 탭 생성 → 탭 이름 편집 → 위젯/템플릿
드래그로 채우기 → 우클릭으로 이름/동작/색깔 설정 → 틀 저장) 6단계 안내를 보여주는 별도 메시지가 뜬다.
헤드리스로 `compile_handler`를 실제 실행해서 `show_text_dialog` 호출 내용이 달라졌음을 확인했고
(`phase19_explain_tab_example_button.py`), 사용자 승인 받은 뒤 앱을 재시작해서 실제 마우스 클릭으로
"설명" 탭 → "예제" 버튼을 눌러 새 다이얼로그가 뜨는 것까지 스크린샷으로 확인함.

## "예제" 버튼 내용 대폭 보강 (웹사이트 링크 예제 + 그룹 선택/이동/동작 설정 상세 설명) (2026-08-16)

사용자가 버튼 라벨을 직접 "예제 : 새 탭 만들어 저장하는 법"으로 바꾼 뒤, 내용이 "너무 성의 없다"며
그룹 선택하는 법·위치 이동하는 법·버튼 동작 지시하는 법을 웹사이트 링크 여는 도구를 예로 들어 상세히
써달라고 요청함. `builder_state.json`의 `button_5["code"]`를 6단계(새 탭 만들기 → 템플릿으로 틀 잡기
→ 위젯 채우기)에서 훨씬 긴 내용으로 재작성: 새 탭 만들기 / 템플릿 드래그 / 위젯 채우기(URL 입력창 +
버튼) / **위치 이동하는 법**(선택 후에만 드래그 가능, 위치/크기... 숫자 입력, 방향키 1px·Shift+방향키
10px, 3px 스냅) / **그룹 선택**(우클릭 → 그룹 선택 메뉴, Ctrl+클릭, 그룹째 이동, 그룹 대상 일괄
정렬 메뉴, Escape로 해제) / **버튼 동작 설정**(동작 설정... → 자연어 입력 → 생성 → 코드 확인 →
저장(위젯에 연결) 순서, `open_url(self.urlbox_1.text())` 예시) / 틀 저장, 총 7개 섹션.

**작업 중 발견한 도구 사용 실수(교훈으로 기록)**: `Edit` 툴로 이 파일의 긴 한글 문자열을 직접
편집하다가 끝부분에 `\")\"` 처럼 여분의 이스케이프 문자가 섞여 들어가 `code` 필드가 문법 오류
상태가 된 적이 있었음 - 이후 `python -c` 로 파일을 다시 읽어 확인하는 과정에서 "윈도우 현황"/
"설명" 같은 멀쩡한 필드까지 `Bash` 툴의 터미널 출력이 깨져 보여서(`윈도우` 같은 실제
코드포인트를 직접 찍어 확인해서 실제로는 파일이 정상이었음을 뒤늦게 확인함 - `repr()`/`ord()`로
코드포인트를 직접 찍어보거나 처음부터 PowerShell로 확인했으면 바로 알 수 있었음) 마치 파일 전체가
깨진 것처럼 보여 한동안 잘못된 진단(전체 파일 인코딩 손상)으로 시간을 썼음. 최종적으로는: (1) 아직
살아있던 빌더 앱의 "틀 저장"을 다시 눌러서 그 시점 메모리의 정상 상태로 파일을 덮어써 문법 오류를
원상복구하고, (2) 새 내용은 `json.load`/`json.dump`(둘 다 `encoding="utf-8"`, `_save_state`가 쓰는
것과 동일한 방식)로 직접 조작하는 파이썬 스크립트로만 다시 적용해서 `Edit` 툴로 긴 한글 문자열을
다시 손으로 이스케이프하는 걸 피함. 이후 회귀 테스트 22개 전부 통과, 앱 재시작 후 실제 클릭으로
새 내용이 뜨는 것까지 스크린샷 확인.

## Ctrl+Z 되돌리기 범위 확장: 삭제만 → 이동/크기/색깔/이름/폰트/동작 설정/일괄 정렬까지 (2026-08-16)

사용자가 이 앱의 문제점으로 "수정할 때마다 이전 설정이 저장 안 됨"을 지적 - 구체적으로 4가지: (1) "틀
저장"을 안 누르고 앱이 닫히면 세션 전체가 날아감, (2) "동작 설정" 창에서 다른 위젯을 편집하면 이전
편집 내용이 사라짐, (3) **잘못 설정한 걸 되돌리기가 안 됨** (지금까지 Ctrl+Z는 삭제만 취소 가능),
(4) 완전히 처음부터 시작하고 싶어도 그렇게 할 수 없음. 이 중 (3)을 "좁은 범위"(여러 단계 undo/redo
스택이 아니라, 지금처럼 딱 1단계만 기억하되 편집 종류를 넓히는 것)로 먼저 구현함 - (1)/(2)/(4)는
아직 미착수.

- **설계**: 기존 `_last_deleted`(삭제 전용 스냅샷)를 `_last_action = {"type": "delete"|"edit",
  "entries": [...]}`으로 일반화. `_snapshot_entry(widget_id)`가 위젯 하나의 전체 상태(위치/크기/
  텍스트/색깔/폰트/instruction+code/checked/parent_id 등)를 캡처하는 공통 헬퍼 - delete/edit 두
  타입이 같은 스냅샷 모양을 공유함. "edit" 타입은 위젯을 다시 만드는 대신(`restore_widget`) **살아있는
  같은 위젯 인스턴스에 값을 그대로 되돌려 씀**(`_restore_entry_in_place`) - 이동/크기조절/색깔/이름/
  폰트/동작 코드는 부모가 안 바뀌는 편집이라 이 방식이 훨씬 단순함.
- **적용 범위**: 이동(드래그, 그룹 드래그 포함) / 크기조절(드래그) / "이름 변경" / "색깔 변경" /
  "폰트 설정" / "동작 설정..." 저장 / "위치/크기..." 숫자 입력 / "선택한 사각형들 정렬" / "내부 위젯
  정렬" / "모든 위젯 상하좌우 크기를 동일하게 함" / "모든 위젯의 열을 맞춤" / "위젯 간격 지정...".
  드래그의 경우 스냅샷을 **컨테이너 자식이 드래그 중 페이지로 임시로 들어 올려지기 전** 시점에 찍어야
  원래 부모/로컬 좌표로 정확히 복원됨 - 실제로 이동이 일어났을 때만(`was_dragged`)/크기가 실제로
  바뀌었을 때만 되돌리기 슬롯에 커밋해서, 그냥 클릭만 하고 끝난 경우 undo 슬롯을 헛되이 덮어쓰지
  않도록 함.
- **일부러 뺀 것**: 방향키 미세 이동(1px/10px)은 추적 안 함(반대 방향키로 바로 고치는 게 더 빠르고,
  추적하면 진짜 편집의 undo 슬롯을 자꾸 덮어써서 오히려 방해가 됨), 템플릿 드롭 직후 자동 정렬(막
  만든 위젯이라 마음에 안 들면 그냥 지우는 게 더 자연스러움), z-order(맨 앞/뒤)·라디오 옵션 추가/
  제거·테두리 없애기(되돌리는 것보다 반대 동작을 다시 누르는 게 더 빠른 사소한 토글들).
- 헤드리스 테스트(`phase20_broad_undo.py`, 23개 체크) - 실제 `QTest` 마우스 드래그로 이동/크기조절
  undo까지 검증(가짜 이벤트가 아니라 진짜 Qt 이벤트 경로를 태움), "동작 설정"은 실제
  `compile_handler`/`bind_handler` 왕복까지 확인, 여러 위젯 일괄 크기맞춤(`_match_selected_sizes`)
  undo도 확인, 그리고 "최근 작업 하나만 기억함"(A를 옮기고 B를 옮기면 A의 이동은 그대로 남음) 원칙도
  확인. `how_to_use.md`의 Ctrl+Z 설명도 갱신.

## "다른 이름으로 저장"/"저장된 틀 불러오기" 추가 (여러 개의 틀 관리) (2026-08-16)

사용자가 남은 4번 항목("완전히 처음부터 시작하기")을 구체화: 단순 초기화보다는 "지금 틀을 이름
붙여서 저장하고, 나중에 여러 틀 중 골라서 불러오는" 기능을 원함(1·2번 항목은 이번엔 필요 없다고
확인받음). "회사용"/"집용"처럼 서로 다른 탭 구성을 왔다 갔다 하는 용도.

- **저장 형식**: 기존 `builder_state.json`과 완전히 같은 JSON 스키마. `appData/layouts/<이름>.json`에
  하나씩 저장(이름 = 파일명, `\/:*?"<>|`와 제어문자는 자동으로 제거됨(`_sanitize_layout_name`) -
  Windows 파일명에 못 쓰는 문자라서).
- **"다른 이름으로 저장"**(`CanvasWindow.save_layout_as`): 이름 입력 → 이미 있으면 덮어쓸지 확인 →
  기존 `_save_state`를 그 경로로 재사용해서 저장. **`STATE_FILE`(=`builder_state.json`, 앱 시작 시
  자동으로 뜨는 그 파일)은 절대 건드리지 않음** - "틀 저장"과 완전히 독립된 별개 슬롯.
  `_save_state`가 이미 `target_file` 매개변수를 받게 설계돼 있어서(원래 자동저장용으로 쓰던 것)
  거의 그대로 재사용함.
- **"저장된 틀 불러오기"**(`CanvasWindow.load_layout_dialog`): `appData/layouts/`의 `.json` 파일
  목록을 드롭다운으로 보여줌(하나도 없으면 안내만 뜸) → 고르면 확인창("지금 화면 내용은 틀 저장을
  안 눌렀으면 사라짐") → `CanvasTabs.load_state(state)`가 **지금 열려 있는 탭을 전부 지우고**
  (`removeTab(0)` + `deleteLater()` + `remove_tab_color(0)` 반복 - 기존 "탭 삭제" 로직과 동일한
  방식) 불러온 state로 다시 채움(기존 `_restore_from_state`를 그대로 재사용, 이건 원래 "빈
  CanvasTabs에 처음 한 번만" 호출되던 걸 재사용 가능하게 확인함). 불러온 뒤에도 `STATE_FILE`은 안
  바뀌므로, 다음 실행에도 이 틀로 시작하게 하려면 불러온 다음 "틀 저장"을 따로 눌러야 함(문서에
  명시).
- 팔레트 오른쪽 칸에 "틀 저장" 바로 아래 두 버튼 추가 (틀 저장 / 다른 이름으로 저장 / 저장된 틀
  불러오기 / 실행 py 저장 / standalone 실행 파일 저장 순서).
- 헤드리스 테스트(`phase21_named_layouts.py`, 14개 체크) - 이름 sanitize, 저장 시 `STATE_FILE` 안
  건드리는지, 덮어쓰기 확인창이 실제로 뜨는지, 불러오기가 실제로 탭을 통째로 교체하는지(불러오기
  직전에 탭 개수/제목/위젯 텍스트를 일부러 바꿔놓고 불러온 뒤 저장된 값으로 되돌아오는지 확인),
  저장된 틀이 하나도 없을 때 안내만 뜨고 죽지 않는지까지 확인.
  - **테스트 작성 중 겪은 문제(교훈)**: 헤드리스 테스트가 출력 하나 없이 무한 행(hang)됐는데, 원인은
    `save_layout_as`가 끝에서 실제 `QMessageBox.information("저장 완료", ...)` 팝업을 띄우는
    부분을 mock 안 하고 놓쳤던 것 - `QInputDialog.getText`/`QMessageBox.question`만 mock하고
    이건 빠뜨림. offscreen 플랫폼에서는 이런 실제 팝업의 `.exec()`가 영원히 안 풀림. `[[feedback-
    autosave-test-hang]]` 메모리에 이 일반화된 교훈(테스트 대상 메서드가 보여주는 팝업을 전부
    빠짐없이 mock해야 함, 안 그러면 아무 출력도 없이 그냥 멈춤) 추가해둠.

## "standalone 실행 파일 저장" 버튼 2줄 + 세로로 늘리기 (2026-08-16)

팔레트의 "standalone 실행 파일 저장" 버튼 라벨을 `"standalone\n실행 파일 저장"`(2줄)로 바꾸고
`setFixedHeight(70)`으로 세로로 늘림(다른 저장 버튼들보다 눈에 띄게 크게). 빌드 중/완료 후 라벨을
되돌리는 `canvas_window.py`의 `_on_exe_build_finished`도 같은 2줄 문자열로 맞춰야 했음 - 안 그러면
빌드 한 번 끝날 때마다 버튼이 다시 1줄짜리 원래 텍스트로(높이는 `setFixedHeight`라 유지되지만 글자만)
되돌아갈 뻔함. 헤드리스로 버튼 텍스트/높이와 두 파일의 문자열이 정확히 일치하는지 확인
(`phase22_exe_button_two_lines.py`), 실제 앱 스크린샷(클릭 없이 순수 캡처만 - 사용자가 화면을 같이
쓰고 있어서 이번엔 자동 클릭 테스트를 하지 않음)으로 2줄 표시와 커진 높이 확인.

## `builder_framework/` 폴더 재구성 + 팔레트 크기 저장 + "새 틀 시작하기" (2026-08-16)

바로 위 항목("다른 이름으로 저장"/"저장된 틀 불러오기")에서 쓰던 `appData/layouts/<이름>.json`
플랫 파일 방식을, 사용자 제안으로 폴더 기반 구조로 다시 정리함. 이어서 두 가지를 추가 확인/구현:
팔레트 창 크기가 어디에도 저장 안 되고 있던 빠진 부분("팔레트도 쓰다 보면 바뀌는데 저장 안 되는 게
맞나?"라는 사용자 지적으로 발견), 그리고 "새 틀 시작하기" 버튼.

- **`builder_framework/` 구조**: `BUILDER_FRAMEWORK_DIR = <빌더>/builder_framework/`,
  기본 틀은 `builder_framework/default/builder_state.json`(`STATE_FILE`), 이름 있는 틀은
  `builder_framework/<이름>/builder_state.json`(`_named_layout_state_path`) — default와 이름
  폴더들이 형제 관계로 나란히 있음. "실행 py 저장"/"standalone 실행 파일 저장"의 기본 저장 위치
  (`EXECUTABLE_PY_DIR`/`STANDALONE_DIR`)도 `DEFAULT_LAYOUT_DIR`(=`builder_framework/default/`)로
  바꿔서, 한 틀의 화면 구성과 내보낸 실행 파일을 같은 폴더에 모아두게 함(이름 있는 틀 폴더 안에도
  내보내면 자연히 그 폴더에 모임 — "실행 py 저장" 창을 이름 폴더로 직접 이동해서 저장하면 됨,
  자동 추적은 하지 않는 단순한 방식으로 결정함). 기존 `appData/layouts/`는 삭제(비어 있었음 —
  실사용 데이터가 그 방식으로 저장된 적이 없었음), 루트의 `builder_state.json`은 `git mv`로
  `builder_framework/default/builder_state.json`으로 이동(rename으로 기록되어 히스토리 보존).
  2026-08-16 이전 내보내기 결과물(`executable_py/`, `standalone/`)은 디스크에 그대로 남아있고
  코드가 더 이상 그 경로를 참조하지 않음 — 처음엔 "레거시 경로" 상수 2개를 남겨뒀다가, 아무 데서도
  안 쓰는 죽은 코드라 바로 지움(CLAUDE.md 파일 구성표로 대신 문서화).
- **팔레트 크기도 함께 저장**: `_save_state`에 `palette_size` 매개변수 추가, `builder_state.json`에
  `"palette": {"width":.., "height":..}` 키로 저장됨(`window` 키와 같은 자리, 같은 방식). "틀
  저장"/자동저장(90초 autosave) 모두 `CanvasWindow._current_palette_size()`(→
  `self.palette_window.width()/height()`)를 읽어서 넘김 — 이러려면 `CanvasWindow`가
  `PaletteWindow` 인스턴스에 대한 역참조를 알아야 해서, `main.py`에서 두 창을 만든 직후
  `canvas.palette_window = palette`로 연결함(순환 import 없이, 두 창을 둘 다 아는 유일한 자리인
  `main.py`에서 배선). 불러올 때(`CanvasTabs.__init__`의 자동 복원, `load_layout_dialog`)는
  `state.get("palette")`를 읽어서 `PaletteWindow(initial_size=...)`/`palette_window.resize(...)`로
  반영.
- **"새 틀 시작하기" 버튼** (팔레트, "저장된 틀 불러오기" 다음 순서): 확인창 후 `CanvasWindow.
  start_new_layout()`이 `self.tabs.load_state(None)`(탭 전부 지우고 빈 탭 하나만 추가)과
  `self.palette_window.reset_to_default_size()`(팔레트를 `PaletteWindow.DEFAULT_WIDTH/HEIGHT`로
  되돌림)를 호출 — 디스크 파일은 안 건드리므로 "틀 저장"을 눌러야 이 빈 상태가 실제로 저장됨.
- 헤드리스 테스트를 새 구조에 맞게 전면 재작성(`phase21_named_layouts.py`, 22개 체크로 확장 —
  sanitizer, save-as가 폴더+파일을 만들고 `STATE_FILE`은 안 건드리는지, `default`라는 이름으로는
  저장을 거부하는지, 덮어쓰기 확인, 불러오기가 탭+팔레트 크기를 동시에 되돌리는지, 저장된 틀이
  없을 때 안내만 뜨는지, "새 틀 시작하기"가 탭 1개+팔레트 기본 크기로 되돌리는지까지) + 기존
  `phase1_smoke_test.py`/`phase19_explain_tab_example_button.py`의 하드코딩된 옛 경로도 새 구조에
  맞게 갱신, 전체 회귀(25개 스크립트) 통과.
- **실제 데이터로 라이브 검증**: 실행 중이던 빌더를 정상 종료(WM_CLOSE) → `git mv`로 마이그레이션
  → 재실행 → 두 창(캔버스/팔레트) 정상 표시 확인 → 클릭 없는 패시브 스크린샷(사용자가 화면을 같이
  쓰고 있어서, 자동 클릭이 사용자의 다른 창을 잘못 건드린 적이 있었던 사고 이후로 이번 세션부터는
  라이브 검증에서 클릭/포커스 전환을 아예 안 함)으로 팔레트의 6개 버튼 순서(틀 저장/다른 이름으로
  저장/저장된 틀 불러오기/새 틀 시작하기/실행 py 저장/standalone 2줄 저장)와 캔버스의 실사용 탭
  (gvf/git/wiki/윈도우 현황/alarm/link/설명)이 마이그레이션 후에도 그대로임을 확인.

**후속 수정 — "다른 이름으로 저장"을 이름 입력 대신 실제 폴더 선택 창으로 (2026-08-16)**: 위에서
구현한 "다른 이름으로 저장"이 `QInputDialog.getText`로 이름만 받았는데, 사용자가 "저장 위치를
직접 고를 수 있는 창이 떠야 하는 거 아니냐"고 지적함. 확인 결과 원하는 방식은 "이름 입력 + 저장
위치는 `builder_framework/` 안에서만 폴더로 고르기"(자유 위치는 아님, `builder_framework/`
바깥으로 새면 "저장된 틀 불러오기" 목록에서 안 보이게 되므로). `QFileDialog.getExistingDirectory
(dir=BUILDER_FRAMEWORK_DIR)`로 교체 — 네이티브 폴더 선택 창의 "새 폴더" 버튼으로 새 이름의 폴더를
만들어 고르거나 기존 폴더를 고르면, **고른 폴더 이름 자체가 틀 이름**이 되고 그 밑에
`builder_state.json`이 저장됨. 고른 폴더가 `BUILDER_FRAMEWORK_DIR`의 직계 자식이 아니면(더 깊이
중첩되었거나 바깥) 경고 팝업 후 저장을 거부(`os.path.dirname(chosen_dir) ==
BUILDER_FRAMEWORK_DIR` 검사) — 중첩을 허용하면 `load_layout_dialog`가 그 폴더를 목록에서 못 찾게
됨. 이제 이름을 파일명 안전 문자로 걸러주던 `_sanitize_layout_name`은 아무도 안 부르는 죽은 코드가
돼서 `_LAYOUT_NAME_UNSAFE_CHARS`와 함께 지움(OS 폴더 선택 창이 반환하는 경로는 이미 그 OS에서
유효한 폴더명이라 별도 검증이 필요 없어짐) — 이제 안 쓰는 `import re`도 같이 정리. 헤드리스
테스트(`phase21_named_layouts.py`)를 `QFileDialog.getExistingDirectory`를 mock하는 방식으로
전면 재작성(21개 체크 — 저장/취소/중첩 폴더 거부/`default` 거부/덮어쓰기 확인/불러오기/새 틀
시작하기), `how_to_use.md`의 "다른 이름으로 저장" 설명도 폴더 선택 흐름으로 갱신.

## "활성 틀(active layout)" 추적 추가 — 모든 수정이 지금 작업 중인 틀 폴더에 저장되도록 (2026-08-16)

사용자가 위 폴더 재구성을 검토하다 지적: "나만의 tool 윈도를 수정하건 위젯 팔레트를 수정하건 수정
내용이 모두 builder_framework 밑의 사용자가 지정한 디렉토리에 저장되는 거야." 코드를 확인해보니
실제로는 그렇지 않았음 — `STATE_FILE`이 `builder_framework/default/builder_state.json`으로
하드코딩되어 있어서, "저장된 틀 불러오기"로 다른 틀(예: "회사용")을 불러와 수정해도 "틀 저장"을
누르면 그 내용은 항상 `default/`에 저장되고 있었음(코드 주석에도 "the app doesn't track a notion of
currently active 틀"이라고 의도적 설계로 적혀 있었음 — 이번에 바꾸기로 함). `builder_state.autosave.json`이
필요한지도 같이 확인 요청받아서, 이건 "틀 저장"과 무관하게 크래시 시 화면에 떠 있던 내용을 살리는
독립적인 안전망(90초 주기, 앱 루트의 고정 파일 하나)이라고 설명하고 사용자에게 처리 방침을 확인함
(`AskUserQuestion` 3개: 내보내기 기본 위치도 활성 틀을 따라갈지 / 창 제목에 활성 틀을 표시할지 /
autosave를 어떻게 할지) — 전부 권장안(예/예/지금처럼 유지)으로 확정.

- **`CanvasWindow._active_layout_name`/`_active_layout_dir`** 신규 추가(`__init__`에서 각각
  `"default"`/`DEFAULT_LAYOUT_DIR`로 시작) — "지금 편집이 어느 틀 폴더를 향하는지"를 세션 동안
  하나만 기억하는 상태. `_active_state_file()`이 `os.path.join(self._active_layout_dir,
  "builder_state.json")`을 돌려주고, `_update_window_title()`이 창 제목을 `f"나만의 tool -
  {self._active_layout_name}"`으로 갱신함.
- **갱신 지점 4곳**: `save_layout_as`(저장 성공 시 그 폴더로 전환 - Save As 관용과 동일하게, 이후
  저장은 방금 저장한 곳을 따라감), `load_layout_dialog`(불러온 틀로 전환), `start_new_layout`(다시
  `default`로 리셋). `save_template`("틀 저장")은 이제 하드코딩된 `STATE_FILE`이 아니라
  `self._active_state_file()`에 씀 - 팔레트 크기 포함 모든 필드가 그대로 그 폴더로 감(별도 코드
  변경 없이 됨 - `_current_palette_size()`를 그대로 넘기던 기존 인자 배선을 안 건드렸으므로).
- **내보내기 기본 위치도 활성 틀을 따라가도록**: `export_dialog`/`export_exe_dialog`가 하드코딩된
  `EXECUTABLE_PY_DIR`/`STANDALONE_DIR` 대신 `self._active_layout_dir`를 씀 - 이 두 상수는 이제 아무
  데서도 안 쓰는 죽은 코드라 지움(모듈 상수 위에 있던 "the app doesn't track a notion of currently
  active 틀" 설명 주석도 같이 지우고 `_active_layout_dir` 필드 쪽 주석으로 대체).
- **autosave는 그대로 독립적으로 유지**: `_autosave`는 여전히 고정된 `AUTOSAVE_STATE_FILE`(앱 루트)에
  만 씀, 활성 틀과 무관 - 어떤 틀을 작업 중이었든 크래시 시점에 화면에 떠 있던 내용을 그대로 살리는
  게 목적이라 "어느 틀 폴더로 갈지"와는 다른 축의 문제라고 판단(사용자도 권장안으로 승인).
- **앱 시작 시 활성 틀은 항상 `default`**: `CanvasTabs.__init__`의 자동 복원은 그대로 `STATE_FILE`
  (`default/`)만 읽음 - "마지막으로 작업하던 틀을 기억해서 거기서 재시작"까지는 이번 범위 밖(이전
  세션에 사용자가 "완전히 처음부터 시작하기" 관련 1/2번 항목은 필요 없다고 확인한 것과 같은 맥락으로
  범위를 좁게 유지함).
- 헤드리스 테스트 신규 작성(`phase23_active_layout_tracking.py`, 21개 체크) - 창 제목 초기값/전환,
  save-as 이후 "틀 저장"이 새 폴더로 가는지 default 파일은 안 건드리는지, 팔레트 크기 변경도 활성
  폴더에 반영되는지, 두 내보내기 다이얼로그의 기본 경로(`QFileDialog.getSaveFileName` 호출 인자를
  직접 캡처해서 확인)가 활성 폴더를 가리키는지, 불러오기로 되돌아간 뒤 "틀 저장"이 그쪽을 따라가는지,
  "새 틀 시작하기"가 default로 리셋하는지, autosave가 활성 틀과 무관하게 고정 파일에 계속 쓰는지까지.
  기존 회귀(`phase21`/`phase1`/`phase19`/`phase20`/`phase22`) 전부 재확인, 전체 통과.
  - **테스트 작성 중 겪은 문제(교훈, `[[feedback-autosave-test-hang]]`과 같은 패턴 재발)**: 새 테스트의
    한 단계에서 이미 파일이 있는 폴더에 다시 `save_layout_as`를 호출해 덮어쓰기 확인
    `QMessageBox.question`을 트리거하는데, 그 호출을 mock하지 않고 놓쳐서 또 조용히 무한 행(hang)됨 -
    `Bash` 타임아웃으로 백그라운드로 넘어간 프로세스를 PID로 찾아 원인이 내가 만든 진단/테스트
    스크립트임을 확인한 뒤(실제 빌더 GUI 프로세스와는 무관), 사용자에게 종료해도 되는지 물어보고
    (`Stop-Process`가 auto-mode 분류기에 의해 매번 별도 승인 필요) 정리함 - 이 세션에서만 이 패턴이
    두 번 반복됨.
- **실제 앱으로 라이브 검증**: 코드가 바뀌었으므로 기존에 켜져 있던 인스턴스를 WM_CLOSE로 정상
  종료(우연히 두 개가 동시에 떠 있었음 - venv `pythonw.exe`가 내부적으로 시스템 Python312의
  `pythonw.exe`를 다시 실행하는 방식으로 보이는 프로세스 쌍이 매번 생김, 실제 창은 항상 후자
  쪽에만 있고 전자는 창 없는 유휴 프로세스 - 이번에도 같은 패턴 확인, 문제 아님) → 재실행 →
  `GetWindowText`로 두 창의 실제 제목을 직접 읽어 확인: "나만의 tool - default" / "위젯 팔레트" -
  실사용 데이터(`builder_framework/default/builder_state.json`)가 정상 로드된 채로 창 제목에 활성
  틀 이름이 정확히 반영됨을 확인.

## 레거시 내보내기 경로 정리 + 팔레트 저장 위치 재확인 + 저장 버튼 이름/그룹 정리 (2026-08-16)

토큰 소진으로 세션을 끊고 `CronCreate`(일회성, `40 18 16 8 *`)로 예약해뒀다가 refill 후 이어서
진행한 4개 항목.

**1. `executable_py/`/`standalone/` 정리**: `executable_py/`는 git으로 추적되던 날짜별 예전 내보내기
결과물 폴더들(`2026_07_26`~`2026_08_12_#7`)이었음 - `CLAUDE.md`가 `2026_07_26/app.py`를 "참고용
기본 예제"로 명시 언급하고 있어서, 이 파일만 먼저 `git mv`로 `examples/website_link_button/app.py`
(신규 디렉토리)로 옮겨 보존한 뒤(내용 확인함 - 버튼 1개로 URL 여는 48줄짜리 최소 예제, 사용자가
그동안 "예제" 버튼 설명에서 계속 언급해온 그 웹사이트 링크 예제와 같은 성격), 나머지는 `git rm -r
executable_py`로 삭제. `standalone/`은 애초에 `.gitignore`에 통째로 올라가 있어 git 추적 대상이
아니었음(`git rm`이 "pathspec did not match"로 실패해서 발견) - 그런데 `rm -rf`도 "Device or
resource busy"로 실패해서 확인해보니 **`standalone/ai_tools.exe`가 실제로 두 프로세스로 실행 중**
(11:26 AM 시작, 사용자가 직접 내보내서 켜둔 것으로 보이는 실행 파일)이었음 - 이건 이 세션이 만든
프로세스가 아니라 사용자가 지금 쓰고 있을 가능성이 있는 것이라 물어보지 않고 종료하지 않았고,
`standalone/` 삭제도 보류함(레거시 정리를 다 못 끝낸 상태로 남음 - 다음에 사용자가 그 실행 파일을
안 쓰는 걸 확인해주면 마저 지우면 됨). Windows 시작프로그램 레지스트리(`HKCU\...\Run`)에 이 경로를
가리키는 항목이 없는 것도 미리 확인해서, 지워도 시작프로그램이 깨지진 않는다는 것까진 확인해둠.
`CLAUDE.md`의 핵심 원칙 2번과 파일 구성표를 새 예제 경로에 맞게 갱신. 정리 중 `.gitignore`에
`standalone/` 통째 제외 규칙만 있고 일반 `*.exe` 규칙이 없던 것도 발견 - `builder_framework/
<이름>/`으로 내보내기 기본 위치가 바뀌면서 exe가 이제 `standalone/` 밖(예:
`builder_framework/default/ai_tools.exe`)에도 생기는데 이게 그대로 `git status`에 안 잡히던 걸
`.gitignore`에 `*.exe` 한 줄 추가해서 막음(용량이 큰 바이너리를 실수로 커밋하지 않기 위함 -
CLAUDE.md에 이미 명시된 의도와 일치, `.py` 내보내기는 계속 추적 대상으로 둠).

**2. 위젯 팔레트 저장 위치 재확인**: 사용자가 이전 세션에서 이미 활성 틀 추적으로 해결됐다고 보고한
뒤에도 "그래도 팔레트 수정하면 `C:\repository\ai-gui-builder-app` 밑에 저장되는 것처럼 보인다,
디폴트를 덮어쓰는 거 아니냐"고 재차 확인 요청함 - `palette_window.py`를 처음부터 끝까지 다시 읽고
`canvas_window.py`에서 `BASE_DIR`/`palette_window.width()/height()`를 참조하는 모든 지점을 grep으로
전수 확인한 결과, **버그 없음**을 확인: `palette_window.py` 자체는 파일 I/O를 전혀 하지 않고(리사이즈
핸들러도, `QSettings`도 없음), 팔레트 크기가 디스크에 쓰이는 경로는 오직 `CanvasWindow.
_current_palette_size()` → `_save_state(..., target_file=...)` 하나뿐이며, 그 `target_file`은
호출 지점마다 이미 활성 틀 추적을 따라감(`save_template`→활성 틀 폴더, `save_layout_as`→방금 고른
폴더, `_autosave`→고정된 별도 파일). 레포 루트(`C:\repository\ai-gui-builder-app`)에 뭔가 쓰이는
것처럼 보인 원인은 `builder_state.autosave.json`(90초 크래시 안전망, 활성 틀과 무관하게 항상 이
경로 하나에만 씀, 팔레트 크기도 포함됨)일 가능성이 높다고 판단 - **이 파일과 `builder_framework/
default/builder_state.json`은 서로 다른 파일이고, autosave 파일 내용이 default의 실제 저장 파일에
반영되려면 크래시 후 "복구할까요?" 팝업에서 예를 누르고 그 뒤에 사용자가 "틀 저장"을 직접 눌러야만
한다(자동으로 덮어쓰지 않음)**는 점을 `how_to_use.md`에 파일 구성표 새 행으로 명확히 문서화함.
코드 변경은 없었고(재확인 결과 이미 이전 세션의 활성 틀 추적 수정으로 해결되어 있었음), 기존
`phase23_active_layout_tracking.py`(21개 체크, 특히 "named 폴더에서 팔레트 리사이즈 후 틀 저장 →
default 파일은 안 건드림" 체크)를 재실행해서 여전히 통과하는 것으로 재확인.

**3. "다른 이름으로 저장" → "다른 이름으로 틀 저장" 이름 변경**: `palette_window.py`의 버튼
라벨과 `canvas_window.py`의 관련 다이얼로그 제목/안내 문구/주석(4곳)을 모두 바꿈. `how_to_use.md`
전체에서 이 버튼을 가리키는 텍스트(8곳, `replace_all`)도 함께 갱신 - `progress_status.md`의 과거
로그 항목들은 당시 실제 라벨을 그대로 서술한 역사 기록이라 손대지 않음(이 프로젝트의 기존 컨벤션).

**4. 저장 버튼 그룹 재배치**: `palette_window.py`의 `save_col`을 세 그룹으로 재구성 - **틀 저장 /
다른 이름으로 틀 저장 / 저장된 틀 불러오기**(그룹 1) — 가로 구분선(`QFrame.HLine`+`Sunken`, 팔레트
안 다른 항목 구분선과 같은 스타일로 통일) — **새 틀 시작하기**(그룹 2) — 가로 구분선 —
**실행 py 저장 / standalone 실행 파일 저장**(그룹 3, 기존 2줄 큰 버튼 유지). 그룹 내부 버튼 간격은
기존 30px에서 20px로 살짝 줄이고, 구분선 전후로 14px씩 둬서 그룹 사이가 그룹 내부보다 시각적으로
더 벌어지게 함.

헤드리스 테스트 신규 작성(`phase24_save_button_rename_and_grouping.py`, 5개 체크) - 새 라벨 존재
확인, 옛 라벨(정확히 일치, "다른 이름으로 틀 저장"의 부분 문자열이 아니라 완전히 옛날 문구 자체)이
남아있지 않은지, `save_col` 레이아웃을 순서대로 순회해서 버튼 8개 + 구분선 2개가 정확히 요청받은
순서와 일치하는지 확인. 전체 회귀(scratchpad의 phase*.py 26개) 재실행 통과. 코드가 바뀌었으므로
실행 중이던 빌더 인스턴스를 WM_CLOSE로 정상 종료 후 재실행, `GetWindowText`로 창 제목 재확인 +
패시브 스크린샷으로 팔레트의 새 그룹/구분선/새 버튼 라벨이 정확히 요청한 모양대로 보이는 것과
"나만의 tool - default" 창의 실사용 탭(gvf/git/wiki/윈도우 현황/alarm/link/설명)이 여전히 정상인
것을 눈으로 확인.

## `standalone/` 최종 삭제 + `pick_startup_file` 기본 경로 후속 수정 (2026-08-16)

위 항목의 "1번" 마무리: 사용자가 "안 쓰는 거니까 종료하고 지워"라고 확인해줘서, 실행 중이던
`standalone/ai_tools.exe` 두 프로세스(11:26 AM부터 떠 있던 것)를 `GetWindowText`로 실제 창이 있는
쪽(PID 8740, 제목 "My App")만 WM_CLOSE로 정상 종료 - 나머지 하나(PID 6808)는 창이 없는 PyInstaller
onefile 부트로더였는지 앞의 프로세스가 끝나자 같이 종료됨. 두 프로세스 모두 사라진 것을 확인한 뒤
`standalone/`을 `rm -rf`로 삭제(애초에 `.gitignore`에 있어 git에는 흔적이 안 남음).

**삭제하다가 발견한 후속 버그**: `code_binder.py`(빌더 자체가 쓰는 실제 함수)와 `exporter.py`의
`HEADER_TEMPLATE`(모든 내보내기 결과물에 그대로 박히는 템플릿 문자열) 양쪽에 있는
`pick_startup_file(parent)`이 `os.path.join(os.path.dirname(os.path.abspath(__file__)),
"standalone")`을 파일 선택 창의 기본 위치로 하드코딩하고 있었음 - `standalone/`을 지운 지금은
이 경로가 더 이상 존재하지 않아서, "설명" 탭의 "시작 프로그램 등록"/"삭제" 버튼을 누르면 파일 선택
창이 엉뚱한(존재하지 않는) 위치에서 열리게 됨. 두 파일 다 `"builder_framework"`로 바꿔서 고침 -
`code_binder.py` 쪽(빌더 자신의 위치 기준)은 항상 실존하는 `builder_framework/`로 정확히 맞고,
`exporter.py`의 템플릿 쪽(내보낸 앱 자신의 위치 기준)은 내보낸 스크립트 옆에 `builder_framework/`가
없는 경우가 많아 완벽하진 않지만(애초에 standalone/도 exported 위치 기준으로는 마찬가지로 대부분
안 맞았던 값이라 이번에 새로 생긴 문제는 아님), 적어도 삭제된 걸 참조하던 하드코딩은 없앰 - 두
파일의 동일 로직은 항상 같이 고쳐야 한다는 이 프로젝트의 기존 컨벤션대로 함께 수정.

헤드리스 테스트 신규 작성(`phase25_pick_startup_file_default_dir.py`, 5개 체크) - `code_binder.py`
쪽이 실제로 `builder_framework/`를 기본값으로 넘기는지, `exporter.HEADER_TEMPLATE` 문자열 안에
`"standalone"` 리터럴이 더 이상 없는지, **실제로 `generate_source`가 만든 소스를 `exec`해서 진짜
함수 객체로 호출**해 내보낸 스크립트 자신의 위치 기준으로 올바르게 `builder_framework/`를 계산하는지
(`app.py` 위치를 임의로 지정해서 그 옆의 `builder_framework/`가 나오는지)까지 확인. `how_to_use.md`
전체에서 남아있던 `standalone/` 언급(시작 프로그램 등록/삭제 버튼 설명, 화이트리스트 함수 목록,
실습 예제 8단계, 파일 구성 요약)을 전부 새 경로/과거형 서술로 갱신.

## `appData/`(alarm/git/gvf)도 활성 틀을 따라가도록 (2026-08-16)

사용자가 `C:\repository\ai-gui-builder-app\appData`의 위치가 맞는지 재차 확인 요청함 - 확인해보니
`alarm_widget.py`/`git_widget.py`/`gvf_widget.py` 세 파일 모두 `_STATE_DIR = os.path.dirname(
os.path.abspath(__file__))`(빌더 실행 시 이 세 소스 파일이 있는 레포 루트로 고정)로 계산하고 있어서,
오늘 만든 "활성 틀" 추적(`builder_state.json`/팔레트 크기)과 달리 **어떤 틀이 활성화돼 있든 항상
같은 고정 위치**를 보고 있었음 - 일관성이 깨져있는 게 맞았음. `AskUserQuestion`으로 확인한 결과
"builder_framework/<활성 틀>/appData/로 이동"을 선택함(공유 유지 대신 완전 분리를 원함).

- **각 위젯 모듈에 `set_state_dir(path)` 추가**: 기존 `_STATE_DIR`/`_APP_DATA_DIR`/
  `ALARM_STATE_FILE`(또는 `GIT_PANEL_STATE_FILE`/`GVF_STATE_FILE`)/레거시 경로 상수들을 전역
  변수 재할당으로 갱신하는 함수. 기존 내부 함수(`_load_alarm_state`/`_save_alarm_state` 등)는 이
  전역 이름들을 호출 시점마다 새로 조회하는 방식이라(파이썬 전역 조회는 매번 동적) 함수 본문은 전혀
  안 건드려도 됨 - 재할당만으로 이후의 모든 읽기/쓰기가 새 경로를 따라감. exported standalone 앱은
  이 함수를 절대 호출하지 않으므로(그런 개념 자체가 없음) 원래의 frozen/스크립트 기준 기본값을
  그대로 유지함 - `exporter.py`가 각 위젯 소스를 파일째로 그대로 임베드하는 방식이라 이 함수도 같이
  딸려 들어가지만 아무도 안 부르니 무해함.
- **`canvas_window.py`에 `_apply_active_layout_state_dir(path)`** 추가 - 세 모듈의 `set_state_dir`를
  한 번에 호출하는 헬퍼. 호출 지점 4곳(전부 "위젯이 (재)생성되기 *전*"이어야 함 - 패널 생성자가
  생성 시점에 상태 파일을 읽으므로): `CanvasWindow.__init__`에서 `CanvasTabs()` 생성 **전**(항상
  `DEFAULT_LAYOUT_DIR`), `save_layout_as`(새로 고른 폴더로), `load_layout_dialog`에서
  `self.tabs.load_state(state)` **전**(불러온 틀 폴더로), `start_new_layout`(다시
  `DEFAULT_LAYOUT_DIR`로).
- **`save_layout_as`에 `_copy_app_data_snapshot(src, dest)` 추가**: 새 폴더로 전환하기 *전에*, 기존
  활성 폴더의 `appData/`가 있으면 `shutil.copytree(dirs_exist_ok=True)`로 새 폴더에 통째로 복사해둠
  - `builder_state.json`이 save-as 시점에 "지금까지의 전체 내용"을 스냅샷하는 것과 같은 원칙(이후
  수정분만 새 위치로 가는 게 아니라, 그 시점까지 쌓인 alarm/git/gvf 데이터도 함께 가져감).
  `load_layout_dialog`/`start_new_layout`은 복사가 필요 없음 - 위젯이 새로 생성되면서 그 폴더에
  이미 있는(또는 없는) 데이터를 그대로 읽어들이는 것 자체가 "전환"이라서.
- **실제 데이터 마이그레이션**: 레포 루트 `appData/`(alarm_state.json 빈 배열, git_panel_state.json
  6쌍 중 3쌍 채워짐, gvf_state.json의 acquisition 값들 - 전부 이 세션 이전부터 쌓여있던 진짜
  사용자 데이터)를 `git mv`로 `builder_framework/default/appData/`로 옮김(파일별 rename으로 히스토리
  보존, 빈 `appData/` 디렉토리는 정리). 실행 중이던 빌더를 WM_CLOSE로 정상 종료 → 마이그레이션 →
  재실행 → 창 제목 "나만의 tool - default" 정상, 옮겨진 3개 파일 내용을 직접 읽어서 마이그레이션
  전과 동일함(빈 알람 목록, git 3쌍, gvf acquisition 값들 그대로)을 확인 → 패시브 스크린샷으로 gvf
  탭이 정상 렌더링되는 것까지 확인. `[[project-appdata-tracked]]` 메모리도 새 경로로 갱신.
- 헤드리스 테스트 신규 작성(`phase26_appdata_follows_active_layout.py`, 17개 체크) - 시작 시 세
  모듈 모두 default를 보는지, 실제 `AlarmClockPanel`을 `load_state`로 진짜 생성해서 그 패널이 보는
  경로가 활성 틀을 따라가는지, save-as가 스냅샷 복사 + 전환을 모두 하는지, 전환 후 새 폴더에서의
  수정이 default 쪽 파일을 안 건드리는지, "저장된 틀 불러오기"로 default에 돌아오면 원래 데이터를
  다시 읽어오는지(중간에 이름있는 틀에서 쓴 내용과 섞이지 않는지), "새 틀 시작하기"도 default로
  리셋하는지까지. 전체 회귀(scratchpad phase*.py 29개) 재실행 통과.
  - **테스트 작성 중 겪은 문제 2건(교훈)**: (1) `_save_alarm_state`는 직렬화 전 in-memory 형식(문자열
    아닌 실제 `QDateTime`)을 기대하는데 테스트에서 문자열을 그대로 넣어서 `AttributeError`로 바로
    터짐 - `QDateTime.fromString(...)`으로 고침. (2) "저장된 틀 불러오기"로 `default`를 선택하는
    단계에서, 이 세션 동안 `default`의 `builder_state.json`을 한 번도 실제로 저장한 적이 없어서
    `_load_state_file`이 `None`을 반환 → `QMessageBox.critical`이 안 mock된 채 호출되어 또
    offscreen에서 조용히 무한 행(hang)됨(`[[feedback-autosave-test-hang]]`과 같은 패턴, 이 세션에서
    세 번째 반복) - 테스트 흐름에 `win.save_template()`을 실제로 한 번 넣어 default 파일이 진짜
    존재하게 만들고, 안전망으로 `QMessageBox.critical`도 전역 mock에 추가해서 고침.
