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
]

TEMPLATE_SPECS_BY_KEY = {spec["key"]: spec for spec in TEMPLATE_SPECS}


def _cluster_and_target(values, outer_value, tolerance):
    """Single-linkage clusters `values` (plus `outer_value` as a sentinel
    member with index None) along one edge kind, and returns a target value
    per input (same order/length as `values`): the outer boundary's exact
    value if it shares a cluster with that entry, else the cluster's mean
    (rounded happens by the caller)."""
    tagged = [(v, i) for i, v in enumerate(values)] + [(outer_value, None)]
    tagged.sort(key=lambda t: t[0])

    clusters = [[tagged[0]]]
    for item in tagged[1:]:
        if item[0] - clusters[-1][-1][0] <= tolerance:
            clusters[-1].append(item)
        else:
            clusters.append([item])

    targets = [None] * len(values)
    for cluster in clusters:
        has_outer = any(idx is None for _, idx in cluster)
        target = outer_value if has_outer else sum(v for v, _ in cluster) / len(cluster)
        for v, idx in cluster:
            if idx is not None:
                targets[idx] = target
    return targets


_ALIGN_TOLERANCE = 16


def equalize_margins(outer_rect, rects, min_sizes=None, tolerance=_ALIGN_TOLERANCE):
    """Auto-aligns `rects` (list of (x, y, w, h) tuples, all in the same
    coordinate space as `outer_rect`) so that edges landing within
    `tolerance` px of each other - or of the outer boundary - snap to a
    single shared margin, independently per edge kind (left/right/top/bottom
    are never mixed with each other). Not a full constraint solver: each of
    the 4 edge kinds is clustered on its own, which is enough for both a
    clean row/column *and* an irregular grid (e.g. one big box + two small
    ones) without assuming any particular arrangement.

    `min_sizes`, if given, is a list of (min_w, min_h) floors matching
    `rects`' order (see canvas_window.py's `_container_min_size` for
    containers that must stay >= their own children's bounding box). A rect
    whose aligned size would fall below its floor keeps its *original* size
    but still moves to its aligned position - this never raises, it just
    leaves that one rect's size alone.

    Returns a new list of (x, y, w, h) tuples, same order/length as `rects`.
    """
    ox, oy, ow, oh = outer_rect
    min_sizes = min_sizes or [(0, 0)] * len(rects)

    lefts = [r[0] for r in rects]
    rights = [r[0] + r[2] for r in rects]
    tops = [r[1] for r in rects]
    bottoms = [r[1] + r[3] for r in rects]

    left_targets = _cluster_and_target(lefts, ox, tolerance)
    right_targets = _cluster_and_target(rights, ox + ow, tolerance)
    top_targets = _cluster_and_target(tops, oy, tolerance)
    bottom_targets = _cluster_and_target(bottoms, oy + oh, tolerance)

    result = []
    for i, (x, y, w, h) in enumerate(rects):
        new_left, new_right = left_targets[i], right_targets[i]
        new_top, new_bottom = top_targets[i], bottom_targets[i]
        new_w = new_right - new_left
        new_h = new_bottom - new_top

        min_w, min_h = min_sizes[i]
        if new_w < min_w:
            new_w = w
        if new_h < min_h:
            new_h = h

        result.append((round(new_left), round(new_top), round(new_w), round(new_h)))
    return result
