# terminal.py
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit
from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont, QTextCursor

class TerminalIntegrada(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Área de salida de texto (La Consola real)
        self.salida = QPlainTextEdit()
        self.salida.setReadOnly(True)
        fuente = QFont("Consolas", 10)
        self.salida.setFont(fuente)
        self.salida.setStyleSheet("background-color: #1e1e1e; color: #cccccc; border: none; padding: 5px;")

        # Línea de entrada de comandos
        self.entrada = QLineEdit()
        self.entrada.setFont(fuente)
        self.entrada.setStyleSheet("background-color: #2d2d2d; color: #ffffff; border: 1px solid #333; padding: 4px;")
        self.entrada.setPlaceholderText("Escribe comandos aquí (ej. dir, cd .., py lexer.py) y presiona Enter...")
        self.entrada.returnPressed.connect(self.ejecutar_comando)

        layout.addWidget(self.salida)
        layout.addWidget(self.entrada)

        # ========================================================
        # NUEVO: PROCESO PERSISTENTE (CONSOLA VIVA)
        # ========================================================
        self.proceso = QProcess(self)
        
        # Unimos los errores y la salida normal para que NADA se pierda silenciosamente
        self.proceso.setProcessChannelMode(QProcess.MergedChannels) 
        self.proceso.readyReadStandardOutput.connect(self.leer_salida)
        
        # Arrancamos la consola correspondiente y la dejamos corriendo
        if sys.platform == "win32":
            self.proceso.start("cmd.exe")
        else:
            self.proceso.start("bash", ["-i"])

    def ejecutar_comando(self):
        comando = self.entrada.text()
        self.entrada.clear()
        
        # Interceptar el comando de limpieza para limpiar el visor del IDE
        if comando.strip().lower() in ['cls', 'clear']:
            self.salida.clear()
            # Le enviamos un Enter invisible a cmd.exe para que vuelva a imprimir la ruta actual (el prompt)
            if sys.platform == "win32":
                self.proceso.write(b"\r\n")
            else:
                self.proceso.write(b"\n")
            return

        # Si el proceso de consola sigue vivo, le inyectamos el comando del usuario
        if self.proceso.state() == QProcess.Running:
            if sys.platform == "win32":
                comando_bytes = (comando + "\r\n").encode('utf-8', errors='replace')
            else:
                comando_bytes = (comando + "\n").encode('utf-8', errors='replace')
            
            # Escribir directamente en la entrada estándar (stdin) de la consola
            self.proceso.write(comando_bytes)

    def leer_salida(self):
        """Lee todo lo que escupe la terminal nativa y lo dibuja tal cual"""
        data = self.proceso.readAllStandardOutput().data()
        
        # Windows suele usar cp850 para los acentos en consola. Fallback a utf-8.
        try:
            texto = data.decode('cp850', errors='replace')
        except:
            texto = data.decode('utf-8', errors='replace')
            
        # Normalizar los saltos de línea para que QPlainTextEdit no haga saltos dobles
        texto = texto.replace('\r\n', '\n')
        
        # Usamos un cursor para añadir el texto al final sin romper el autoscroll
        cursor = self.salida.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(texto)
        
        self.salida.setTextCursor(cursor)
        self.salida.ensureCursorVisible()

    def cambiar_directorio(self, nueva_ruta):
        """Sincroniza la terminal cuando el usuario abre una carpeta desde la interfaz gráfica del IDE"""
        if self.proceso.state() == QProcess.Running:
            if sys.platform == "win32":
                # '/d' obliga a CMD a cambiar de disco si la ruta está en otra unidad (ej. de C: a D:)
                comando = f'cd /d "{nueva_ruta}"\r\n'
            else:
                comando = f'cd "{nueva_ruta}"\n'
            
            self.proceso.write(comando.encode('utf-8', errors='replace'))