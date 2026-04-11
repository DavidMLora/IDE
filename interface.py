# interface.py
import os
import sys
import subprocess
from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QTextEdit, 
                             QStatusBar, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QTabBar, QStackedWidget, QToolButton,
                             QFileDialog, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QTreeView,QFileSystemModel)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize
import qtawesome as qta

from editor import CodeEditor
from welcome import WelcomeScreen
from styles import GLOBAL_STYLES
from terminal import TerminalIntegrada

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

        self.top_btn_new = self._create_tool_button('fa5s.file-medical', "Nuevo")
        self.top_btn_open = self._create_tool_button('fa5s.folder-open', "Abrir Archivo")
        self.top_btn_open_folder = self._create_tool_button('fa5s.folder-plus', "Abrir Carpeta de Proyecto")
        self.top_btn_save = self._create_tool_button('fa5s.save', "Guardar")
        self.top_btn_save_as = self._create_tool_button('fa5s.save', "Guardar como")
        self.top_btn_close = self._create_tool_button('fa5s.window-close', "Cerrar")

        self.top_btn_new.setObjectName('top_toolbar_btn')
        self.top_btn_open.setObjectName('top_toolbar_btn')
        self.top_btn_open_folder.setObjectName('top_toolbar_btn')
        self.top_btn_save.setObjectName('top_toolbar_btn')
        self.top_btn_save_as.setObjectName('top_toolbar_btn')
        self.top_btn_close.setObjectName('top_toolbar_btn')

        self.top_btn_new.clicked.connect(self.nuevo_archivo)
        self.top_btn_open.clicked.connect(self.abrir_archivo)
        self.top_btn_open_folder.clicked.connect(self.abrir_carpeta)
        self.top_btn_save.clicked.connect(self.guardar_archivo)
        self.top_btn_save_as.clicked.connect(self.guardar_como)
        self.top_btn_close.clicked.connect(self.cerrar_archivo_actual)

        self.header_layout.addWidget(self.top_btn_new)
        self.header_layout.addWidget(self.top_btn_open)
        self.header_layout.addWidget(self.top_btn_open_folder)
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

        self.header_layout.addWidget(self.file_tabs_bar)
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
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(6, 6, 6, 6)
        sidebar_layout.setSpacing(6)

        sidebar_title = QLabel("EXPLORADOR")
        sidebar_title.setObjectName('sidebar_title')
        sidebar_layout.addWidget(sidebar_title)

        # MODELO DE SISTEMA DE ARCHIVOS (ESTILO VS CODE)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("") 
        
        self.file_explorer = QTreeView()
        self.file_explorer.setObjectName('file_explorer')
        self.file_explorer.setModel(self.file_model)
        self.file_explorer.setRootIndex(self.file_model.index("")) # Oculto hasta abrir carpeta
        self.file_explorer.setHeaderHidden(True)
        
        # Ocultar columnas de tamaño, tipo y fecha
        for i in range(1, 4):
            self.file_explorer.hideColumn(i)
            
        self.file_explorer.clicked.connect(self._on_explorer_item_clicked)
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

    def _on_explorer_item_clicked(self, index):
        if not self.file_model.isDir(index):
            ruta = self.file_model.filePath(index)
            self.abrir_archivo_desde_ruta(ruta)

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
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(10, 10, 5, 5)
        editor_layout.addWidget(self.view_stack)
        
        self.h_splitter = QSplitter(Qt.Horizontal)
        self.h_splitter.addWidget(self.sidebar)
        self.h_splitter.addWidget(self.editor_container)
        
        self.panel_derecho = QWidget()
        panel_derecho_layout = QVBoxLayout(self.panel_derecho)
        panel_derecho_layout.setContentsMargins(5, 10, 10, 5)
        
        right_header = QWidget()
        rh_layout = QHBoxLayout(right_header)
        rh_layout.setContentsMargins(0, 0, 0, 0)
        rh_layout.setSpacing(6)
        right_title = QLabel("Panel de Análisis")
        rh_layout.addWidget(right_title)
        rh_layout.addStretch()
        btn_close_right = QToolButton()
        btn_close_right.setIcon(qta.icon('fa5s.times', color='#ff5c5c'))
        btn_close_right.setIconSize(QSize(16, 16))
        btn_close_right.setFixedSize(28, 28)
        btn_close_right.setToolTip("Cerrar panel de análisis")
        btn_close_right.setStyleSheet("QToolButton { background: transparent; border-radius: 4px; } QToolButton:hover { background: rgba(255,92,92,0.12); }")
        btn_close_right.clicked.connect(self.close_panel_derecho)
        rh_layout.addWidget(btn_close_right)

        panel_derecho_layout.addWidget(right_header)
        panel_derecho_layout.addWidget(self.tabs_analisis)
        self.h_splitter.addWidget(self.panel_derecho)

        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.addWidget(self.h_splitter)
        
        self.panel_inferior = QWidget()
        panel_inferior_layout = QVBoxLayout(self.panel_inferior)
        panel_inferior_layout.setContentsMargins(10, 5, 10, 10)
        
        bottom_header = QWidget()
        bh_layout = QHBoxLayout(bottom_header)
        bh_layout.setContentsMargins(0, 0, 0, 0)
        bh_layout.setSpacing(6)
        bottom_title = QLabel("Consola")
        bh_layout.addWidget(bottom_title)
        bh_layout.addStretch()
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

        self.v_splitter.setStretchFactor(0, 3)
        self.v_splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.v_splitter)

    def actualizar_estado_ui(self):
        hay_archivo = self.editor_actual() is not None

        if not hay_archivo:
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
        self.panel_derecho.setVisible(True)
        sizes = self.h_splitter.sizes()
        if len(sizes) >= 3 and sizes[2] == 0:
            total = sum(sizes) or self.width()
            self.h_splitter.setSizes([int(total * 0.15), int(total * 0.7), int(total * 0.15)])
        elif len(sizes) == 2 and sizes[1] == 0:
            total = sum(sizes) or self.width()
            self.h_splitter.setSizes([int(total * 0.7), int(total * 0.3)])

    def restaurar_panel_inferior(self):
        self.panel_inferior.setVisible(True)
        sizes = self.v_splitter.sizes()
        if sizes[1] == 0:  
            total = sum(sizes) or self.height()
            self.v_splitter.setSizes([int(total * 0.75), int(total * 0.25)])

    def close_panel_derecho(self):
        self.panel_derecho.setVisible(False)
        sizes = self.h_splitter.sizes()
        total = sum(sizes) or self.width()
        self.h_splitter.setSizes([int(total * 0.15), int(total * 0.85), 0])

    def close_panel_inferior(self):
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
            self.file_model.setRootPath(carpeta)
            self.file_explorer.setRootIndex(self.file_model.index(carpeta))
            os.chdir(carpeta)
            
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.cambiar_directorio(carpeta)
                
            self.status_bar.showMessage(f"Carpeta de proyecto abierta: {carpeta}", 5000)

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
        """
        Busca si los archivos generados están abiertos en alguna pestaña del IDE
        y actualiza su contenido leyendo el disco duro nuevamente.
        """
        import os
        
        # 1. Normalizamos las rutas objetivo (convierte todas las / y \ al mismo formato)
        rutas_normalizadas = [os.path.normcase(os.path.normpath(r)) for r in rutas_a_recargar]

        for i in range(self.editor_stack.count()):
            ed = self.editor_stack.widget(i)
            
            # 2. Verificamos que el editor tenga un archivo asignado
            if hasattr(ed, 'file_path') and ed.file_path:
                # Normalizamos la ruta de la pestaña actual
                ruta_editor = os.path.normcase(os.path.normpath(ed.file_path))
                
                # 3. Comparamos las rutas normalizadas
                if ruta_editor in rutas_normalizadas:
                    if os.path.exists(ed.file_path):
                        try:
                            with open(ed.file_path, 'r', encoding='utf-8') as f:
                                nuevo_texto = f.read()
                            
                            # Solo actualizamos el texto si realmente cambió
                            if ed.toPlainText() != nuevo_texto:
                                cursor = ed.textCursor()
                                posicion = cursor.position()
                                
                                ed.setPlainText(nuevo_texto)
                                
                                cursor.setPosition(min(posicion, len(nuevo_texto)))
                                ed.setTextCursor(cursor)
                        except Exception as e:
                            print(f"No se pudo recargar el archivo {ed.file_path}: {e}")
        """
        Busca si los archivos generados están abiertos en alguna pestaña del IDE
        y actualiza su contenido leyendo el disco duro nuevamente.
        """
        import os
        for i in range(self.editor_stack.count()):
            ed = self.editor_stack.widget(i)
            # Verificamos si la pestaña actual tiene un archivo asociado y si es uno de los que queremos recargar
            if hasattr(ed, 'file_path') and ed.file_path in rutas_a_recargar:
                if os.path.exists(ed.file_path):
                    with open(ed.file_path, 'r', encoding='utf-8') as f:
                        nuevo_texto = f.read()
                    
                    # Solo actualizamos el texto si realmente cambió (evita parpadeos en la pantalla)
                    if ed.toPlainText() != nuevo_texto:
                        # Guardamos la posición del cursor para que la pantalla no salte hasta arriba
                        cursor = ed.textCursor()
                        posicion = cursor.position()
                        
                        ed.setPlainText(nuevo_texto)
                        
                        # Restauramos el cursor
                        cursor.setPosition(min(posicion, len(nuevo_texto)))
                        ed.setTextCursor(cursor)
    def obtener_codigo(self):
        ed = self.editor_actual()
        if not ed:
            return None
        return ed.toPlainText()

    def ejecutar_lexico(self):
        import sys
        import os
        import subprocess

        ed = self.editor_actual()
        if not ed: return

        if not hasattr(ed, 'file_path') or not ed.file_path:
            self.guardar_como()
            if not ed.file_path: return

        # El IDE solo guarda su propio código fuente (esto sí le toca al IDE)
        self.guardar_archivo()
        self.restaurar_panel_derecho()
        self.restaurar_panel_inferior()
        self.status_bar.showMessage("Ejecutando Análisis Léxico externo...", 3000)

        DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
        RUTA_COMPILADOR = os.path.join(DIRECTORIO_BASE, "comp", "lexer.py")

        try:
            # Mandamos a llamar al lexer.py (Él ya se encarga de sobreescribir y guardar bien)
            proceso = subprocess.run(
                [sys.executable, RUTA_COMPILADOR, ed.file_path],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # Reconstruimos la ruta para leer lo que el lexer acaba de crear
            directorio, archivo = os.path.split(ed.file_path)
            nombre_base, _ = os.path.splitext(archivo)
            ruta_tokens = os.path.join(directorio, f"{nombre_base}_tokens.txt")
            ruta_errores = os.path.join(directorio, f"{nombre_base}_errores.txt")

            tabla_tokens = self.tabs_analisis.widget(0)
            tabla_tokens.setRowCount(0) 

            # Llenar la tabla de tokens
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
                tabla_tokens.setItem(0, 0, QTableWidgetItem("ERROR CRÍTICO"))
                tabla_tokens.setItem(0, 1, QTableWidgetItem("El compilador se ejecutó pero NO creó el archivo de tokens."))
                self.consola_inferior.widget(0).setPlainText(f"Salida de la consola:\n{proceso.stderr}\n{proceso.stdout}")
                self.consola_inferior.setCurrentIndex(0) 

            self.tabs_analisis.setCurrentIndex(0)

            # Llenar la consola de errores
            if os.path.exists(ruta_errores):
                with open(ruta_errores, 'r', encoding='utf-8') as f_err:
                    contenido_errores = f_err.read()
                
                self.consola_inferior.widget(0).setPlainText(contenido_errores)
                if proceso.returncode != 0:
                    self.consola_inferior.setCurrentIndex(0) 
            else:
                self.consola_inferior.widget(0).setPlainText(">> No se generó el archivo de errores.")

        except Exception as e:
            self.consola_inferior.widget(0).setPlainText(f"Error al intentar ejecutar el compilador:\n{str(e)}")
            self.consola_inferior.setCurrentIndex(0)
        ed = self.editor_actual()
        if not ed: return

        if not hasattr(ed, 'file_path') or not ed.file_path:
            self.guardar_como()
            if not ed.file_path: return

        # 1. Guardar los cambios del editor en el archivo físico
        self.guardar_archivo()
        self.restaurar_panel_derecho()
        self.restaurar_panel_inferior()
        self.status_bar.showMessage("Ejecutando Análisis Léxico externo...", 3000)

        DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
        RUTA_COMPILADOR = os.path.join(DIRECTORIO_BASE, "comp", "lexer.py")

        # 2. Reconstruir rutas de los archivos de salida
        directorio, archivo = os.path.split(ed.file_path)
        nombre_base, _ = os.path.splitext(archivo)
        ruta_tokens = os.path.join(directorio, f"{nombre_base}_tokens.txt")
        ruta_errores = os.path.join(directorio, f"{nombre_base}_errores.txt")

        # 3. ELIMINAR LOS ARCHIVOS VIEJOS (Para evitar Datos Fantasma)
        if os.path.exists(ruta_tokens):
            os.remove(ruta_tokens)
        if os.path.exists(ruta_errores):
            os.remove(ruta_errores)

        try:
            # 4. Usar sys.executable asegura que se use el mismo Python (soluciona conflictos py vs python)
            proceso = subprocess.run(
                [sys.executable, RUTA_COMPILADOR, ed.file_path],
                capture_output=True,
                text=True,
                encoding='cp1252'
            )
            
            # Limpiar la tabla antes de llenarla
            tabla_tokens = self.tabs_analisis.widget(0)
            tabla_tokens.setRowCount(0) 

            # Llenar la tabla solo si el archivo nuevo fue creado con éxito
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

            # Revisar el archivo de errores
            if os.path.exists(ruta_errores):
                with open(ruta_errores, 'r', encoding='utf-8') as f_err:
                    contenido_errores = f_err.read()
                
                self.consola_inferior.widget(0).setPlainText(contenido_errores)
                if proceso.returncode != 0:
                    self.consola_inferior.setCurrentIndex(0) 
            else:
                self.consola_inferior.widget(0).setPlainText(f">> No se generó el archivo de errores.\nSalida de la consola:\n{proceso.stderr}")

        except Exception as e:
            self.consola_inferior.widget(0).setPlainText(f"Error crítico al intentar ejecutar el compilador:\n{str(e)}")
            self.consola_inferior.setCurrentIndex(0)
        ed = self.editor_actual()
        if not ed: return

        if not hasattr(ed, 'file_path') or not ed.file_path:
            self.guardar_como()
            if not ed.file_path: return

        self.guardar_archivo()
        self.restaurar_panel_derecho()
        self.restaurar_panel_inferior()
        self.status_bar.showMessage("Ejecutando Análisis Léxico externo...", 3000)

        DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
        RUTA_COMPILADOR = os.path.join(DIRECTORIO_BASE, "comp", "lexer.py")

        try:
            proceso = subprocess.run(
                ['python', RUTA_COMPILADOR, ed.file_path],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            directorio, archivo = os.path.split(ed.file_path)
            nombre_base, _ = os.path.splitext(archivo)
            ruta_tokens = os.path.join(directorio, f"{nombre_base}_tokens.txt")
            ruta_errores = os.path.join(directorio, f"{nombre_base}_errores.txt")

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
                tabla_tokens.setItem(0, 1, QTableWidgetItem("No se encontró archivo _tokens.txt"))

            self.tabs_analisis.setCurrentIndex(0)

            if os.path.exists(ruta_errores):
                with open(ruta_errores, 'r', encoding='utf-8') as f_err:
                    contenido_errores = f_err.read()
                
                self.consola_inferior.widget(0).setPlainText(contenido_errores)
                if proceso.returncode != 0:
                    self.consola_inferior.setCurrentIndex(0) 
            else:
                self.consola_inferior.widget(0).setPlainText(">> No se generó el archivo de errores.")
            self.recargar_pestanas_abiertas([ruta_tokens, ruta_errores])
        except Exception as e:
            self.consola_inferior.widget(0).setPlainText(f"Error al intentar ejecutar el compilador:\n{str(e)}")
            self.consola_inferior.setCurrentIndex(0)

    def ejecutar_sintactico(self):
        if self.obtener_codigo() is None: return
        self.restaurar_panel_derecho() 
        self.status_bar.showMessage("Ejecutando Análisis Sintáctico...", 3000)
        simulacion = ">> INICIANDO ANÁLISIS SINTÁCTICO...\n\n PROGRAMA\n └── FUNCION_PRINCIPAL\n     ├── TIPO: int\n     ├── ID: main\n     └── BLOQUE\n         └── RETORNO: 0\n\n>> Análisis sintáctico finalizado."
        self.tabs_analisis.widget(1).setPlainText(simulacion)
        self.tabs_analisis.setCurrentIndex(1)

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