import os
from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QTextEdit, 
                             QStatusBar, QToolBar, QFileDialog, QWidget, 
                             QHBoxLayout, QVBoxLayout, QPushButton, QTabBar,
                             QStackedWidget,QToolButton,QLabel)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from editor import CodeEditor
import qtawesome as qta
from welcome import WelcomeScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE")
        self.resize(1200, 800)

        # Paneles de resultados y errores (Requerimientos 33, 54, 62) [cite: 33, 54, 62]
        self.tabs_analisis = QTabWidget() 
        self.consola_inferior = QTabWidget() 

        self.init_layout()
        self.crear_menus_y_herramientas()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Crear una pestaña vacía al inicio
       # self.nuevo_archivo()

    def init_layout(self):
        import qtawesome as qta # Importación local por seguridad

        # --- 1. CONTENEDOR PRINCIPAL DEL EDITOR (IZQUIERDA) ---
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)

        # --- 2. CABECERA MODERNA (Pestañas + Botones de Compilación) ---
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #1e1e1e;")
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0   , 0)
        self.header_layout.setSpacing(2)

        # Barra de pestañas (Requerimiento: Gestión de archivos/Cerrar)
        self.file_tabs_bar = QTabBar()
        self.file_tabs_bar.setTabsClosable(True)
        self.file_tabs_bar.setMovable(True)
        self.file_tabs_bar.tabCloseRequested.connect(self.cerrar_pestana)
        self.file_tabs_bar.currentChanged.connect(self.cambiar_archivo_activo)
        # En tu init_layout, cambia el estilo de la barra por este:
        self.file_tabs_bar.setStyleSheet("""
            QTabBar::tab {
                background: #333333; color: #bbbbbb;
                padding: 8px 30px 8px 15px; /* Más espacio a la derecha para el botón */
                border-right: 1px solid #222222;
            }
            QTabBar::tab:selected {
                background: #1e1e1e; color: white;
                border-bottom: 2px solid #007acc;
            }
            /* Eliminamos QTabBar::close-button ya que usamos un QToolButton manual */
        """)

        # --- 3. BOTONES DE ACCESO RÁPIDO (Requerimiento 2.2 del PDF) ---
        # Definimos estilo común para los botones
        estilo_iconos = """
            QPushButton { background: transparent; border: none; padding: 5px; border-radius: 4px; }
            QPushButton:hover { background-color: #3d3d3d; }
        """

        # Crear botones con iconos de Font Awesome
        self.btn_lexico = QPushButton()
        self.btn_lexico.setIcon(qta.icon('fa5s.search', color='#cccccc'))
        self.btn_lexico.setToolTip("Análisis Léxico")

        self.btn_sintactico = QPushButton()
        self.btn_sintactico.setIcon(qta.icon('fa5s.code-branch', color='#cccccc'))
        self.btn_sintactico.setToolTip("Análisis Sintáctico")

        self.btn_semantico = QPushButton()
        self.btn_semantico.setIcon(qta.icon('fa5s.check-circle', color='#cccccc'))
        self.btn_semantico.setToolTip("Análisis Semántico")

        self.btn_intermedio = QPushButton()
        self.btn_intermedio.setIcon(qta.icon('fa5s.file-code', color='#cccccc'))
        self.btn_intermedio.setToolTip("Generar Código Intermedio")

        self.btn_run = QPushButton()
        self.btn_run.setIcon(qta.icon('fa5s.play', color='#4ec9b0')) # Verde para el Run
        self.btn_run.setToolTip("Ejecutar Programa")

        # Aplicar estilo a todos
        for btn in [self.btn_lexico, self.btn_sintactico, self.btn_semantico, self.btn_intermedio, self.btn_run]:
            btn.setStyleSheet(estilo_iconos)
            btn.setFixedSize(32, 30)

        # Organizar Cabecera: Pestañas -> Espacio -> Botones
        self.header_layout.addWidget(self.file_tabs_bar)
        self.header_layout.addStretch() # El "resorte" que empuja los botones a la derecha
        self.header_layout.addWidget(self.btn_lexico)
        self.header_layout.addWidget(self.btn_sintactico)
        self.header_layout.addWidget(self.btn_semantico)
        self.header_layout.addWidget(self.btn_intermedio)
        self.header_layout.addWidget(self.btn_run)

        # --- 4. STACK DE VISTAS (PANTALLA INICIO vs EDITOR) ---
        self.view_stack = QStackedWidget()
        self.welcome_screen = WelcomeScreen(self)
        
        # Contenedor para cuando hay archivos abiertos
        self.editor_workspace = QWidget()
        workspace_layout = QVBoxLayout(self.editor_workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        
        self.editor_stack = QStackedWidget()
        
        # Añadimos la cabecera y el editor al workspace
        workspace_layout.addWidget(self.header_widget)
        workspace_layout.addWidget(self.editor_stack)
        
        # Añadimos ambas vistas al stack principal
        self.view_stack.addWidget(self.welcome_screen)    # Índice 0 (Inicio)
        self.view_stack.addWidget(self.editor_workspace)  # Índice 1 (Trabajo)
        
        # Añadir al contenedor izquierdo
        self.editor_layout.addWidget(self.view_stack)

        # --- 5. ENSAMBLAJE FINAL CON SPLITTERS (Requerimiento 5: Paneles simultáneos) ---
        # Splitter Horizontal: [ Editor | Paneles Análisis ]
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(self.editor_container)
        
        # Paneles de Análisis (Derecha)
        self.tabs_analisis.addTab(QTextEdit(), "Léxico")
        self.tabs_analisis.addTab(QTextEdit(), "Sintáctico")
        self.tabs_analisis.addTab(QTextEdit(), "Semántico")
        self.tabs_analisis.addTab(QTextEdit(), "Tabla Símbolos")
        self.tabs_analisis.addTab(QTextEdit(), "C. Intermedio")
        h_splitter.addWidget(self.tabs_analisis)

        # Splitter Vertical: [ Arriba (Editor+Analisis) | Abajo (Consola/Errores) ]
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(h_splitter)
        
        # Pestañas inferiores (Requerimientos 7 y 8 del PDF)
        self.consola_inferior.addTab(QTextEdit(), "Errores")
        self.consola_inferior.addTab(QTextEdit(), "Resultados")
        v_splitter.addWidget(self.consola_inferior)

        # Ajustar proporciones iniciales (70% arriba, 30% abajo)
        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(v_splitter)

    # --- LÓGICA DE ARCHIVOS ---
    def editor_actual(self):
        return self.editor_stack.currentWidget()

    def nuevo_archivo(self):
        nuevo_ed = CodeEditor()
        nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
        idx = self.editor_stack.addWidget(nuevo_ed)
        
        # 1. Añadimos la pestaña de texto
        self.file_tabs_bar.addTab("Sin título")
        
        # 2. Creamos un botón personalizado con Font Awesome para la "X"
        btn_cerrar = QToolButton()
        btn_cerrar.setIcon(qta.icon('fa5s.times', color='#bbbbbb')) # Icono 'X'
        btn_cerrar.setStyleSheet("""
            QToolButton { border: none; background: transparent; }
            QToolButton:hover { background: #e81123; border-radius: 2px; }
        """)
        
        # 3. Importante: Conectamos el botón a la lógica de cerrar
        # Usamos una función lambda para pasarle el índice actual
        btn_cerrar.clicked.connect(lambda: self.cerrar_pestana(self.file_tabs_bar.currentIndex()))
        
        # 4. Colocamos el botón en la pestaña
        self.file_tabs_bar.setTabButton(idx, QTabBar.RightSide, btn_cerrar)
        
        self.file_tabs_bar.setCurrentIndex(idx)
        self.view_stack.setCurrentIndex(1)

    def abrir_archivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Archivos de texto (*.txt);;Todos (*)")
        if path:
            nuevo_ed = CodeEditor()
            with open(path, 'r') as f:
                nuevo_ed.setPlainText(f.read())
            nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
            idx = self.editor_stack.addWidget(nuevo_ed)
            self.file_tabs_bar.addTab(os.path.basename(path))
            self.file_tabs_bar.setCurrentIndex(idx)
            self.view_stack.setCurrentIndex(1)
    def guardar_archivo(self):
        ed = self.editor_actual()
        if ed:
            path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "Archivos de texto (*.txt)")
            if path:
                with open(path, 'w') as f:
                    f.write(ed.toPlainText())
                self.file_tabs_bar.setTabText(self.file_tabs_bar.currentIndex(), os.path.basename(path))

    def cerrar_pestana(self, index):
        # Reemplazamos todo el método con esta nueva lógica
        widget = self.editor_stack.widget(index)
        self.editor_stack.removeWidget(widget)
        self.file_tabs_bar.removeTab(index)
        widget.deleteLater() # Liberar memoria del widget cerrado
        
        # Si ya no quedan pestañas, volvemos a la pantalla de inicio
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
            # Requerimiento 3.1: Línea y columna [cite: 37, 38]
            self.status_bar.showMessage(f"Línea: {cursor.blockNumber()+1} | Columna: {cursor.columnNumber()}")

    def crear_menus_y_herramientas(self):
        menu = self.menuBar()
        archivo_menu = menu.addMenu("&Archivo") # [cite: 9]
        
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