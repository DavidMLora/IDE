# welcome.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
import qtawesome as qta
from styles import WELCOME_STYLES

class WelcomeScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(WELCOME_STYLES)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setAlignment(Qt.AlignCenter)
        
        # Títulos
        title = QLabel("CompilladorIDE")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("IDE para los Compillas")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Botones de Acción
        self.btn_new = QPushButton("   Nuevo Archivo...")
        self.btn_new.setIcon(qta.icon('fa5s.file-medical', color='#4ebfff'))
        self.btn_new.setObjectName("link_btn")
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self.main_window.nuevo_archivo) 
        
        self.btn_open = QPushButton("   Abrir Archivo...")
        self.btn_open.setIcon(qta.icon('fa5s.folder-open', color='#4ebfff'))
        self.btn_open.setObjectName("link_btn")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self.main_window.abrir_archivo)
        
        # Contenedor para centrar botones
        btn_layout = QVBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setSpacing(10)
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_open)
        
        layout.addLayout(btn_layout)
        layout.addStretch()