"""`ColorTabBar`: the tab bar used by both the builder canvas and every
standalone-exported app, kept in its own file (like `alarm_widget.py`/
`window_status_widget.py`) so the two copies can't drift apart - the
exporter embeds this file's source verbatim.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPainterPath
from PySide6.QtWidgets import QStyle, QStyleOptionTab, QStylePainter, QTabBar


class ColorTabBar(QTabBar):
    """Tab bar that can paint an individual tab's label area with a flat
    color, bypassing the native style (which may ignore QPalette overrides)
    so the fill is always visible."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_colors = {}
        self.tabMoved.connect(self._on_tab_moved)

    def set_tab_color(self, index, color):
        self._tab_colors[index] = color
        self.update()

    def _on_tab_moved(self, from_index, to_index):
        """Keeps colors attached to their tab's content when the user
        drags a tab to a new position."""
        color = self._tab_colors.pop(from_index, None)
        shifted = {}
        for i, c in self._tab_colors.items():
            if from_index < to_index and from_index < i <= to_index:
                i -= 1
            elif to_index <= i < from_index:
                i += 1
            shifted[i] = c
        if color is not None:
            shifted[to_index] = color
        self._tab_colors = shifted
        self.update()

    def get_tab_color(self, index):
        return self._tab_colors.get(index)

    def remove_tab_color(self, index):
        self._tab_colors.pop(index, None)
        self._tab_colors = {
            (i - 1 if i > index else i): color for i, color in self._tab_colors.items()
        }
        self.update()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        current = self.currentIndex()
        for index in range(self.count()):
            color = self._tab_colors.get(index)
            rect = self.tabRect(index)
            font = QFont(self.font())
            font.setBold(index == current)
            if color is None:
                painter.save()
                opt = QStyleOptionTab()
                self.initStyleOption(opt, index)
                # Draw the native tab shape/chrome, then the label text
                # ourselves (instead of the combined CE_TabBarTab) so the
                # bold-when-selected font is actually honored - the native
                # style ignores a font set on the option or the painter
                # when drawing the label as part of CE_TabBarTab.
                painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
                text_rect = self.style().subElementRect(
                    QStyle.SubElement.SE_TabBarTabText, opt, self
                )
                painter.setFont(font)
                painter.setPen(self.palette().windowText().color())
                painter.drawText(text_rect, Qt.AlignCenter, self.tabText(index))
                painter.restore()
            else:
                painter.save()
                painter.setFont(font)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                # Match the QSS-styled (uncolored) tabs' rounded top corners
                # instead of a flat fillRect, so every tab reads as the same
                # shape regardless of whether it has a custom color.
                radius = 8
                path = QPainterPath()
                path.moveTo(rect.left(), rect.bottom())
                path.lineTo(rect.left(), rect.top() + radius)
                path.arcTo(rect.left(), rect.top(), 2 * radius, 2 * radius, 180, -90)
                path.lineTo(rect.right() - radius, rect.top())
                path.arcTo(rect.right() - 2 * radius, rect.top(), 2 * radius, 2 * radius, 90, -90)
                path.lineTo(rect.right(), rect.bottom())
                path.closeSubpath()
                painter.fillPath(path, color)
                painter.setPen(self.palette().windowText().color())
                painter.drawText(rect, Qt.AlignCenter, self.tabText(index))
                painter.restore()
