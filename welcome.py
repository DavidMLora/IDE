from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
import qtawesome as qta

class WelcomeScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        
        # Título principal
        title = QLabel("Compilador UAA - IDE 2026")
        title.setStyleSheet("font-size: 36px; color: #cccccc; font-weight: normal;")
        layout.addWidget(title)
        
        subtitle = QLabel("Editing evolved")
        subtitle.setStyleSheet("font-size: 18px; color: #888888; margin-bottom: 30px;")
        layout.addWidget(subtitle)
        
        # Sección Start
        start_label = QLabel("Start")
        start_label.setStyleSheet("font-size: 20px; color: #cccccc; margin-top: 20px; margin-bottom: 10px;")
        layout.addWidget(start_label)
        
        # Estilo para los botones tipo link
        btn_style = """
            QPushButton { text-align: left; background: transparent; color: #007acc; font-size: 14px; border: none; padding: 5px 0px; }
            QPushButton:hover { color: #0098ff; text-decoration: underline; }
        """
        
        # Botón Nuevo Archivo
        btn_new = QPushButton("  Nuevo Archivo...")
        btn_new.setIcon(qta.icon('fa5s.file-medical', color='#007acc'))
        btn_new.setStyleSheet(btn_style)
        btn_new.setCursor(Qt.PointingHandCursor)
        # Conectamos con la función de la ventana principal
        btn_new.clicked.connect(self.main_window.nuevo_archivo) 
        layout.addWidget(btn_new)
        
        # Botón Abrir Archivo
        btn_open = QPushButton("  Abrir Archivo...")
        btn_open.setIcon(qta.icon('fa5s.folder-open', color='#007acc'))
        btn_open.setStyleSheet(btn_style)
        btn_open.setCursor(Qt.PointingHandCursor)
        # Conectamos con la función de la ventana principal
        btn_open.clicked.connect(self.main_window.abrir_archivo)
        layout.addWidget(btn_open)
        
        layout.addStretch() # Empuja todo hacia arriba
        self.setStyleSheet("background-color: #1e1e1e;") # Fondo oscuro