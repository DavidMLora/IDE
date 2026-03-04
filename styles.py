# styles.py

GLOBAL_STYLES = """
    /* Fondo general y texto */
    QMainWindow, QWidget {
        background-color: #1e1e1e;
        color: #cccccc;
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    /* Editor de texto (Global) */
    QTextEdit, QPlainTextEdit {
        background-color: #252526;
        color: #d4d4d4;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 4px;
        selection-background-color: #264f78;
    }

    /* Pestañas (Tabs) */
    QTabWidget::pane {
        border: 1px solid #333333;
        border-radius: 6px;
        background-color: #252526;
        margin-top: -1px;
    }
    
    QTabWidget QTextEdit, QTabWidget QPlainTextEdit {
        border: none;
        border-radius: 0px; 
    }

    QTabBar::tab {
        background: #2d2d2d;
        color: #888888;
        padding: 8px 16px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        border: 1px solid transparent;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #252526;
        color: #ffffff;
        border-bottom: 2px solid #007acc;
    }
    QTabBar::tab:hover:!selected {
        background: #333333;
    }

    QTabBar::scroller {
        width: 40px; 
    }
    QTabBar QToolButton {
        background-color: #2d2d2d;
        color: #cccccc;
        border: none;
        border-radius: 4px;
        margin: 2px;
    }
    QTabBar QToolButton:hover {
        background-color: #444444;
    }

    /* Botones de herramientas y acciones */
    QPushButton, QToolButton {
        background-color: transparent;
        color: #cccccc;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 6px;
    }
    QPushButton:hover, QToolButton:hover {
        background-color: #333333;
        border: 1px solid #444444;
    }
    QPushButton:pressed, QToolButton:pressed {
        background-color: #007acc;
        color: white;
    }

    /* ======== ESTILOS DE MENÚ ======== */
    QMenuBar {
        background-color: #1e1e1e;
        color: #cccccc;
        border-bottom: 1px solid #333333;
    }
    QMenuBar::item {
        padding: 6px 12px;
        background-color: transparent;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background-color: #333333;
    }

    QMenu {
        background-color: #252526;
        color: #cccccc;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 4px 0px;
    }
    QMenu::item {
        padding: 6px 30px 6px 20px;
        background-color: transparent;
        min-width: 220px; /* <-- Esto le da suficiente espacio para el atajo largo */
    }
    QMenu::item:selected {
        background-color: #007acc;
        color: white;
    }
    QMenu::separator {
        height: 1px;
        background: #333333;
        margin: 4px 0px;
    }
    
    /* ======== ESTADO DESHABILITADO ======== */
    QPushButton:disabled, QToolButton:disabled {
        color: #555555;
        background-color: transparent;
        border: 1px solid transparent;
    }
    QMenu::item:disabled {
        color: #555555;
        background-color: transparent;
    }

    /* ======== SIDEBAR / EXPLORER ======== */
    QWidget#sidebar {
        background-color: #171717;
        border-right: 1px solid #2b2b2b;
    }
    QLabel#sidebar_title {
        color: #9fbfe6;
        font-weight: 700;
        padding: 8px 10px;
        font-size: 12px;
    }
    QListWidget#file_explorer {
        background: transparent;
        color: #d0d0d0;
        border: none;
        padding: 6px;
    }
    QListWidget#file_explorer::item {
        padding: 6px 10px;
    }
    QListWidget#file_explorer::item:selected {
        background-color: #094771;
        color: white;
    }

    /* ======== TOP HEADER / TOOLBAR ======== */
    QLabel#app_logo_label {
        color: #4ebfff;
        font-weight: 700;
        margin-right: 6px;
    }
    QLabel#app_name {
        color: #ffffff;
        font-weight: 700;
        font-size: 14px;
        margin-right: 12px;
    }
    QPushButton#top_toolbar_btn {
        background: transparent;
        color: #cfd8df;
        border-radius: 6px;
        padding: 6px;
    }
    QPushButton#top_toolbar_btn:hover {
        background-color: #2a2a2a;
    }
"""

WELCOME_STYLES = """
    QLabel#title {
        font-size: 36px; 
        color: #ffffff; 
        font-weight: bold;
    }
    QLabel#subtitle {
        font-size: 18px; 
        color: #888888; 
        margin-bottom: 30px;
    }
    QPushButton#link_btn {
        text-align: left; 
        color: #007acc; 
        font-size: 15px; 
        padding: 8px 12px;
    }
    QPushButton#link_btn:hover {
        background-color: #2a2d2e;
        color: #4ebfff;
        text-decoration: none;
    }
    QFrame#welcome_container {
        background-color: transparent;
    }
    QWidget#welcome_left {
        min-width: 360px;
        max-width: 480px;
    }
    QWidget#welcome_right {
        background-color: #1b1b1b;
        border: 1px solid #2d2d2d;
        border-radius: 8px;
        padding: 18px;
    }
    QLabel#welcome_card_title {
        font-size: 20px;
        color: #ffffff;
        font-weight: 600;
    }
    QLabel#welcome_card_sub {
        color: #9a9a9a;
        font-size: 13px;
    }
    QPushButton#primary_btn {
        background-color: #0e639c;
        color: white;
        border-radius: 6px;
        padding: 10px 12px;
        font-weight: 600;
    }
    QPushButton#primary_btn:hover {
        background-color: #1177c7;
    }
    QPushButton#secondary_btn {
        background-color: transparent;
        color: #c7d2de;
        border: 1px solid #2f2f2f;
        border-radius: 6px;
        padding: 8px 10px;
    }
    QListWidget#welcome_recent {
        background-color: transparent;
        color: #d0d0d0;
        border: none;
    }
    QListWidget#welcome_recent::item {
        padding: 8px 12px;
    }
    QListWidget#welcome_recent::item:selected {
        background-color: #094771;
        color: white;
    }
    QLabel#tip {
        color: #bfc7cf;
        font-size: 13px;
    }
    /* ======== SCROLLBARS ======== */
    QScrollBar:vertical {
        border: none;
        background: #1e1e1e;
        width: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #424242;
        min-height: 20px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical:hover {
        background: #4f4f4f;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
    QScrollBar:horizontal {
        border: none;
        background: #1e1e1e;
        height: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:horizontal {
        background: #424242;
        min-width: 20px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #4f4f4f;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        border: none;
        background: none;
    }
"""