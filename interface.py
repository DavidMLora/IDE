# interface.py
import os
import sys
import subprocess
import shutil
import json
from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QTextEdit, 
                             QStatusBar, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QTabBar, QStackedWidget, QToolButton,
                             QFileDialog, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QTreeWidget, QTreeWidgetItem, QMessageBox,
                             QMenu, QInputDialog)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize
import qtawesome as qta

from editor import CodeEditor
from welcome import WelcomeScreen
from styles import GLOBAL_STYLES
from terminal import TerminalIntegrada

# ==========================================
# CLASE NUEVA: Ventana Flotante NATIVA
# ==========================================
class FloatWindow(QWidget):
    def __init__(self, title, child_widget, reattach_callback, main_ref):
        super().__init__(None) 
        self.setWindowTitle(title)
        self.resize(600, 400)
        self.child_widget = child_widget
        self.reattach_callback = reattach_callback
        self.main_ref = main_ref
        self.is_manual_close = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.child_widget)
        
        # Usar el GLOBAL_STYLES importado
        self.setStyleSheet(GLOBAL_STYLES)
        self.setWindowIcon(qta.icon('fa5s.code', color='#4ebfff'))
        
    def closeEvent(self, event):
        # Si el usuario hace clic en la 'X' de la ventana, la reintegramos
        if not self.is_manual_close:
            self.is_manual_close = True # Evitamos bucles
            self.reattach_callback()
        event.accept()

# ==========================================
# VENTANA PRINCIPAL
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CompilladorIDE")
        self.resize(1200, 800)
        self.setStyleSheet(GLOBAL_STYLES)

        self.tabs_analisis = QTabWidget()
        self.consola_inferior = QTabWidget()

        self._setup_ui()
        self.crear_menus_y_herramientas()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.actualizar_estado_ui()

    # --- NUEVO: ASEGURAR QUE SE CIERREN LAS VENTANAS FLOTANTES AL SALIR ---
    def closeEvent(self, event):
        if getattr(self, 'win_sidebar', None):
            self.win_sidebar.is_manual_close = True
            self.win_sidebar.close()
        if getattr(self, 'win_derecho', None):
            self.win_derecho.is_manual_close = True
            self.win_derecho.close()
        if getattr(self, 'win_inferior', None):
            self.win_inferior.is_manual_close = True
            self.win_inferior.close()
        event.accept()
    # ----------------------------------------------------------------------

    def _setup_ui(self):
        self._setup_header()
        self._setup_workspace()
        self._setup_panels()
        self._assemble_layout()

    def _setup_header(self):
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(10, 5, 10, 5)
        self.header_layout.setSpacing(10)

        logo_label = QLabel()
        logo_label.setObjectName('app_logo_label')
        logo_label.setPixmap(qta.icon('fa5s.code', color='#4ebfff').pixmap(18, 18))
        self.header_layout.addWidget(logo_label)

        app_name = QLabel("CompilladorIDE")
        app_name.setObjectName('app_name')
        self.header_layout.addWidget(app_name)

        self.file_tabs_bar = QTabBar()
        self.file_tabs_bar.setTabsClosable(True)
        self.file_tabs_bar.setMovable(False)
        self.file_tabs_bar.tabCloseRequested.connect(self.cerrar_pestana)
        self.file_tabs_bar.currentChanged.connect(self.cambiar_archivo_activo)
        
        self.header_layout.addWidget(self.file_tabs_bar)

        self.top_btn_save = self._create_tool_button('fa5s.save', "Guardar")
        self.top_btn_save_as = self._create_tool_button('fa5s.save', "Guardar como")
        self.top_btn_close = self._create_tool_button('fa5s.window-close', "Cerrar")

        self.top_btn_save.setObjectName('top_toolbar_btn')
        self.top_btn_save_as.setObjectName('top_toolbar_btn')
        self.top_btn_close.setObjectName('top_toolbar_btn')

        self.top_btn_save.clicked.connect(self.guardar_archivo)
        self.top_btn_save_as.clicked.connect(self.guardar_como)
        self.top_btn_close.clicked.connect(self.cerrar_archivo_actual)

        self.header_layout.addWidget(self.top_btn_save)
        self.header_layout.addWidget(self.top_btn_save_as)
        self.header_layout.addWidget(self.top_btn_close)

        self.btn_lexico = self._create_tool_button('fa5s.search', "Análisis Léxico (F6)")
        self.btn_sintactico = self._create_tool_button('fa5s.project-diagram', "Análisis Sintáctico (F7)")
        self.btn_semantico = self._create_tool_button('fa5s.lightbulb', "Análisis Semántico (F8)")
        self.btn_intermedio = self._create_tool_button('fa5s.code', "Generar Código Intermedio (F9)")
        self.btn_run = self._create_tool_button('fa5s.play', "Ejecutar Programa", color='#4ec9b0')

        self.btn_lexico.clicked.connect(self.ejecutar_lexico)
        self.btn_sintactico.clicked.connect(self.ejecutar_sintactico)
        self.btn_semantico.clicked.connect(self.ejecutar_semantico)
        self.btn_intermedio.clicked.connect(self.ejecutar_codigo_intermedio)
        self.btn_run.clicked.connect(self.ejecutar_programa)

        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_lexico)
        self.header_layout.addWidget(self.btn_sintactico)
        self.header_layout.addWidget(self.btn_semantico)
        self.header_layout.addWidget(self.btn_intermedio)
        self.header_layout.addWidget(self.btn_run)

    def _create_tool_button(self, icon_name, tooltip, color='#cccccc'):
        btn = QPushButton()
        btn.setIcon(qta.icon(icon_name, color=color, disabled_color='#444444'))
        btn.setToolTip(tooltip)
        btn.setFixedSize(36, 36)
        return btn

    def _setup_workspace(self):
        self.view_stack = QStackedWidget()
        self.welcome_screen = WelcomeScreen(self)
        
        self.sidebar = QWidget()
        self.sidebar.setObjectName('sidebar')
        self.sidebar.setMinimumSize(0, 0)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(6, 6, 6, 6)
        sidebar_layout.setSpacing(6)

        sidebar_header = QWidget()
        sidebar_header_layout = QHBoxLayout(sidebar_header)
        sidebar_header_layout.setContentsMargins(4, 0, 4, 0)
        sidebar_header_layout.setSpacing(2)

        self.sidebar_title = QLabel("EXPLORADOR")
        self.sidebar_title.setObjectName('sidebar_title')
        sidebar_header_layout.addWidget(self.sidebar_title)
        
        sidebar_header_layout.addStretch()

        self.btn_float_sidebar = self._create_tool_button('fa5s.external-link-alt', "Separar Explorador")
        self.btn_sidebar_new = self._create_tool_button('fa5s.file-medical', "Nuevo Archivo")
        self.btn_sidebar_open = self._create_tool_button('fa5s.folder-open', "Abrir Archivo")
        self.btn_sidebar_open_folder = self._create_tool_button('fa5s.folder-plus', "Abrir Carpeta")

        for btn in [self.btn_float_sidebar, self.btn_sidebar_new, self.btn_sidebar_open, self.btn_sidebar_open_folder]:
            btn.setObjectName('sidebar_btn')
            btn.setFixedSize(26, 26) 
            sidebar_header_layout.addWidget(btn)

        self.btn_float_sidebar.clicked.connect(self.toggle_float_sidebar)
        self.btn_sidebar_new.clicked.connect(self.nuevo_archivo)
        self.btn_sidebar_open.clicked.connect(self.abrir_archivo)
        self.btn_sidebar_open_folder.clicked.connect(self.abrir_carpeta)

        sidebar_layout.addWidget(sidebar_header)

        self.ruta_proyecto = None
        
        self.file_explorer = QTreeWidget()
        self.file_explorer.setObjectName('file_explorer')
        self.file_explorer.setHeaderHidden(True)
        self.file_explorer.setAnimated(True)
        self.file_explorer.setIndentation(20)
            
        self.file_explorer.itemClicked.connect(self._on_explorer_item_clicked)
        self.file_explorer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_explorer.customContextMenuRequested.connect(self.mostrar_menu_contextual_explorador)

        sidebar_layout.addWidget(self.file_explorer)

        self.editor_workspace = QWidget()
        workspace_layout = QVBoxLayout(self.editor_workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        
        self.editor_stack = QStackedWidget()
        workspace_layout.addWidget(self.header_widget)
        workspace_layout.addWidget(self.editor_stack)
        
        self.view_stack.addWidget(self.welcome_screen)
        self.view_stack.addWidget(self.editor_workspace)

    def show_analysis_tab(self, index: int):
        self.restaurar_panel_derecho()
        if 0 <= index < self.tabs_analisis.count():
            self.tabs_analisis.setCurrentIndex(index)

    def show_console_tab(self, index: int):
        self.restaurar_panel_inferior()
        if 0 <= index < self.consola_inferior.count():
            self.consola_inferior.setCurrentIndex(index)

    def _setup_panels(self):
        paneles_analisis = ["Léxico", "Sintáctico", "Semántico", "Tabla Símbolos", "C. Intermedio"]
        
        self.analysis_toolbar = QWidget()
        at_layout = QHBoxLayout(self.analysis_toolbar)
        at_layout.setContentsMargins(6, 6, 6, 6)
        at_layout.setSpacing(6)
        analysis_icons = [
            ('fa5s.search', 'Léxico', 0),
            ('fa5s.project-diagram', 'Sintáctico', 1),
            ('fa5s.lightbulb', 'Semántico', 2),
            ('fa5s.table', 'Tabla Símbolos', 3),
            ('fa5s.code', 'C. Intermedio', 4),
        ]
        for icon, tip, idx in analysis_icons:
            btn = QToolButton()
            btn.setIcon(qta.icon(icon, color='#cfd8df'))
            btn.setToolTip(tip)
            btn.setFixedSize(28, 28)
            btn.clicked.connect(lambda _, i=idx: self.show_analysis_tab(i))
            at_layout.addWidget(btn)

        for nombre in paneles_analisis:
            if nombre == "Léxico":
                tabla = QTableWidget()
                tabla.setColumnCount(4)
                tabla.setHorizontalHeaderLabels(["Token", "Lexema", "Fila", "Columna"])
                tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                tabla.setEditTriggers(QTableWidget.NoEditTriggers)
                tabla.setStyleSheet("""
                    QTableWidget { background-color: #1e1e1e; color: #d4d4d4; gridline-color: #333333; border: none; }
                    QHeaderView::section { background-color: #2d2d2d; color: #cccccc; border: 1px solid #333333; padding: 4px; font-weight: bold; }
                """)
                self.tabs_analisis.addTab(tabla, nombre)
            elif nombre == "Sintáctico":
                arbol = QTreeWidget()
                arbol.setHeaderHidden(True)
                arbol.setStyleSheet("""
                    QTreeWidget { background-color: #1e1e1e; color: #cccccc; border: none; }
                    QTreeView::item:hover { background-color: #2a2d2e; }
                    QTreeView::item:selected { background-color: #04395e; color: #ffffff; }
                """)
                self.tabs_analisis.addTab(arbol, nombre)
            else:
                txt_edit = QTextEdit()
                txt_edit.setReadOnly(True)
                self.tabs_analisis.addTab(txt_edit, nombre)

        self.console_toolbar = QWidget()
        ct_layout = QHBoxLayout(self.console_toolbar)
        ct_layout.setContentsMargins(6, 6, 6, 6)
        ct_layout.setSpacing(6)
        console_icons = [
            ('fa5s.exclamation-circle', 'Errores Léxicos', 0),
            ('fa5s.exclamation-triangle', 'Errores Sintácticos', 1),
            ('fa5s.bug', 'Errores Semánticos', 2),
            ('fa5s.terminal', 'Resultados', 3),
        ]
        for icon, tip, idx in console_icons:
            btn = QToolButton()
            btn.setIcon(qta.icon(icon, color='#cfd8df'))
            btn.setToolTip(tip)
            btn.setFixedSize(28, 28)
            btn.clicked.connect(lambda _, i=idx: self.show_console_tab(i))
            ct_layout.addWidget(btn)

        for nombre in ["Errores Léxicos", "Errores Sintácticos", "Errores Semánticos", "Resultados"]:
            txt_edit = QTextEdit()
            txt_edit.setReadOnly(True)
            self.consola_inferior.addTab(txt_edit, nombre)

        self.terminal_widget = TerminalIntegrada()
        self.consola_inferior.addTab(self.terminal_widget, "Terminal")

    def _assemble_layout(self):
        self.editor_container = QWidget()
        self.editor_container.setMinimumSize(0, 0) # <--- Permitir que se encoja para dar espacio a los paneles
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(10, 10, 5, 5)
        editor_layout.addWidget(self.view_stack)
        
        self.h_splitter = QSplitter(Qt.Horizontal)
        self.h_splitter.addWidget(self.sidebar)
        self.h_splitter.addWidget(self.editor_container)
        
        self.panel_derecho = QWidget()
        self.panel_derecho.setMinimumSize(0, 0)
        panel_derecho_layout = QVBoxLayout(self.panel_derecho)
        panel_derecho_layout.setContentsMargins(5, 10, 10, 5)
        
        right_header = QWidget()
        rh_layout = QHBoxLayout(right_header)
        rh_layout.setContentsMargins(0, 0, 0, 0)
        rh_layout.setSpacing(6)
        right_title = QLabel("Panel de Análisis")
        rh_layout.addWidget(right_title)
        rh_layout.addStretch()

        self.btn_float_right = QToolButton()
        self.btn_float_right.setIcon(qta.icon('fa5s.external-link-alt', color='#cccccc'))
        self.btn_float_right.setFixedSize(28, 28)
        self.btn_float_right.setToolTip("Separar panel")
        self.btn_float_right.setStyleSheet("QToolButton { background: transparent; border-radius: 4px; } QToolButton:hover { background: #333333; }")
        self.btn_float_right.clicked.connect(self.toggle_float_derecho)
        rh_layout.addWidget(self.btn_float_right)

        btn_close_right = QToolButton()
        btn_close_right.setIcon(qta.icon('fa5s.times', color='#ff5c5c'))
        btn_close_right.setIconSize(QSize(16, 16))
        btn_close_right.setFixedSize(28, 28)
        btn_close_right.setToolTip("Cerrar panel")
        btn_close_right.setStyleSheet("QToolButton { background: transparent; border-radius: 4px; } QToolButton:hover { background: rgba(255,92,92,0.12); }")
        btn_close_right.clicked.connect(self.close_panel_derecho)
        rh_layout.addWidget(btn_close_right)

        panel_derecho_layout.addWidget(right_header)
        panel_derecho_layout.addWidget(self.tabs_analisis)
        self.h_splitter.addWidget(self.panel_derecho)

        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.addWidget(self.h_splitter)
        
        self.panel_inferior = QWidget()
        self.panel_inferior.setMinimumSize(0, 0)
        panel_inferior_layout = QVBoxLayout(self.panel_inferior)
        panel_inferior_layout.setContentsMargins(10, 5, 10, 10)
        
        bottom_header = QWidget()
        bh_layout = QHBoxLayout(bottom_header)
        bh_layout.setContentsMargins(0, 0, 0, 0)
        bh_layout.setSpacing(6)
        bottom_title = QLabel("Consola")
        bh_layout.addWidget(bottom_title)
        bh_layout.addStretch()

        self.btn_float_bottom = QToolButton()
        self.btn_float_bottom.setIcon(qta.icon('fa5s.external-link-alt', color='#cccccc'))
        self.btn_float_bottom.setFixedSize(28, 28)
        self.btn_float_bottom.setToolTip("Separar consola")
        self.btn_float_bottom.setStyleSheet("QToolButton { background: transparent; border-radius: 4px; } QToolButton:hover { background: #333333; }")
        self.btn_float_bottom.clicked.connect(self.toggle_float_inferior)
        bh_layout.addWidget(self.btn_float_bottom)

        btn_close_bottom = QToolButton()
        btn_close_bottom.setIcon(qta.icon('fa5s.times', color='#ff5c5c'))
        btn_close_bottom.setIconSize(QSize(16, 16))
        btn_close_bottom.setFixedSize(28, 28)
        btn_close_bottom.setToolTip("Cerrar consola")
        btn_close_bottom.setStyleSheet("QToolButton { background: transparent; border-radius: 4px; } QToolButton:hover { background: rgba(255,92,92,0.12); }")
        btn_close_bottom.clicked.connect(self.close_panel_inferior)
        bh_layout.addWidget(btn_close_bottom)

        panel_inferior_layout.addWidget(bottom_header)
        panel_inferior_layout.addWidget(self.consola_inferior)
        self.v_splitter.addWidget(self.panel_inferior)

        self.h_splitter.setStretchFactor(0, 1)
        self.h_splitter.setStretchFactor(1, 4)
        self.h_splitter.setStretchFactor(2, 1)
        self.v_splitter.setStretchFactor(0, 3)
        self.v_splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.v_splitter)

    # ==========================================
    # LÓGICA DE VENTANAS FLOTANTES (POP-OUT)
    # ==========================================
    
    def toggle_float_sidebar(self):
        if not getattr(self, 'win_sidebar', None):
            self.win_sidebar = FloatWindow("Explorador de Archivos", self.sidebar, self._on_sidebar_float_close, self)
            self.win_sidebar.show()
            self.btn_float_sidebar.setIcon(qta.icon('fa5s.compress-arrows-alt', color='#4ebfff'))
            self.btn_float_sidebar.setToolTip("Integrar Explorador")
        else:
            self._on_sidebar_float_close()

    def _on_sidebar_float_close(self):
        # 1. PRIMERO rescatamos el widget de regreso al MainWindow
        self.h_splitter.insertWidget(0, self.sidebar)
        
        # 2. AHORA SÍ cerramos la ventana flotante de forma segura
        if getattr(self, 'win_sidebar', None):
            self.win_sidebar.is_manual_close = True
            self.win_sidebar.close()
            self.win_sidebar = None
            
        self.btn_float_sidebar.setIcon(qta.icon('fa5s.external-link-alt', color='#cccccc'))
        self.btn_float_sidebar.setToolTip("Separar Explorador")

    def toggle_float_derecho(self):
        if not getattr(self, 'win_derecho', None):
            self.win_derecho = FloatWindow("Panel de Análisis", self.panel_derecho, self._on_derecho_float_close, self)
            self.win_derecho.show()
            self.btn_float_right.setIcon(qta.icon('fa5s.compress-arrows-alt', color='#4ebfff'))
            self.btn_float_right.setToolTip("Integrar panel")
        else:
            self._on_derecho_float_close()

    def _on_derecho_float_close(self):
        # 1. PRIMERO rescatamos el widget de regreso al MainWindow
        self.h_splitter.insertWidget(2, self.panel_derecho)
        
        # 2. AHORA SÍ cerramos la ventana flotante
        if getattr(self, 'win_derecho', None):
            self.win_derecho.is_manual_close = True
            self.win_derecho.close()
            self.win_derecho = None
            
        self.btn_float_right.setIcon(qta.icon('fa5s.external-link-alt', color='#cccccc'))
        self.btn_float_right.setToolTip("Separar panel")

    def toggle_float_inferior(self):
        if not getattr(self, 'win_inferior', None):
            self.win_inferior = FloatWindow("Consola y Resultados", self.panel_inferior, self._on_inferior_float_close, self)
            self.win_inferior.show()
            self.btn_float_bottom.setIcon(qta.icon('fa5s.compress-arrows-alt', color='#4ebfff'))
            self.btn_float_bottom.setToolTip("Integrar consola")
        else:
            self._on_inferior_float_close()

    def _on_inferior_float_close(self):
        # 1. PRIMERO rescatamos el widget de regreso al MainWindow
        self.v_splitter.insertWidget(1, self.panel_inferior)
        
        # 2. AHORA SÍ cerramos la ventana flotante
        if getattr(self, 'win_inferior', None):
            self.win_inferior.is_manual_close = True
            self.win_inferior.close()
            self.win_inferior = None
            
        self.btn_float_bottom.setIcon(qta.icon('fa5s.external-link-alt', color='#cccccc'))
        self.btn_float_bottom.setToolTip("Separar consola")


    # ==========================================
    # MANEJO GENERAL DE UI Y ESTADO
    # ==========================================

    def actualizar_estado_ui(self):
        hay_archivo = self.editor_actual() is not None

        if not hay_archivo:
            if getattr(self, 'win_derecho', None): self._on_derecho_float_close()
            if getattr(self, 'win_inferior', None): self._on_inferior_float_close()
            self.panel_derecho.setVisible(False)
            self.panel_inferior.setVisible(False)

        self.btn_lexico.setEnabled(hay_archivo)
        self.btn_sintactico.setEnabled(hay_archivo)
        self.btn_semantico.setEnabled(hay_archivo)
        self.btn_intermedio.setEnabled(hay_archivo)
        self.btn_run.setEnabled(hay_archivo)

        if hasattr(self, 'action_cerrar'):
            self.action_cerrar.setEnabled(hay_archivo)
            self.action_guardar.setEnabled(hay_archivo)
            self.action_guardar_como.setEnabled(hay_archivo)
            self.action_lexico.setEnabled(hay_archivo)
            self.action_sintactico.setEnabled(hay_archivo)
            self.action_semantico.setEnabled(hay_archivo)
            self.action_intermedio.setEnabled(hay_archivo)
            self.action_run.setEnabled(hay_archivo)

    def restaurar_panel_derecho(self):
        if getattr(self, 'win_derecho', None):
            self.win_derecho.raise_()
            self.win_derecho.activateWindow()
            return
            
        self.panel_derecho.setVisible(True)
        sizes = self.h_splitter.sizes()
        if len(sizes) >= 3 and sizes[2] == 0:
            total = sum(sizes) or self.width()
            self.h_splitter.setSizes([int(total * 0.15), int(total * 0.7), int(total * 0.15)])
        elif len(sizes) == 2 and sizes[1] == 0:
            total = sum(sizes) or self.width()
            self.h_splitter.setSizes([int(total * 0.7), int(total * 0.3)])

    def restaurar_panel_inferior(self):
        if getattr(self, 'win_inferior', None):
            self.win_inferior.raise_()
            self.win_inferior.activateWindow()
            return
            
        self.panel_inferior.setVisible(True)
        sizes = self.v_splitter.sizes()
        if sizes[1] == 0:  
            total = sum(sizes) or self.height()
            self.v_splitter.setSizes([int(total * 0.75), int(total * 0.25)])

    def close_panel_derecho(self):
        if getattr(self, 'win_derecho', None):
            self._on_derecho_float_close()
            
        self.panel_derecho.setVisible(False)
        sizes = self.h_splitter.sizes()
        total = sum(sizes) or self.width()
        self.h_splitter.setSizes([int(total * 0.15), int(total * 0.85), 0])

    def close_panel_inferior(self):
        if getattr(self, 'win_inferior', None):
            self._on_inferior_float_close()
            
        self.panel_inferior.setVisible(False)
        sizes = self.v_splitter.sizes()
        total = sum(sizes) or self.height()
        self.v_splitter.setSizes([int(total * 1.0), 0])

    def editor_actual(self):
        return self.editor_stack.currentWidget()

    def nuevo_archivo(self):
        nuevo_ed = CodeEditor()
        nuevo_ed.file_path = None
        nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
        nuevo_ed.textChanged.connect(self.actualizar_status)
        idx = self.editor_stack.addWidget(nuevo_ed)
        
        self.file_tabs_bar.addTab("Sin título")
        
        btn_cerrar = QToolButton()
        btn_cerrar.setIcon(qta.icon('fa5s.times', color='#bbbbbb'))
        btn_cerrar.setIconSize(QSize(10, 10))
        btn_cerrar.setFixedSize(20, 20)
        btn_cerrar.setStyleSheet("QToolButton { border: none; padding: 0px; border-radius: 4px; } QToolButton:hover { background-color: #c42b1c; color: white; }")
        btn_cerrar.clicked.connect(self.cerrar_pestana_desde_boton)
        
        self.file_tabs_bar.setTabButton(idx, QTabBar.RightSide, btn_cerrar)
        self.file_tabs_bar.setCurrentIndex(idx)
        self.view_stack.setCurrentIndex(1)
        self.actualizar_estado_ui()

    def abrir_archivo_desde_ruta(self, path):
        for i in range(self.editor_stack.count()):
            ed = self.editor_stack.widget(i)
            if hasattr(ed, 'file_path') and ed.file_path == path:
                self.file_tabs_bar.setCurrentIndex(i) 
                return

        nuevo_ed = CodeEditor()
        with open(path, 'r', encoding='utf-8') as f:
            nuevo_ed.setPlainText(f.read())
        
        nuevo_ed.file_path = path
        nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
        nuevo_ed.textChanged.connect(self.actualizar_status)
        idx = self.editor_stack.addWidget(nuevo_ed)
        
        name = os.path.basename(path)
        self.file_tabs_bar.addTab(name)
        
        btn_cerrar = QToolButton()
        btn_cerrar.setIcon(qta.icon('fa5s.times', color='#bbbbbb'))
        btn_cerrar.setIconSize(QSize(10, 10))
        btn_cerrar.setFixedSize(20, 20)
        btn_cerrar.setStyleSheet("QToolButton { border: none; padding: 0px; border-radius: 4px; } QToolButton:hover { background-color: #c42b1c; color: white; }")
        btn_cerrar.clicked.connect(self.cerrar_pestana_desde_boton)
        self.file_tabs_bar.setTabButton(idx, QTabBar.RightSide, btn_cerrar)

        self.file_tabs_bar.setCurrentIndex(idx)
        self.view_stack.setCurrentIndex(1)
        self.actualizar_estado_ui()

    def abrir_archivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Archivos de texto (*.txt);;Todos (*)")
        if path:
            self.abrir_archivo_desde_ruta(path)

    def abrir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Abrir Carpeta de Proyecto")
        if carpeta:
            self.cargar_proyecto_en_arbol(carpeta)

    def cargar_proyecto_en_arbol(self, carpeta):
        self.ruta_proyecto = os.path.normpath(carpeta)
        
        self.file_explorer.clear()
        
        nombre_carpeta = os.path.basename(self.ruta_proyecto)
        root_item = QTreeWidgetItem(self.file_explorer, [nombre_carpeta])
        root_item.setIcon(0, qta.icon('fa5s.folder-open', color='#dcb67a')) 
        root_item.setData(0, Qt.UserRole, self.ruta_proyecto)

        self._poblar_arbol(self.ruta_proyecto, root_item)
        root_item.setExpanded(True)

        os.chdir(self.ruta_proyecto)
        if hasattr(self, 'terminal_widget'):
            self.terminal_widget.cambiar_directorio(self.ruta_proyecto)
            
        self.status_bar.showMessage(f"Carpeta de proyecto abierta: {self.ruta_proyecto}", 5000)

    def _poblar_arbol(self, ruta_directorio, parent_item):
        try:
            entradas = os.listdir(ruta_directorio)
            carpetas = []
            archivos = []

            for e in entradas:
                if e.startswith('__pycache__') or e.startswith('.git'):
                    continue
                    
                ruta_completa = os.path.join(ruta_directorio, e)
                if os.path.isdir(ruta_completa):
                    carpetas.append((e, ruta_completa))
                else:
                    archivos.append((e, ruta_completa))

            carpetas.sort(key=lambda x: x[0].lower())
            archivos.sort(key=lambda x: x[0].lower())

            for nombre, ruta in carpetas:
                item = QTreeWidgetItem(parent_item, [nombre])
                item.setIcon(0, qta.icon('fa5s.folder', color='#dcb67a'))
                item.setData(0, Qt.UserRole, ruta)
                self._poblar_arbol(ruta, item)

            for nombre, ruta in archivos:
                item = QTreeWidgetItem(parent_item, [nombre])
                
                if nombre.endswith('.py'):
                    icon = qta.icon('fa5s.file-code', color='#ffde57')
                elif nombre.endswith('.txt'):
                    icon = qta.icon('fa5s.file-alt', color='#cccccc')
                else:
                    icon = qta.icon('fa5s.file', color='#cccccc')
                    
                item.setIcon(0, icon)
                item.setData(0, Qt.UserRole, ruta)

        except Exception as e:
            print(f"Error poblando árbol: {e}")

    def _on_explorer_item_clicked(self, item, column):
        ruta = item.data(0, Qt.UserRole)
        if ruta and os.path.isfile(ruta):
            self.abrir_archivo_desde_ruta(ruta)

    def mostrar_menu_contextual_explorador(self, pos):
        if not self.ruta_proyecto: return

        item = self.file_explorer.itemAt(pos)
        ruta_origen = item.data(0, Qt.UserRole) if item else self.ruta_proyecto

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #252526; color: #cccccc; border: 1px solid #454545; } QMenu::item:selected { background-color: #094771; }")

        accion_nuevo_archivo = QAction(qta.icon('fa5s.file'), "Nuevo Archivo", self)
        accion_nueva_carpeta = QAction(qta.icon('fa5s.folder'), "Nueva Carpeta", self)
        accion_eliminar = QAction(qta.icon('fa5s.trash-alt', color='#ff5c5c'), "Eliminar", self)

        accion_nuevo_archivo.triggered.connect(lambda: self.crear_elemento_explorador(ruta_origen, es_carpeta=False))
        accion_nueva_carpeta.triggered.connect(lambda: self.crear_elemento_explorador(ruta_origen, es_carpeta=True))
        accion_eliminar.triggered.connect(lambda: self.eliminar_elemento_explorador(ruta_origen))

        menu.addAction(accion_nuevo_archivo)
        menu.addAction(accion_nueva_carpeta)
        
        if item and ruta_origen != self.ruta_proyecto:
            menu.addSeparator()
            menu.addAction(accion_eliminar)

        menu.exec(self.file_explorer.viewport().mapToGlobal(pos))

    def crear_elemento_explorador(self, ruta_origen, es_carpeta):
        ruta_base = ruta_origen if os.path.isdir(ruta_origen) else os.path.dirname(ruta_origen)
        
        tipo = "Carpeta" if es_carpeta else "Archivo"
        nombre, ok = QInputDialog.getText(self, f"Nuevo {tipo}", f"Nombre del {tipo.lower()}:")

        if ok and nombre:
            ruta_completa = os.path.join(ruta_base, nombre)
            try:
                if es_carpeta:
                    os.makedirs(ruta_completa, exist_ok=True)
                else:
                    with open(ruta_completa, 'w', encoding='utf-8') as f:
                        pass 
                    self.abrir_archivo_desde_ruta(ruta_completa)
                    
                self.cargar_proyecto_en_arbol(self.ruta_proyecto)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear: {str(e)}")

    def eliminar_elemento_explorador(self, ruta_origen):
        if not ruta_origen or ruta_origen == self.ruta_proyecto: return
        
        es_carpeta = os.path.isdir(ruta_origen)
        nombre = os.path.basename(ruta_origen)

        respuesta = QMessageBox.question(
            self, 
            "Confirmar Eliminación", 
            f"¿Estás seguro de que deseas eliminar permanentemente '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            try:
                if es_carpeta:
                    shutil.rmtree(ruta_origen) 
                else:
                    os.remove(ruta_origen)
                    self.cerrar_pestana_por_ruta(ruta_origen) 
                    
                self.cargar_proyecto_en_arbol(self.ruta_proyecto)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {str(e)}")

    def cerrar_pestana_por_ruta(self, ruta):
        ruta_norm = os.path.normpath(ruta)
        for i in range(self.editor_stack.count()):
            ed = self.editor_stack.widget(i)
            if hasattr(ed, 'file_path') and ed.file_path and os.path.normpath(ed.file_path) == ruta_norm:
                self.cerrar_pestana(i)
                break

    def guardar_archivo(self):
        ed = self.editor_actual()
        if ed:
            if hasattr(ed, 'file_path') and ed.file_path:
                with open(ed.file_path, 'w', encoding='utf-8') as f:
                    f.write(ed.toPlainText())
                name = os.path.basename(ed.file_path)
                cur = self.file_tabs_bar.currentIndex()
                if cur != -1:
                    self.file_tabs_bar.setTabText(cur, name)

                self.status_bar.showMessage(f"Archivo guardado: {name}", 3000)
            else:
                self.guardar_como()

    def guardar_como(self):
        ed = self.editor_actual()
        if ed:
            path, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "Archivos de texto (*.txt);;Todos (*)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(ed.toPlainText())
                
                ed.file_path = path
                name = os.path.basename(path)
                cur = self.file_tabs_bar.currentIndex()
                if cur != -1:
                    self.file_tabs_bar.setTabText(cur, name)

                self.status_bar.showMessage(f"Archivo guardado como: {name}", 3000)

    def cerrar_archivo_actual(self):
        idx = self.file_tabs_bar.currentIndex()
        if idx != -1:
            self.cerrar_pestana(idx)

    def cerrar_pestana(self, index):
        widget = self.editor_stack.widget(index)
        self.editor_stack.removeWidget(widget)
        self.file_tabs_bar.removeTab(index)
        widget.deleteLater()
        
        if self.file_tabs_bar.count() == 0:
            self.view_stack.setCurrentIndex(0)
            self.status_bar.clearMessage()
        
        self.actualizar_estado_ui()

    def cerrar_pestana_desde_boton(self):
        boton_presionado = self.sender() 
        for i in range(self.file_tabs_bar.count()):
            if self.file_tabs_bar.tabButton(i, QTabBar.RightSide) == boton_presionado:
                self.cerrar_pestana(i)
                break

    def cambiar_archivo_activo(self, index):
        self.editor_stack.setCurrentIndex(index)
        self.actualizar_status()
        self.actualizar_estado_ui()

    def actualizar_status(self):
        ed = self.editor_actual()
        if ed:
            cursor = ed.textCursor()
            caracteres = len(ed.toPlainText())
            self.status_bar.showMessage(f"Línea: {cursor.blockNumber()+1} | Columna: {cursor.columnNumber()} | Caracteres: {caracteres}")

    def recargar_pestanas_abiertas(self, rutas_a_recargar):
        rutas_normalizadas = [os.path.normcase(os.path.normpath(r)) for r in rutas_a_recargar]

        for i in range(self.editor_stack.count()):
            ed = self.editor_stack.widget(i)
            
            if hasattr(ed, 'file_path') and ed.file_path:
                ruta_editor = os.path.normcase(os.path.normpath(ed.file_path))
                
                if ruta_editor in rutas_normalizadas:
                    if os.path.exists(ed.file_path):
                        try:
                            with open(ed.file_path, 'r', encoding='utf-8') as f:
                                nuevo_texto = f.read()
                            
                            if ed.toPlainText() != nuevo_texto:
                                cursor = ed.textCursor()
                                posicion = cursor.position()
                                
                                ed.setPlainText(nuevo_texto)
                                
                                cursor.setPosition(min(posicion, len(nuevo_texto)))
                                ed.setTextCursor(cursor)
                        except Exception as e:
                            print(f"No se pudo recargar el archivo {ed.file_path}: {e}")

    def obtener_codigo(self):
        ed = self.editor_actual()
        if not ed:
            return None
        return ed.toPlainText()

    def ejecutar_lexico(self):
        ed = self.editor_actual()
        if not ed: return

        if not hasattr(ed, 'file_path') or not ed.file_path:
            self.guardar_como()
            if not ed.file_path: return

        if not ed.toPlainText().strip():
            self.status_bar.showMessage("El archivo está vacío. Escribe algo de código primero.", 3000)
            return

        self.guardar_archivo()
        self.restaurar_panel_derecho()
        self.restaurar_panel_inferior()
        self.status_bar.showMessage("Ejecutando Análisis Léxico externo...", 3000)

        DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
        RUTA_COMPILADOR = os.path.join(DIRECTORIO_BASE, "comp", "lexer.py")

        directorio, archivo = os.path.split(ed.file_path)
        nombre_base, _ = os.path.splitext(archivo)
        
        out_dir = os.path.join(directorio, ".compilados")
        os.makedirs(out_dir, exist_ok=True)
        
        ruta_tokens = os.path.join(out_dir, f"{nombre_base}_tokens.txt")
        ruta_errores = os.path.join(out_dir, f"{nombre_base}_errores.txt")

        if os.path.exists(ruta_tokens):
            os.remove(ruta_tokens)
        if os.path.exists(ruta_errores):
            os.remove(ruta_errores)

        try:
            proceso = subprocess.run(
                [sys.executable, RUTA_COMPILADOR, ed.file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace' 
            )
            
            tabla_tokens = self.tabs_analisis.widget(0)
            tabla_tokens.setRowCount(0) 

            if os.path.exists(ruta_tokens):
                with open(ruta_tokens, 'r', encoding='utf-8') as f_tok:
                    lineas = f_tok.readlines()
                
                for linea in lineas[2:]:
                    if not linea.strip(): continue
                    
                    partes = linea.split('|')
                    if len(partes) == 4:
                        token = partes[0].split(':', 1)[1].strip()
                        lexema = partes[1].split(':', 1)[1].strip()
                        fila = partes[2].split(':', 1)[1].strip()
                        columna = partes[3].split(':', 1)[1].strip()

                        row_position = tabla_tokens.rowCount()
                        tabla_tokens.insertRow(row_position)
                        tabla_tokens.setItem(row_position, 0, QTableWidgetItem(token))
                        tabla_tokens.setItem(row_position, 1, QTableWidgetItem(lexema))
                        tabla_tokens.setItem(row_position, 2, QTableWidgetItem(fila))
                        tabla_tokens.setItem(row_position, 3, QTableWidgetItem(columna))
            else:
                tabla_tokens.insertRow(0)
                tabla_tokens.setItem(0, 0, QTableWidgetItem("ERROR"))
                tabla_tokens.setItem(0, 1, QTableWidgetItem("El compilador falló y no generó el archivo de tokens."))

            self.tabs_analisis.setCurrentIndex(0)

            if os.path.exists(ruta_errores):
                with open(ruta_errores, 'r', encoding='utf-8') as f_err:
                    contenido_errores = f_err.read()
                
                self.consola_inferior.widget(0).setPlainText(contenido_errores)
                self.consola_inferior.setCurrentIndex(0) 
            else:
                self.consola_inferior.widget(0).setPlainText(f">> No se generó el archivo de errores.\nSalida de la consola:\n{proceso.stderr}")
                self.consola_inferior.setCurrentIndex(0)

            self.recargar_pestanas_abiertas([ruta_tokens, ruta_errores])
            
            if self.ruta_proyecto:
                self.cargar_proyecto_en_arbol(self.ruta_proyecto)

        except Exception as e:
            self.consola_inferior.widget(0).setPlainText(f"Error crítico al intentar ejecutar el compilador:\n{str(e)}")
            self.consola_inferior.setCurrentIndex(0)

    def _poblar_arbol_sintactico(self, nodo_datos, parent_item):
        if not isinstance(nodo_datos, dict):
            return
            
        tipo = nodo_datos.get("tipo", "")
        valor = nodo_datos.get("valor", "")
        
        texto_item = tipo
        if valor:
            texto_item += f": {valor}"
            
        item = QTreeWidgetItem(parent_item, [texto_item])
        
        if tipo == "programa":
            item.setIcon(0, qta.icon('fa5s.laptop-code', color='#4ebfff'))
        elif tipo in ["keyword", "tipo_dato"]:
            item.setIcon(0, qta.icon('fa5s.key', color='#c586c0'))
        elif tipo == "id":
            item.setIcon(0, qta.icon('fa5s.tag', color='#9cdcfe'))
        elif tipo in ["numero", "booleano", "cadena", "literal"]:
            item.setIcon(0, qta.icon('fa5s.cube', color='#b5cea8'))
        elif tipo in ["simbolo", "operador", "op_relacional", "suma_op", "mult_op", "pot_op", "op_logico"]:
            item.setIcon(0, qta.icon('fa5s.cog', color='#d4d4d4'))
        else:
            item.setIcon(0, qta.icon('fa5s.folder', color='#dcb67a'))
            
        hijos = nodo_datos.get("hijos", [])
        for hijo in hijos:
            self._poblar_arbol_sintactico(hijo, item)
            
        item.setExpanded(True)

    def ejecutar_sintactico(self):
        ed = self.editor_actual()
        if not ed or not hasattr(ed, 'file_path') or not ed.file_path: return
        
        self.guardar_archivo()
        self.restaurar_panel_derecho()
        self.restaurar_panel_inferior()
        self.status_bar.showMessage("Ejecutando Análisis Sintáctico...", 3000)

        directorio, archivo = os.path.split(ed.file_path)
        nombre_base, _ = os.path.splitext(archivo)
        
        out_dir = os.path.join(directorio, ".compilados")
        os.makedirs(out_dir, exist_ok=True)
        
        ruta_tokens = os.path.join(out_dir, f"{nombre_base}_tokens.txt")
        ruta_ast = os.path.join(out_dir, f"{nombre_base}_ast.json")
        ruta_errores = os.path.join(out_dir, f"{nombre_base}_errores_sintacticos.txt")
        
        if not os.path.exists(ruta_tokens):
            self.consola_inferior.widget(1).setPlainText("Error: No se encontro archivo de tokens. Ejecute analisis lexico primero.")
            self.consola_inferior.setCurrentIndex(1)
            return

        DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
        RUTA_PARSER = os.path.join(DIRECTORIO_BASE, "comp", "parser.py")
        
        try:
            proceso = subprocess.run(
                [sys.executable, RUTA_PARSER, ruta_tokens],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            arbol_sintactico = self.tabs_analisis.widget(1)
            arbol_sintactico.clear()
            
            if os.path.exists(ruta_ast):
                with open(ruta_ast, 'r', encoding='utf-8') as f:
                    ast_data = json.load(f)
                self._poblar_arbol_sintactico(ast_data, arbol_sintactico)
            else:
                QTreeWidgetItem(arbol_sintactico, ["Error: No se genero el AST."])
                
            self.tabs_analisis.setCurrentIndex(1)
            
            if os.path.exists(ruta_errores):
                with open(ruta_errores, 'r', encoding='utf-8') as f_err:
                    contenido_errores = f_err.read()
                
                self.consola_inferior.widget(1).setPlainText(contenido_errores)
                self.consola_inferior.setCurrentIndex(1) 
            else:
                self.consola_inferior.widget(1).setPlainText(f">> No se generó el archivo de errores sintácticos.\nSalida:\n{proceso.stderr}")
                self.consola_inferior.setCurrentIndex(1)
                
        except Exception as e:
            self.consola_inferior.widget(1).setPlainText(f"Error crítico en analizador sintáctico:\n{str(e)}")
            self.consola_inferior.setCurrentIndex(1)

    def ejecutar_semantico(self):
        if self.obtener_codigo() is None: return
        self.restaurar_panel_derecho() 
        self.status_bar.showMessage("Ejecutando Análisis Semántico...", 3000)
        simulacion = ">> INICIANDO ANÁLISIS SEMÁNTICO...\n\n[OK] Verificación de tipos exitosa.\n[OK] Ámbitos de variables validados.\n\n>> Análisis semántico finalizado."
        self.tabs_analisis.widget(2).setPlainText(simulacion)
        self.tabs_analisis.setCurrentIndex(2)

    def ejecutar_codigo_intermedio(self):
        if self.obtener_codigo() is None: return
        self.restaurar_panel_derecho() 
        self.status_bar.showMessage("Generando Código Intermedio...", 3000)
        simulacion = ">> GENERANDO CÓDIGO INTERMEDIO (Tres Direcciones)...\n\nt1 = 5\nt2 = 10\nt3 = t1 + t2\na = t3\ngoto L1\n"
        self.tabs_analisis.widget(4).setPlainText(simulacion)
        self.tabs_analisis.setCurrentIndex(4)

    def ejecutar_programa(self):
        if self.obtener_codigo() is None: return
        
        self.status_bar.showMessage("Compilando todo el proyecto...", 3000)
        self.ejecutar_lexico()
        self.ejecutar_sintactico()
        self.ejecutar_semantico()
        self.ejecutar_codigo_intermedio()
        
        self.restaurar_panel_inferior() 
        self.status_bar.showMessage("Ejecutando Programa...", 3000)
        simulacion = ">> EJECUCIÓN INICIADA...\n\nHola Mundo!\n\n>> Proceso terminado con código de salida 0."
        self.consola_inferior.widget(3).setPlainText(simulacion)
        self.consola_inferior.setCurrentIndex(3)

    def crear_menus_y_herramientas(self):
        menu = self.menuBar()
        archivo_menu = menu.addMenu("&Archivo")
        
        self.action_nuevo = QAction("Nuevo", self)
        self.action_nuevo.setShortcut("Ctrl+N")
        self.action_nuevo.triggered.connect(self.nuevo_archivo)
        
        self.action_abrir = QAction("Abrir Archivo", self)
        self.action_abrir.setShortcut("Ctrl+O")
        self.action_abrir.triggered.connect(self.abrir_archivo)

        self.action_abrir_carpeta = QAction("Abrir Carpeta", self)
        self.action_abrir_carpeta.setShortcut("Ctrl+K")
        self.action_abrir_carpeta.triggered.connect(self.abrir_carpeta)
        
        self.action_cerrar = QAction("Cerrar Editor", self)
        self.action_cerrar.setShortcut("Ctrl+F4")
        self.action_cerrar.triggered.connect(self.cerrar_archivo_actual)
        
        self.action_guardar = QAction("Guardar", self)
        self.action_guardar.setShortcut("Ctrl+S")
        self.action_guardar.triggered.connect(self.guardar_archivo)
        
        self.action_guardar_como = QAction("Guardar como...", self)
        self.action_guardar_como.setShortcut("Ctrl+Shift+S")
        self.action_guardar_como.triggered.connect(self.guardar_como)
        
        self.action_salir = QAction("Salir", self)
        self.action_salir.setShortcut("Alt+F4")
        self.action_salir.triggered.connect(self.close)

        archivo_menu.addAction(self.action_nuevo)
        archivo_menu.addAction(self.action_abrir)
        archivo_menu.addAction(self.action_abrir_carpeta)
        archivo_menu.addAction(self.action_cerrar)
        archivo_menu.addAction(self.action_guardar)
        archivo_menu.addAction(self.action_guardar_como)
        archivo_menu.addSeparator()
        archivo_menu.addAction(self.action_salir)

        compilar_menu = menu.addMenu("&Compilar")
        
        self.action_lexico = QAction("Análisis Léxico", self)
        self.action_lexico.setShortcut("F6")
        self.action_lexico.triggered.connect(self.ejecutar_lexico)
        
        self.action_sintactico = QAction("Análisis Sintáctico", self)
        self.action_sintactico.setShortcut("F7")
        self.action_sintactico.triggered.connect(self.ejecutar_sintactico)
        
        self.action_semantico = QAction("Análisis Semántico", self)
        self.action_semantico.setShortcut("F8")
        self.action_semantico.triggered.connect(self.ejecutar_semantico)
        
        self.action_intermedio = QAction("Generación de Código Intermedio", self)
        self.action_intermedio.setShortcut("F9")
        self.action_intermedio.triggered.connect(self.ejecutar_codigo_intermedio)
        
        self.action_run = QAction("Ejecución", self)
        self.action_run.setShortcut("F5")
        self.action_run.triggered.connect(self.ejecutar_programa)

        compilar_menu.addAction(self.action_lexico)
        compilar_menu.addAction(self.action_sintactico)
        compilar_menu.addAction(self.action_semantico)
        compilar_menu.addAction(self.action_intermedio)
        compilar_menu.addSeparator()
        compilar_menu.addAction(self.action_run)