"""빌더 상태를 헤드리스로 복원해서, 탭 안 위젯들의 좌표/여백/간격을 표로 찍어준다.

이 세션에서 "여백을 좌우와 같게", "간격을 모두 동일하게" 같은 요청을 처리할 때마다
매번 새로 짰던 임시 스크립트를 하나로 정리한 것 - 실제 렌더링된(offscreen) 좌표를
기준으로 하므로 손으로 계산하는 것보다 정확하다.

사용법 (저장소 루트에서):
    venv\\Scripts\\python.exe tools\\inspect_layout.py           # 모든 탭
    venv\\Scripts\\python.exe tools\\inspect_layout.py gvf        # "gvf" 탭만
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from PySide6.QtWidgets import QApplication  # noqa: E402

import canvas_window as cw  # noqa: E402
import theme  # noqa: E402


def _load_canvas():
    """Builds the real CanvasWindow (same restore path main.py uses) and
    forces one resize/show/processEvents cycle - without this, QTabWidget's
    page size() reports a stale default instead of the actual tab content
    area (learned the hard way earlier this session)."""
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(theme.APP_STYLESHEET)
    width, height = cw.get_saved_window_size() or (820, 499)
    win = cw.CanvasWindow(width, height)
    win.resize(width, height)
    win.show()
    for _ in range(5):
        app.processEvents()
    return app, win


def _ranges_overlap(a_start, a_len, b_start, b_len):
    return a_start < b_start + b_len and b_start < a_start + a_len


def inspect_tab(page, tab_title):
    page_w, page_h = page.width(), page.height()
    print(f"\n=== 탭 '{tab_title}' (콘텐츠 영역 {page_w}x{page_h}) ===")

    items = []
    for widget_id, entry in page.entries.items():
        g = entry["widget"].geometry()
        items.append((widget_id, entry["kind"], g))
    items.sort(key=lambda item: (item[2].y(), item[2].x()))

    if not items:
        print("  (위젯 없음)")
        return

    for widget_id, kind, g in items:
        left, top = g.x(), g.y()
        right = page_w - (g.x() + g.width())
        bottom = page_h - (g.y() + g.height())
        print(
            f"  {widget_id:16s} kind={kind:16s} x={g.x():4d} y={g.y():4d} "
            f"w={g.width():4d} h={g.height():4d}  "
            f"(좌={left} 우={right} 상={top} 하={bottom})"
        )

    # Nearest-neighbor gaps only (not every pair) - a tab with N widgets has
    # O(N^2) pairs with overlapping perpendicular ranges, and most of those
    # aren't actually adjacent (something else sits between them). For each
    # widget, only the closest widget to its right / below it is a real
    # "여백/간격" a person would ask about.
    right_gap = {}  # id -> (neighbor_id, gap)
    bottom_gap = {}
    for id_a, _kind_a, ga in items:
        for id_b, _kind_b, gb in items:
            if id_a == id_b:
                continue
            if _ranges_overlap(ga.y(), ga.height(), gb.y(), gb.height()):
                if ga.x() + ga.width() <= gb.x():
                    gap = gb.x() - (ga.x() + ga.width())
                    if id_a not in right_gap or gap < right_gap[id_a][1]:
                        right_gap[id_a] = (id_b, gap)
            if _ranges_overlap(ga.x(), ga.width(), gb.x(), gb.width()):
                if ga.y() + ga.height() <= gb.y():
                    gap = gb.y() - (ga.y() + ga.height())
                    if id_a not in bottom_gap or gap < bottom_gap[id_a][1]:
                        bottom_gap[id_a] = (id_b, gap)

    if right_gap or bottom_gap:
        print("  --- 인접 간격 (각 위젯의 가장 가까운 오른쪽/아래쪽 이웃) ---")
        for id_a, _kind_a, _ga in items:
            if id_a in right_gap:
                neighbor, gap = right_gap[id_a]
                print(f"  {id_a} → {neighbor}: {gap}px")
            if id_a in bottom_gap:
                neighbor, gap = bottom_gap[id_a]
                print(f"  {id_a} ↓ {neighbor}: {gap}px")


def main():
    target_tab = sys.argv[1] if len(sys.argv) > 1 else None
    _app, win = _load_canvas()

    tabs = win.tabs
    found = False
    for i in range(tabs.count()):
        title = tabs.tabText(i)
        if target_tab and title != target_tab:
            continue
        found = True
        tabs.setCurrentIndex(i)
        _app.processEvents()
        inspect_tab(tabs.widget(i), title)

    if target_tab and not found:
        available = [tabs.tabText(i) for i in range(tabs.count())]
        print(f"'{target_tab}' 탭을 찾을 수 없습니다. 사용 가능한 탭: {available}")
        sys.exit(1)


if __name__ == "__main__":
    main()
