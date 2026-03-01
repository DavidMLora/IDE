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
    
    /* ======== NUEVO: ESTADO DESHABILITADO ======== */
    QPushButton:disabled, QToolButton:disabled {
        color: #555555;
        background-color: transparent;
        border: 1px solid transparent;
    }
    QMenu::item:disabled {
        color: #555555;
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
"""