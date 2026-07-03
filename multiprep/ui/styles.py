GMAIL_STYLE = """
QMainWindow, QWidget {
    background: #fffdf7;
    color: #202124;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}
QLabel { color: #202124; background: transparent; }
QFrame#BrandHeader {
    background: #ffffff;
    border: 1px solid #f1e4b4;
    border-radius: 14px;
}
QFrame#GmailGuide {
    background: #fff7d6;
    border: 1px solid #f9ab00;
    border-radius: 12px;
}
QFrame#ClassicGuide {
    background: #ffffff;
    border: 1px solid #d8cfb9;
    border-radius: 12px;
}
QLabel#ClassicGuideTitle { color: #202124; font-size: 12pt; font-weight: 800; }
QLabel#BrandTitle { color: #202124; font-size: 19pt; font-weight: 800; }
QLabel#BrandVersion { color: #9a6700; font-size: 10pt; font-weight: 700; }
QLabel#GuideTitle { color: #7a4f00; font-size: 12pt; font-weight: 800; }
QLabel#MutedText { color: #6b6250; }
QLineEdit, QSpinBox {
    background: #ffffff;
    color: #202124;
    border: 1px solid #d8cfb9;
    border-radius: 7px;
    padding: 7px 9px;
    selection-background-color: #f9ab00;
    selection-color: #202124;
}
QLineEdit:focus, QSpinBox:focus { border: 2px solid #f9ab00; }
QPushButton {
    background: #f9ab00;
    color: #202124;
    border: 1px solid #e89b00;
    border-radius: 8px;
    padding: 9px 14px;
    font-weight: 700;
}
QPushButton:hover { background: #ffc232; }
QPushButton:pressed { background: #e89b00; }
QPushButton#SecondaryButton { background: #ffffff; border: 1px solid #d8cfb9; }
QPushButton#SecondaryButton:hover { background: #fff7d6; border-color: #f9ab00; }
QPushButton#ModeButton { background: #202124; color: #ffffff; border: none; }
QPushButton#ModeButton:hover { background: #3c4043; }
QToolButton {
    background: #ffffff;
    color: #202124;
    border: 1px solid #d8cfb9;
    border-radius: 7px;
    min-width: 26px;
    min-height: 28px;
    font-size: 15px;
    font-weight: 700;
}
QToolButton:hover { background: #fff7d6; border-color: #f9ab00; }
QCheckBox { color: #202124; spacing: 8px; background: transparent; }
QCheckBox::indicator {
    width: 18px; height: 18px; background: #ffffff;
    border: 1px solid #b8ad91; border-radius: 4px;
}
QCheckBox::indicator:checked { background: #f9ab00; border-color: #d99000; }
QListWidget { border: 1px solid #eadfbf; border-radius: 10px; background: #fffaf0; }
QMenu { background: #ffffff; color: #202124; border: 1px solid #d8cfb9; }
QMenu::item:selected { background: #fff0b3; }
QMessageBox { background: #fffdf7; }
QStatusBar { background: #ffffff; color: #6b6250; }
"""


CLASSIC_STYLE = """
QMainWindow, QWidget { background: #111827; color: #f9fafb; font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; }
QLabel { color: #f9fafb; background: transparent; }
QFrame#BrandHeader { background: #172033; border: 1px solid #374151; border-radius: 12px; }
QFrame#ClassicGuide { background: #172033; border: 1px solid #374151; border-radius: 10px; }
QLabel#ClassicGuideTitle { color: #93c5fd; font-size: 12pt; font-weight: 800; }
QLabel#BrandTitle { color: #f9fafb; font-size: 19pt; font-weight: 800; }
QLabel#BrandVersion { color: #93c5fd; font-size: 10pt; font-weight: 700; }
QLabel#MutedText { color: #cbd5e1; }
QLineEdit, QSpinBox { background: #f9fafb; color: #111827; border: 1px solid #64748b; border-radius: 5px; padding: 6px 8px; selection-background-color: #2563eb; selection-color: #ffffff; }
QLineEdit:focus, QSpinBox:focus { border: 2px solid #60a5fa; }
QPushButton { background: #2563eb; color: #ffffff; border: none; border-radius: 5px; padding: 8px 12px; font-weight: 600; }
QPushButton:hover { background: #1d4ed8; }
QPushButton:pressed { background: #1e40af; }
QPushButton#SecondaryButton { background: #334155; border: 1px solid #64748b; }
QPushButton#ModeButton { background: #f9ab00; color: #202124; }
QToolButton { background: #334155; color: #ffffff; border: 1px solid #64748b; border-radius: 5px; min-width: 26px; min-height: 28px; font-size: 15px; font-weight: 700; }
QToolButton:hover { background: #475569; border-color: #93c5fd; }
QCheckBox { color: #f9fafb; spacing: 8px; background: transparent; }
QCheckBox::indicator { width: 18px; height: 18px; background: #f9fafb; border: 1px solid #94a3b8; border-radius: 3px; }
QCheckBox::indicator:checked { background: #2563eb; border: 1px solid #93c5fd; }
QListWidget { border: 1px solid #374151; border-radius: 8px; background: #0f172a; }
QMenu { background: #1f2937; color: #f9fafb; border: 1px solid #4b5563; }
QMenu::item:selected { background: #2563eb; }
QMessageBox { background: #111827; }
"""


APP_STYLE = GMAIL_STYLE

_gmail_mode = True


def set_theme_mode(gmail_mode: bool) -> None:
    global _gmail_mode
    _gmail_mode = gmail_mode


def is_gmail_mode() -> bool:
    return _gmail_mode
