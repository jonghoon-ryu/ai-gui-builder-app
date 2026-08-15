"""App-wide QSS applied once at startup for a nicer default look.

Deliberately avoids setting font-family/font-size so widgets keep
inheriting Qt's default (which already matches the Windows system font).
Per-widget stylesheets (colored tabs, user-picked widget colors, etc.)
set directly on those widgets still take precedence over these rules.
"""

APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f4f5f8;
}

QPushButton {
    background-color: #ffffff;
    color: #262a33;
    border: 1px solid #ced2db;
    border-radius: 6px;
    padding: 2px 6px;
    min-height: 0px;
}
QPushButton:hover {
    background-color: #eef1f8;
    border-color: #aeb4c2;
}
QPushButton:pressed {
    background-color: #e1e5f0;
}
QPushButton:disabled {
    color: #9aa0ab;
    background-color: #eeeff2;
    border-color: #dde0e6;
}

QLineEdit, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #ced2db;
    border-radius: 5px;
    padding: 4px 6px;
    selection-background-color: #b9c9fb;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #5b72e0;
}

QComboBox {
    background-color: #ffffff;
    color: #262a33;
    border: 1px solid #ced2db;
    border-radius: 6px;
    padding: 4px 10px;
    min-height: 22px;
    selection-background-color: #b9c9fb;
}
QComboBox:hover {
    border-color: #aeb4c2;
    background-color: #f8f9fc;
}
QComboBox:focus {
    border: 1px solid #5b72e0;
}
QComboBox:disabled {
    color: #9aa0ab;
    background-color: #eeeff2;
    border-color: #dde0e6;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #ced2db;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #eef1f8;
}
QComboBox::drop-down:hover {
    background-color: #dde3f5;
}
QComboBox::down-arrow {
    width: 9px;
    height: 9px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #ced2db;
    border-radius: 6px;
    padding: 4px;
    outline: none;
    selection-background-color: #5b72e0;
    selection-color: #ffffff;
}
QComboBox QAbstractItemView::item {
    padding: 6px 8px;
    border-radius: 4px;
    min-height: 20px;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #ced2db;
    border-radius: 5px;
}
QListWidget::item {
    padding: 4px 6px;
}
QListWidget::item:selected {
    background-color: #dbe4fd;
    color: #1c2130;
}

QGroupBox {
    border: 1px solid #ced2db;
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 6px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

QTabWidget::pane {
    border: 0;
}
QTabBar::tab {
    background: #e4e7ee;
    border: 1px solid #ced2db;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 6px 18px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom: 2px solid #5b72e0;
}
QTabBar::tab:hover:!selected {
    background: #eef1f8;
}

QCalendarWidget QAbstractItemView {
    selection-background-color: #5b72e0;
    selection-color: #ffffff;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #c3c8d4;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #a7adbc;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #c3c8d4;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #a7adbc;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
"""
