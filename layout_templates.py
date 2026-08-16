"""Pure data + pure geometry for the palette's "레이아웃 템플릿" feature.

No Qt imports on purpose - `TEMPLATE_SPECS` describes each preset arrangement
of `rect_group` boxes as *fractions* of the canvas page's current size (not
fixed pixels), so a template always fits whatever the page's size happens to
be at drop time instead of assuming a particular window size (see CLAUDE.md's
"never resize the builder window" rule - fixed pixel offsets would eventually
force that). `equalize_margins` is the one algorithm behind both the
multi-container "정렬" action and the per-container "내부 정렬" action in
canvas_window.py - see md_files progress notes for the feature this supports.
"""

# Each variant's `rects` list is drop order, which also becomes z-order
# (later entries drawn on top) and save/restore order.
TEMPLATE_SPECS = [
    {
        "key": "single",
        "label": "큰 사각형 1개",
        "rects": [
            {"title": "사각형 1", "rel_x": 0.03, "rel_y": 0.03, "rel_w": 0.94, "rel_h": 0.94},
        ],
    },
    {
        "key": "stacked",
        "label": "큰 사각형 2개 (상하)",
        "rects": [
            {"title": "사각형 1", "rel_x": 0.03, "rel_y": 0.03, "rel_w": 0.94, "rel_h": 0.45},
            {"title": "사각형 2", "rel_x": 0.03, "rel_y": 0.52, "rel_w": 0.94, "rel_h": 0.45},
        ],
    },
    {
        "key": "side_by_side",
        "label": "큰 사각형 2개 (좌우)",
        "rects": [
            {"title": "사각형 1", "rel_x": 0.03, "rel_y": 0.03, "rel_w": 0.45, "rel_h": 0.94},
            {"title": "사각형 2", "rel_x": 0.52, "rel_y": 0.03, "rel_w": 0.45, "rel_h": 0.94},
        ],
    },
    {
        "key": "big_top_two_small_bottom",
        "label": "큰 사각형 1개 + 작은 사각형 2개 (큰 것이 위)",
        "rects": [
            {"title": "사각형 1", "rel_x": 0.03, "rel_y": 0.03, "rel_w": 0.94, "rel_h": 0.55},
            {"title": "사각형 2", "rel_x": 0.03, "rel_y": 0.62, "rel_w": 0.45, "rel_h": 0.35},
            {"title": "사각형 3", "rel_x": 0.52, "rel_y": 0.62, "rel_w": 0.45, "rel_h": 0.35},
        ],
    },
    {
        "key": "two_small_top_big_bottom",
        "label": "작은 사각형 2개 + 큰 사각형 1개 (작은 것들이 위)",
        "rects": [
            {"title": "사각형 1", "rel_x": 0.03, "rel_y": 0.03, "rel_w": 0.45, "rel_h": 0.35},
            {"title": "사각형 2", "rel_x": 0.52, "rel_y": 0.03, "rel_w": 0.45, "rel_h": 0.35},
            {"title": "사각형 3", "rel_x": 0.03, "rel_y": 0.42, "rel_w": 0.94, "rel_h": 0.55},
        ],
    },
    {
        "key": "three_across",
        "label": "직사각형 3개 (가로)",
        "rects": [
            {"title": "사각형 1", "rel_x": 0.03, "rel_y": 0.03, "rel_w": 0.30, "rel_h": 0.94},
            {"title": "사각형 2", "rel_x": 0.35, "rel_y": 0.03, "rel_w": 0.30, "rel_h": 0.94},
            {"title": "사각형 3", "rel_x": 0.67, "rel_y": 0.03, "rel_w": 0.30, "rel_h": 0.94},
        ],
    },
    {
        "key": "three_stacked",
        "label": "직사각형 3개 (세로)",
        "rects": [
            {"title": "사각형 1", "rel_x": 0.03, "rel_y": 0.03, "rel_w": 0.94, "rel_h": 0.30},
            {"title": "사각형 2", "rel_x": 0.03, "rel_y": 0.35, "rel_w": 0.94, "rel_h": 0.30},
            {"title": "사각형 3", "rel_x": 0.03, "rel_y": 0.67, "rel_w": 0.94, "rel_h": 0.30},
        ],
    },
]

TEMPLATE_SPECS_BY_KEY = {spec["key"]: spec for spec in TEMPLATE_SPECS}


def _cluster_into_rows(rects):
    """Groups rect indices into rows by vertical (y-range) overlap - two
    rects are in the same row if one's vertical extent overlaps more than
    half of the shorter one's height. Handles irregular grids (e.g. one big
    box on top of two small ones) without assuming a clean uniform grid: the
    big box simply ends up alone in its own row since it doesn't vertically
    overlap the row below it. Returns rows top-to-bottom, each a list of
    rect indices sorted left-to-right."""
    order = sorted(range(len(rects)), key=lambda i: rects[i][1])
    rows = []
    for i in order:
        _x, y, _w, h = rects[i]
        for row in rows:
            _rx, ry, _rw, rh = rects[row[0]]
            overlap = min(y + h, ry + rh) - max(y, ry)
            if overlap > 0.5 * min(h, rh):
                row.append(i)
                break
        else:
            rows.append([i])
    for row in rows:
        row.sort(key=lambda i: rects[i][0])
    rows.sort(key=lambda row: min(rects[i][1] for i in row))
    return rows


def equalize_margins(outer_rect, rects, min_sizes=None):
    """Repositions *and* resizes `rects` (list of (x, y, w, h) tuples, all in
    the same coordinate space as `outer_rect`) so a single margin/gap value
    M applies everywhere: the outer margin on all 4 sides of the whole
    group, the gap between rows, and the gap between boxes within a row -
    genuinely the same number throughout, not just "snap similar values
    together". Rects are grouped into rows by vertical overlap (see
    `_cluster_into_rows`) so an irregular grid (e.g. one big box + two small
    ones) is handled without assuming a clean uniform grid.

    M is derived from the median of the group's *current* outer margins/
    gaps (so the result reflects roughly what was already there, just made
    exact) and then clamped so no row/box is squeezed below its floor.
    Reaching an exact shared M generally isn't possible by repositioning
    alone unless the current sizes already happen to add up right, so each
    row's total height and each box's width within its row are resized
    proportionally to their current sizes - a "big" box stays proportionally
    bigger than "small" ones, just resized to make the margins exact.

    `min_sizes`, if given, is a list of (min_w, min_h) floors matching
    `rects`' order (see canvas_window.py's `_container_min_size` for a
    `rect_group` that must stay >= its own children's bounding box, decision
    C) - never violated, at the cost of that one box's margins possibly
    landing slightly off from the shared M in a tight fit.

    Returns a new list of (x, y, w, h) tuples, same order/length as `rects`.
    """
    if not rects:
        return []
    ox, oy, ow, oh = outer_rect
    min_sizes = min_sizes or [(0, 0)] * len(rects)

    rows = _cluster_into_rows(rects)
    num_rows = len(rows)

    row_heights_now = [max(rects[i][3] for i in row) for row in rows]
    row_tops_now = [min(rects[i][1] for i in row) for row in rows]
    row_bottoms_now = [max(rects[i][1] + rects[i][3] for i in row) for row in rows]

    # Every currently-observed outer margin and internal gap, both axes
    # combined - the median of these is the M that best reflects "roughly
    # what the user already had", before we make it exact everywhere.
    v_gaps = [row_tops_now[0] - oy]
    for k in range(1, num_rows):
        v_gaps.append(row_tops_now[k] - row_bottoms_now[k - 1])
    v_gaps.append((oy + oh) - row_bottoms_now[-1])

    h_gaps = []
    for row in rows:
        xs = [rects[i][0] for i in row]
        ws = [rects[i][2] for i in row]
        h_gaps.append(xs[0] - ox)
        for k in range(1, len(row)):
            h_gaps.append(xs[k] - (xs[k - 1] + ws[k - 1]))
        h_gaps.append((ox + ow) - (xs[-1] + ws[-1]))

    all_gaps = sorted(v_gaps + h_gaps)
    m = all_gaps[len(all_gaps) // 2]

    # Clamp M so distributing the leftover budget below can't push any
    # row/box under its floor (decision C).
    row_min_heights = [max(min_sizes[i][1] for i in row) for row in rows]
    m_caps = [(oh - sum(row_min_heights)) / (num_rows + 1)]
    for row in rows:
        total_min_w = sum(min_sizes[i][0] for i in row)
        m_caps.append((ow - total_min_w) / (len(row) + 1))
    m = max(1, round(min([m] + m_caps)))

    # Vertical: distribute leftover height across rows proportionally to
    # their current heights, floored at each row's own min height.
    v_budget = oh - m * (num_rows + 1)
    total_row_height_now = sum(row_heights_now) or 1
    new_row_heights = [
        max(min_h, round(v_budget * (rh / total_row_height_now)))
        for rh, min_h in zip(row_heights_now, row_min_heights)
    ]

    result = [None] * len(rects)
    y_cursor = oy + m
    for row, new_h in zip(rows, new_row_heights):
        h_budget = ow - m * (len(row) + 1)
        ws_now = [rects[i][2] for i in row]
        total_w_now = sum(ws_now) or 1
        x_cursor = ox + m
        for slot, i in enumerate(row):
            min_w, _min_h = min_sizes[i]
            new_w = max(min_w, round(h_budget * (ws_now[slot] / total_w_now)))
            result[i] = (x_cursor, y_cursor, new_w, new_h)
            x_cursor += new_w + m
        y_cursor += new_h + m

    return result
