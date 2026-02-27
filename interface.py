# interface.py
import os
from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QTextEdit, 
                             QStatusBar, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QTabBar, QStackedWidget, QToolButton)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import qtawesome as qta

from editor import CodeEditor
from welcome import WelcomeScreen
from styles import GLOBAL_STYLES

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE")
        self.resize(1200, 800)
        self.setStyleSheet(GLOBAL_STYLES)

        # Contenedores principales
        self.tabs_analisis = QTabWidget()
        self.consola_inferior = QTabWidget()

        self._setup_ui()
        self.crear_menus_y_herramientas()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _setup_ui(self):
        """Organiza la construcción de la interfaz principal"""
        self._setup_header()
        self._setup_workspace()
        self._setup_panels()
        self._assemble_layout()

    def _setup_header(self):
        """Configura la barra de pestañas y botones de ejecución"""
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(10, 5, 10, 5)
        self.header_layout.setSpacing(10)

        # Barra de pestañas de archivos
        self.file_tabs_bar = QTabBar()
        self.file_tabs_bar.setTabsClosable(True)
        self.file_tabs_bar.setMovable(True)
        self.file_tabs_bar.tabCloseRequested.connect(self.cerrar_pestana)
        self.file_tabs_bar.currentChanged.connect(self.cambiar_archivo_activo)

        # Botones de herramientas
        self.btn_lexico = self._create_tool_button('fa5s.search', "Análisis Léxico")
        self.btn_sintactico = self._create_tool_button('fa5s.code-branch', "Análisis Sintáctico")
        self.btn_semantico = self._create_tool_button('fa5s.check-circle', "Análisis Semántico")
        self.btn_intermedio = self._create_tool_button('fa5s.file-code', "Generar Código Intermedio")
        self.btn_run = self._create_tool_button('fa5s.play', "Ejecutar Programa", color='#4ec9b0')

        self.header_layout.addWidget(self.file_tabs_bar)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_lexico)
        self.header_layout.addWidget(self.btn_sintactico)
        self.header_layout.addWidget(self.btn_semantico)
        self.header_layout.addWidget(self.btn_intermedio)
        self.header_layout.addWidget(self.btn_run)

    def _create_tool_button(self, icon_name, tooltip, color='#cccccc'):
        """Método auxiliar para crear botones uniformes"""
        btn = QPushButton()
        btn.setIcon(qta.icon(icon_name, color=color))
        btn.setToolTip(tooltip)
        btn.setFixedSize(36, 36)
        return btn

    def _setup_workspace(self):
        """Configura el área del editor y la pantalla de inicio"""
        self.view_stack = QStackedWidget()
        self.welcome_screen = WelcomeScreen(self)
        
        self.editor_workspace = QWidget()
        workspace_layout = QVBoxLayout(self.editor_workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        
        self.editor_stack = QStackedWidget()
        workspace_layout.addWidget(self.header_widget)
        workspace_layout.addWidget(self.editor_stack)
        
        self.view_stack.addWidget(self.welcome_screen)
        self.view_stack.addWidget(self.editor_workspace)

    def _setup_panels(self):
        """Configura los paneles laterales e inferiores"""
        paneles_analisis = ["Léxico", "Sintáctico", "Semántico", "Tabla Símbolos", "C. Intermedio"]
        for nombre in paneles_analisis:
            self.tabs_analisis.addTab(QTextEdit(), nombre)

        self.consola_inferior.addTab(QTextEdit(), "Errores")
        self.consola_inferior.addTab(QTextEdit(), "Resultados")

    def _assemble_layout(self):
        """Ensambla todos los componentes usando QSplitters"""
        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(10, 10, 5, 5)
        editor_layout.addWidget(self.view_stack)

        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(self.editor_container)
        
        panel_derecho = QWidget()
        panel_derecho_layout = QVBoxLayout(panel_derecho)
        panel_derecho_layout.setContentsMargins(5, 10, 10, 5)
        panel_derecho_layout.addWidget(self.tabs_analisis)
        h_splitter.addWidget(panel_derecho)

        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(h_splitter)
        
        panel_inferior = QWidget()
        panel_inferior_layout = QVBoxLayout(panel_inferior)
        panel_inferior_layout.setContentsMargins(10, 5, 10, 10)
        panel_inferior_layout.addWidget(self.consola_inferior)
        v_splitter.addWidget(panel_inferior)

        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 1)
        self.setCentralWidget(v_splitter)

    # --- LÓGICA DE ARCHIVOS MANTENIDA IGUAL, ESTILIZANDO LA 'X' ---
    def editor_actual(self):
        return self.editor_stack.currentWidget()

    def nuevo_archivo(self):
        nuevo_ed = CodeEditor()
        nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
        idx = self.editor_stack.addWidget(nuevo_ed)
        
        self.file_tabs_bar.addTab("Sin título")
        
        btn_cerrar = QToolButton()
        btn_cerrar.setIcon(qta.icon('fa5s.times', color='#bbbbbb'))
        btn_cerrar.clicked.connect(lambda: self.cerrar_pestana(self.file_tabs_bar.currentIndex()))
        self.file_tabs_bar.setTabButton(idx, QTabBar.RightSide, btn_cerrar)
        
        self.file_tabs_bar.setCurrentIndex(idx)
        self.view_stack.setCurrentIndex(1)

    def abrir_archivo(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Archivos de texto (*.txt);;Todos (*)")
        if path:
            nuevo_ed = CodeEditor()
            with open(path, 'r', encoding='utf-8') as f:
                nuevo_ed.setPlainText(f.read())
            nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
            idx = self.editor_stack.addWidget(nuevo_ed)
            self.file_tabs_bar.addTab(os.path.basename(path))
            self.file_tabs_bar.setCurrentIndex(idx)
            self.view_stack.setCurrentIndex(1)

    def guardar_archivo(self):
        from PySide6.QtWidgets import QFileDialog
        ed = self.editor_actual()
        if ed:
            path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "Archivos de texto (*.txt)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(ed.toPlainText())
                self.file_tabs_bar.setTabText(self.file_tabs_bar.currentIndex(), os.path.basename(path))

    def cerrar_pestana(self, index):
        widget = self.editor_stack.widget(index)
        self.editor_stack.removeWidget(widget)
        self.file_tabs_bar.removeTab(index)
        widget.deleteLater()
        
        if self.file_tabs_bar.count() == 0:
            self.view_stack.setCurrentIndex(0)
            self.status_bar.clearMessage()

    def cambiar_archivo_activo(self, index):
        self.editor_stack.setCurrentIndex(index)
        self.actualizar_status()

    def actualizar_status(self):
        ed = self.editor_actual()
        if ed:
            cursor = ed.textCursor()
            self.status_bar.showMessage(f"Línea: {cursor.blockNumber()+1} | Columna: {cursor.columnNumber()}")

    def crear_menus_y_herramientas(self):
        menu = self.menuBar()
        archivo_menu = menu.addMenu("&Archivo")
        
        acciones = [
            ("Nuevo", self.nuevo_archivo),
            ("Abrir", self.abrir_archivo),
            ("Guardar", self.guardar_archivo),
            ("Salir", self.close)
        ]

        for nombre, func in acciones:
            act = QAction(nombre, self)
            act.triggered.connect(func)
            archivo_menu.addAction(act)