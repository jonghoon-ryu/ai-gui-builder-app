# progress_status.md — 현재까지 진행 상황 (다음에 이어서 시작할 때 참고)

기준 시점: 2026-08-09 저녁. 이 문서는 "지금 뭐가 되어 있고, 다음에 뭘 더 할 수 있는지"를 빠르게
파악하기 위한 스냅샷이다. 자세한 사용법은 `how_to_use.md`, 지금까지의 요구사항 변경 이력은
`tool_requirement.md` 참고.

## 지금 상태 (한 줄 요약)

빌더(`main.py`)는 완성도 있게 동작 중이고, 실제로 사용자가 5개 탭(git/wiki/쉬었다 합시다/윈도우 현황/
alarm)에 위젯을 채워서 쓰고 있다. 위젯 종류, 저장/복원, standalone 내보내기, 자연어 동작 생성용
화이트리스트 함수, 전용 "알람 시계" 위젯까지 전부 구현 완료 상태.

## 지금 켜져 있는 앱 실행법

```bash
cd /home/ryuj/Ryu/ai-gui-builder-app
./venv/bin/python main.py
```

## 지원하는 위젯 (팔레트)

드롭박스, 누름 버튼, 텍스트 박스, 가로선, 세로선, URL 입력창(팝업으로도 입력 가능),
디렉토리 입력창(폴더 아이콘으로 선택), 라디오 버튼(그룹별 독립, 첫 옵션 기본 선택).

**알람 시계**는 팔레트에 없음 — "alarm" 탭에 이미 고정 배치되어 있음 (사용자 요청으로 팔레트에서 뺌).

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
오른쪽 위 180×180 아날로그 시계, 알람 시간에 20cm×20cm 정사각형 팝업(메시지를 96pt 굵은 글씨로 크게
표시). 패널 기본 크기
840×640. 구현은 `alarm_widget.py` (빌더/standalone 양쪽에서 같은 소스 파일을 그대로 사용).

**알아둘 제한사항**: 등록한 알람 목록 자체(무슨 알람을 만들었는지)는 저장 대상이 아니라서 앱을
재시작하면 초기화됨 — 위젯의 위치/크기만 저장됨. 필요해지면 이어서 작업할 수 있음.

## 현재 탭 구성 (실사용 중인 내용)

- **git** — 비어있음
- **wiki** — URL/디렉토리 입력창 + "가져와서 md로 변환" 버튼(웹 문서를 md로 저장, 이미지는 라디오
  버튼으로 자동/claude 분류 선택) + 라디오 버튼 2개
- **쉬었다 합시다** — 노래 링크 버튼 3개(유튜브 열기) + 구분선
- **윈도우 현황** — 비어있음
- **alarm** — 알람 시계 위젯 1개

## 알려진 미완/보류 항목

- **Windows 미검증**: 코드상으로는 크로스플랫폼(PySide6/markdownify/bs4)이라 될 가능성이 높다고 보지만,
  실제 Windows에서 돌려본 적은 없음. 특히 `subprocess.run(["claude", ...])`로 호출하는 부분들
  (`classify_image_with_claude`, `ai_client.py`)이 Windows에 npm으로 깐 `claude`(.cmd 셸 스크립트)를
  `shell=True` 없이 잘 찾는지 확인 필요. 생성된 동작 코드가 경로를 `"/"`로 직접 이어붙이는 부분도
  Windows에서 문제없는지 실사용 시 확인.
- **이미지 분류 로직**: `wiki` 탭의 "가져와서 md로 변환" 버튼 동작 코드에 이미 실제로 붙어 있음
  (`extract_images`/`download_file`/`classify_image_with_claude`/`move_file` 사용). 다만
  `classify_image_with_claude`는 이미지 개수만큼 `claude` CLI를 순차 호출하므로 이미지가 많은
  페이지에서는 느릴 수 있음 — 필요하면 배치 처리나 병렬화 고려 가능.
- **알람 목록 영속성**: 위에서 언급한 대로 알람 내용 자체는 재시작 시 사라짐. 저장하고 싶다면
  `AlarmClockPanel`에 저장/복원 로직을 추가해야 함 (현재는 범위 밖으로 보류).
- **합성 위젯(알람 시계)의 이동/크기조절 한계**: 내부에 버튼/리스트가 꽉 차 있어서 위젯 내부를 클릭해
  드래그로 옮기기는 어려움 (러버밴드 선택 + 삭제/복사는 정상 동작). 필요하면 자식 위젯까지 이벤트를
  전달하는 방식으로 개선 가능.

## standalone 내보내기 이력

`standalone/` 밑에 날짜(+번호)별 폴더로 정리되어 있음: `2026_07_26`, `2026_08_09_#2`, `#3`, `#5`,
`#6`, `#7`, `#8`. 앞으로도 이 규칙(`standalone/2026_MM_DD_#N/app.py`)을 따르면 됨.

## 파일 구성 요약

`main.py`(진입점) · `palette_window.py`(팔레트) · `canvas_window.py`(캔버스/탭/위젯 로직 대부분) ·
`behavior_dialog.py`(동작 설정 다이얼로그) · `ai_client.py`(claude CLI 호출, 코드 생성 프롬프트) ·
`code_binder.py`(화이트리스트 함수 + 안전한 exec) · `exporter.py`(standalone 내보내기) ·
`alarm_widget.py`(알람 시계) · `builder_state.json`(자동 저장되는 현재 작업 상태) ·
`md_files/`(문서) · `standalone/`(내보내기 결과물).
