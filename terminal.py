# terminal.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit
from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont

class TerminalIntegrada(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Área de salida de texto
        self.salida = QPlainTextEdit()
        self.salida.setReadOnly(True)
        fuente = QFont("Consolas", 10)
        self.salida.setFont(fuente)
        self.salida.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: none;")

        # Línea de entrada de comandos
        self.entrada = QLineEdit()
        self.entrada.setFont(fuente)
        self.entrada.setStyleSheet("background-color: #2d2d2d; color: #ffffff; border: 1px solid #333; padding: 2px;")
        self.entrada.setPlaceholderText("Escribe un comando (ej. python lexer.py archivo.cmp) y presiona Enter...")
        self.entrada.returnPressed.connect(self.ejecutar_comando)

        layout.addWidget(self.salida)
        layout.addWidget(self.entrada)

        # Objeto QProcess para manejar las llamadas al sistema sin congelar la UI
        self.proceso = QProcess(self)
        self.proceso.readyReadStandardOutput.connect(self.leer_salida)
        self.proceso.readyReadStandardError.connect(self.leer_errores)
        self.proceso.finished.connect(self.proceso_terminado)

    def ejecutar_comando(self):
        comando = self.entrada.text()
        if comando.strip():
            self.salida.appendPlainText(f"\n> {comando}")
            self.entrada.clear()
            # En Windows se usa 'cmd /c', en Mac/Linux puede ser 'bash -c'
            import sys
            if sys.platform == "win32":
                self.proceso.start("cmd", ["/c", comando])
            else:
                self.proceso.start("bash", ["-c", comando])

    def leer_salida(self):
        texto = self.proceso.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self.salida.insertPlainText(texto)
        self.salida.ensureCursorVisible()

    def leer_errores(self):
        texto = self.proceso.readAllStandardError().data().decode('utf-8', errors='replace')
        self.salida.insertPlainText(texto)
        self.salida.ensureCursorVisible()

    def proceso_terminado(self):
        self.salida.ensureCursorVisible()
    def cambiar_directorio(self, nueva_ruta):
        # Cambia la carpeta donde se ejecutan los comandos de la terminal
        self.proceso.setWorkingDirectory(nueva_ruta)
        # Mostrar un mensaje verde en la terminal para avisar al usuario
        self.salida.appendHtml(f"<br><font color='#4ec9b0'>> Directorio de trabajo cambiado a: {nueva_ruta}</font><br>")
        self.salida.ensureCursorVisible()