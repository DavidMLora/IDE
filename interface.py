# interface.py
import os
from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QTextEdit, 
                             QStatusBar, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QTabBar, QStackedWidget, QToolButton,
                             QFileDialog)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize
import qtawesome as qta

from editor import CodeEditor
from welcome import WelcomeScreen
from styles import GLOBAL_STYLES

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE Compilador")
        self.resize(1200, 800)
        self.setStyleSheet(GLOBAL_STYLES)

        # Contenedores principales
        self.tabs_analisis = QTabWidget()
        self.consola_inferior = QTabWidget()

        self._setup_ui()
        self.crear_menus_y_herramientas()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Actualizar la interfaz al estado inicial (sin archivos)
        self.actualizar_estado_ui()

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

        # Conectar botones a las simulaciones
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
        """Método auxiliar para crear botones uniformes"""
        btn = QPushButton()
        # Añadimos 'disabled_color' para que el icono se vuelva gris oscuro automáticamente
        btn.setIcon(qta.icon(icon_name, color=color, disabled_color='#444444'))
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
            txt_edit = QTextEdit()
            txt_edit.setReadOnly(True)
            self.tabs_analisis.addTab(txt_edit, nombre)

        # Consolas inferiores
        for nombre in ["Errores Léxicos", "Errores Sintácticos", "Errores Semánticos", "Resultados"]:
            txt_edit = QTextEdit()
            txt_edit.setReadOnly(True)
            self.consola_inferior.addTab(txt_edit, nombre)

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

    # --- CONTROL DE ESTADO DE LA UI ---
    def actualizar_estado_ui(self):
        """Activa o desactiva botones y menús dependiendo de si hay un archivo abierto."""
        hay_archivo = self.editor_actual() is not None

        # Botones de herramientas superiores
        self.btn_lexico.setEnabled(hay_archivo)
        self.btn_sintactico.setEnabled(hay_archivo)
        self.btn_semantico.setEnabled(hay_archivo)
        self.btn_intermedio.setEnabled(hay_archivo)
        self.btn_run.setEnabled(hay_archivo)

        # Opciones del menú Archivo (si ya fueron creadas)
        if hasattr(self, 'action_cerrar'):
            self.action_cerrar.setEnabled(hay_archivo)
            self.action_guardar.setEnabled(hay_archivo)
            self.action_guardar_como.setEnabled(hay_archivo)

        # Opciones del menú Compilar (si ya fueron creadas)
        if hasattr(self, 'action_lexico'):
            self.action_lexico.setEnabled(hay_archivo)
            self.action_sintactico.setEnabled(hay_archivo)
            self.action_semantico.setEnabled(hay_archivo)
            self.action_intermedio.setEnabled(hay_archivo)
            self.action_run.setEnabled(hay_archivo)

    # --- LÓGICA DE ARCHIVOS ---
    def editor_actual(self):
        return self.editor_stack.currentWidget()

    def nuevo_archivo(self):
        nuevo_ed = CodeEditor()
        nuevo_ed.file_path = None # Atributo para saber si el archivo ya fue guardado en disco
        nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
        idx = self.editor_stack.addWidget(nuevo_ed)
        
        self.file_tabs_bar.addTab("Sin título")
        
        btn_cerrar = QToolButton()
        btn_cerrar.setIcon(qta.icon('fa5s.times', color='#bbbbbb'))
        btn_cerrar.setIconSize(QSize(10, 10))
        btn_cerrar.setFixedSize(20, 20)
        btn_cerrar.setStyleSheet("""
            QToolButton { border: none; padding: 0px; border-radius: 4px; }
            QToolButton:hover { background-color: #c42b1c; color: white; }
        """)
        btn_cerrar.clicked.connect(lambda: self.cerrar_pestana(self.file_tabs_bar.currentIndex()))
        
        self.file_tabs_bar.setTabButton(idx, QTabBar.RightSide, btn_cerrar)
        self.file_tabs_bar.setCurrentIndex(idx)
        self.view_stack.setCurrentIndex(1)
        self.actualizar_estado_ui() # Actualizamos la UI

    def abrir_archivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Archivos de texto (*.txt);;Todos (*)")
        if path:
            nuevo_ed = CodeEditor()
            with open(path, 'r', encoding='utf-8') as f:
                nuevo_ed.setPlainText(f.read())
            
            nuevo_ed.file_path = path # Guardamos la ruta del archivo abierto
            nuevo_ed.cursorPositionChanged.connect(self.actualizar_status)
            idx = self.editor_stack.addWidget(nuevo_ed)
            self.file_tabs_bar.addTab(os.path.basename(path))
            
            btn_cerrar = QToolButton()
            btn_cerrar.setIcon(qta.icon('fa5s.times', color='#bbbbbb'))
            btn_cerrar.setIconSize(QSize(10, 10))
            btn_cerrar.setFixedSize(20, 20)
            btn_cerrar.setStyleSheet("""
                QToolButton { border: none; padding: 0px; border-radius: 4px; }
                QToolButton:hover { background-color: #c42b1c; color: white; }
            """)
            btn_cerrar.clicked.connect(lambda: self.cerrar_pestana(self.file_tabs_bar.currentIndex()))
            self.file_tabs_bar.setTabButton(idx, QTabBar.RightSide, btn_cerrar)

            self.file_tabs_bar.setCurrentIndex(idx)
            self.view_stack.setCurrentIndex(1)
            self.actualizar_estado_ui() # Actualizamos la UI

    def guardar_archivo(self):
        ed = self.editor_actual()
        if ed:
            # Si el archivo ya tiene una ruta (fue abierto o guardado antes), sobreescribir
            if hasattr(ed, 'file_path') and ed.file_path:
                with open(ed.file_path, 'w', encoding='utf-8') as f:
                    f.write(ed.toPlainText())
                self.status_bar.showMessage(f"Archivo guardado: {os.path.basename(ed.file_path)}", 3000)
            else:
                # Si no tiene ruta (es "Sin título"), se comporta como Guardar Como
                self.guardar_como()

    def guardar_como(self):
        ed = self.editor_actual()
        if ed:
            path, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "Archivos de texto (*.txt);;Todos (*)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(ed.toPlainText())
                
                ed.file_path = path # Actualizamos la ruta en el editor
                self.file_tabs_bar.setTabText(self.file_tabs_bar.currentIndex(), os.path.basename(path))
                self.status_bar.showMessage(f"Archivo guardado como: {os.path.basename(path)}", 3000)

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
        
        self.actualizar_estado_ui() # Actualizamos la UI al cerrar

    def cambiar_archivo_activo(self, index):
        self.editor_stack.setCurrentIndex(index)
        self.actualizar_status()
        self.actualizar_estado_ui()

    def actualizar_status(self):
        ed = self.editor_actual()
        if ed:
            cursor = ed.textCursor()
            self.status_bar.showMessage(f"Línea: {cursor.blockNumber()+1} | Columna: {cursor.columnNumber()}")

    # --- SIMULACIÓN DE COMPILACIÓN ---
    def obtener_codigo(self):
        ed = self.editor_actual()
        if not ed:
            return None
        return ed.toPlainText()

    def ejecutar_lexico(self):
        codigo = self.obtener_codigo()
        if codigo is None: return

        self.status_bar.showMessage("Ejecutando Análisis Léxico...", 3000)
        simulacion = ">> INICIANDO ANÁLISIS LÉXICO...\n"
        simulacion += f">> Caracteres leídos: {len(codigo)}\n\n"
        simulacion += "Token: RESERVADA | Lexema: int | Fila: 1 | Col: 1\n"
        simulacion += "Token: IDENTIFICADOR | Lexema: main | Fila: 1 | Col: 5\n"
        simulacion += "Token: SIMBOLO | Lexema: ( | Fila: 1 | Col: 9\n"
        simulacion += "Token: SIMBOLO | Lexema: ) | Fila: 1 | Col: 10\n"
        simulacion += "\n>> Análisis léxico finalizado sin errores."

        self.tabs_analisis.widget(0).setPlainText(simulacion)
        self.tabs_analisis.setCurrentIndex(0)

    def ejecutar_sintactico(self):
        if self.obtener_codigo() is None: return
        self.status_bar.showMessage("Ejecutando Análisis Sintáctico...", 3000)
        simulacion = ">> INICIANDO ANÁLISIS SINTÁCTICO...\n\n PROGRAMA\n └── FUNCION_PRINCIPAL\n     ├── TIPO: int\n     ├── ID: main\n     └── BLOQUE\n         └── RETORNO: 0\n\n>> Análisis sintáctico finalizado."
        self.tabs_analisis.widget(1).setPlainText(simulacion)
        self.tabs_analisis.setCurrentIndex(1)

    def ejecutar_semantico(self):
        if self.obtener_codigo() is None: return
        self.status_bar.showMessage("Ejecutando Análisis Semántico...", 3000)
        simulacion = ">> INICIANDO ANÁLISIS SEMÁNTICO...\n\n[OK] Verificación de tipos exitosa.\n[OK] Ámbitos de variables validados.\n\n>> Análisis semántico finalizado."
        self.tabs_analisis.widget(2).setPlainText(simulacion)
        self.tabs_analisis.setCurrentIndex(2)

    def ejecutar_codigo_intermedio(self):
        if self.obtener_codigo() is None: return
        self.status_bar.showMessage("Generando Código Intermedio...", 3000)
        simulacion = ">> GENERANDO CÓDIGO INTERMEDIO (Tres Direcciones)...\n\nt1 = 5\nt2 = 10\nt3 = t1 + t2\na = t3\ngoto L1\n"
        self.tabs_analisis.widget(4).setPlainText(simulacion)
        self.tabs_analisis.setCurrentIndex(4)

    def ejecutar_programa(self):
        if self.obtener_codigo() is None: return
        self.status_bar.showMessage("Ejecutando Programa...", 3000)
        simulacion = ">> EJECUCIÓN INICIADA...\n\nHola Mundo!\n\n>> Proceso terminado con código de salida 0."
        self.consola_inferior.widget(3).setPlainText(simulacion)
        self.consola_inferior.setCurrentIndex(3)

    # --- MENÚS ---
    def crear_menus_y_herramientas(self):
        menu = self.menuBar()
        
        # MENÚ ARCHIVO
        archivo_menu = menu.addMenu("&Archivo")
        
        self.action_nuevo = QAction("Nuevo", self)
        self.action_nuevo.triggered.connect(self.nuevo_archivo)
        
        self.action_abrir = QAction("Abrir", self)
        self.action_abrir.triggered.connect(self.abrir_archivo)
        
        self.action_cerrar = QAction("Cerrar", self)
        self.action_cerrar.triggered.connect(self.cerrar_archivo_actual)
        
        self.action_guardar = QAction("Guardar", self)
        self.action_guardar.triggered.connect(self.guardar_archivo)
        
        self.action_guardar_como = QAction("Guardar como", self)
        self.action_guardar_como.triggered.connect(self.guardar_como)
        
        self.action_salir = QAction("Salir", self)
        self.action_salir.triggered.connect(self.close)

        archivo_menu.addAction(self.action_nuevo)
        archivo_menu.addAction(self.action_abrir)
        archivo_menu.addAction(self.action_cerrar)
        archivo_menu.addAction(self.action_guardar)
        archivo_menu.addAction(self.action_guardar_como)
        archivo_menu.addSeparator()
        archivo_menu.addAction(self.action_salir)

        # MENÚ COMPILAR
        compilar_menu = menu.addMenu("&Compilar")
        
        self.action_lexico = QAction("Análisis Léxico", self)
        self.action_lexico.triggered.connect(self.ejecutar_lexico)
        
        self.action_sintactico = QAction("Análisis Sintáctico", self)
        self.action_sintactico.triggered.connect(self.ejecutar_sintactico)
        
        self.action_semantico = QAction("Análisis Semántico", self)
        self.action_semantico.triggered.connect(self.ejecutar_semantico)
        
        self.action_intermedio = QAction("Generación de Código Intermedio", self)
        self.action_intermedio.triggered.connect(self.ejecutar_codigo_intermedio)
        
        self.action_run = QAction("Ejecución", self)
        self.action_run.triggered.connect(self.ejecutar_programa)

        compilar_menu.addAction(self.action_lexico)
        compilar_menu.addAction(self.action_sintactico)
        compilar_menu.addAction(self.action_semantico)
        compilar_menu.addAction(self.action_intermedio)
        compilar_menu.addSeparator()
        compilar_menu.addAction(self.action_run)