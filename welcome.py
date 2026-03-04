# welcome.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
import qtawesome as qta
from styles import WELCOME_STYLES


class WelcomeScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(WELCOME_STYLES)

        container = QFrame(self)
        container.setObjectName("welcome_container")

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)

        # Columna izquierda: logo, título, subtítulo, botones, recientes
        left = QWidget()
        left.setObjectName("welcome_left")
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(12)

        logo = QLabel()
        logo.setPixmap(qta.icon('fa5s.code', color='#4ebfff').pixmap(72, 72))
        left_layout.addWidget(logo, alignment=Qt.AlignLeft)

        title = QLabel("CompilladorIDE")
        title.setObjectName("title")
        left_layout.addWidget(title)

        subtitle = QLabel("IDE para los Compillas — Comienza rápido")
        subtitle.setObjectName("subtitle")
        left_layout.addWidget(subtitle)

        # botones principales
        btn_new = QPushButton(qta.icon('fa5s.file-medical', color='white'), " Nuevo archivo")
        btn_new.setObjectName("primary_btn")
        btn_new.clicked.connect(self.main_window.nuevo_archivo)

        btn_open = QPushButton(qta.icon('fa5s.folder-open', color='#c7d2de'), " Abrir archivo")
        btn_open.setObjectName("secondary_btn")
        btn_open.clicked.connect(self.main_window.abrir_archivo)

        left_layout.addWidget(btn_new)
        left_layout.addWidget(btn_open)

        # area de recientes
        recent_label = QLabel("Recientes")
        recent_label.setObjectName("welcome_card_title")
        left_layout.addSpacing(8)
        left_layout.addWidget(recent_label)

        self.recent_list = QListWidget()
        self.recent_list.setObjectName("welcome_recent")

        # simplemente hardcodeamos algunos archivos recientes para mostrar
        for name in ["main.cmp", "proyecto1.cmp", "README.md"]:
            item = QListWidgetItem(qta.icon('fa5s.file', color='#9aa4ad'), f"  {name}")
            self.recent_list.addItem(item)

        left_layout.addWidget(self.recent_list)
        left_layout.addStretch()

        # columnda derecha: tarjeta de bienvenida con tips
        right = QWidget()
        right.setObjectName("welcome_right")
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(10)

        card_title = QLabel("Bienvenido a CompilladorIDE")
        card_title.setObjectName("welcome_card_title")
        right_layout.addWidget(card_title)

        card_sub = QLabel("Crea, abre y ejecuta tus proyectos rápidamente.")
        card_sub.setObjectName("welcome_card_sub")
        right_layout.addWidget(card_sub)

        right_layout.addSpacing(8)

        tip1 = QLabel("• Usa `Nuevo archivo` para empezar un archivo vacío.")
        tip1.setObjectName("tip")
        tip2 = QLabel("• Abre carpetas de proyecto desde el menú Archivo.")
        tip2.setObjectName("tip")
        tip3 = QLabel("• Explora extensiones y snippets en el panel Extensiones.")
        tip3.setObjectName("tip")

        right_layout.addWidget(tip1)
        right_layout.addWidget(tip2)
        right_layout.addWidget(tip3)

        right_layout.addStretch()

        # columnas juntas
        main_layout.addWidget(left)
        main_layout.addWidget(right, stretch=1)

        outer = QVBoxLayout(self)
        outer.addWidget(container)
        outer.setContentsMargins(0, 0, 0, 0)