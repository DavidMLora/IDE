# editor.py
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QPainter, QTextFormat, QColor, QSyntaxHighlighter,QTextCharFormat,QFont
from PySide6.QtCore import Qt, QRect, QSize, QRegularExpression

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)
class LexerHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        # --- CONFIGURACIÓN DE COLORES ---
        
        # Color 1: Números enteros y reales
        formato_numeros = QTextCharFormat()
        formato_numeros.setForeground(QColor("#91d46d")) # Verde claro

        # Color 2: Identificadores (letras y dígitos, no empiezan con dígito)
        formato_identificadores = QTextCharFormat()
        formato_identificadores.setForeground(QColor("#9cdcfe")) # Azul claro

        # Color 3: Comentarios de una y múltiples líneas
        self.formato_comentarios = QTextCharFormat()
        self.formato_comentarios.setForeground(QColor("#395b2a")) # Verde oscuro
        self.formato_comentarios.setFontItalic(True)

        # Color 4: Palabras reservadas
        formato_reservadas = QTextCharFormat()
        formato_reservadas.setForeground(QColor("#c586c0")) # Rosa/Morado
        # CORRECCIÓN PYSIDE6: Se usa QFont.Weight.Bold en lugar de QFont.Bold
        # formato_reservadas.setFontWeight(QFont.Weight.Bold) 

        # Color 5: Operadores aritméticos
        formato_aritmeticos = QTextCharFormat()
        formato_aritmeticos.setForeground(QColor("#d3d344")) # Amarillo

        # Color 6: Operadores relacionales y lógicos
        formato_relacionales = QTextCharFormat()
        formato_relacionales.setForeground(QColor("#4ec9b0")) # Turquesa

        # --- REGLAS DE EXPRESIONES REGULARES ---
        # EL ORDEN ES VITAL: Las reglas generales van primero, las específicas después.

        # 1. Identificadores (Color 2) - Van primero para ser la base
        # Modificado para seguir la regla exacta: letras y dígitos sin comenzar por dígito
        patron_id = QRegularExpression(r"\b[a-zA-Z][a-zA-Z0-9]*\b")
        self.rules.append((patron_id, formato_identificadores))

        # 2. Palabras Reservadas (Color 4) - Van después para SOBREESCRIBIR a los identificadores
        reservadas = ["if", "else", "end", "do", "while", "switch", "case", "int", "float", "main", "cin", "cout"]
        for palabra in reservadas:
            patron = QRegularExpression(rf"\b{palabra}\b")
            self.rules.append((patron, formato_reservadas))

        # 3. Números enteros y reales (Color 1)
        patron_numeros = QRegularExpression(r"\b\d+(\.\d+)?\b")
        self.rules.append((patron_numeros, formato_numeros))

        # 4. Operadores Aritméticos (Color 5)
        patron_aritmeticos = QRegularExpression(r"(\+\+|--|\+|-|\*|/|%|\^)")
        self.rules.append((patron_aritmeticos, formato_aritmeticos))

        # 5. Operadores Relacionales y Lógicos (Color 6)
        patron_relacionales = QRegularExpression(r"(<=|>=|==|!=|<|>|&&|\|\||!)")
        self.rules.append((patron_relacionales, formato_relacionales))

        # 6. Comentarios de una línea (Color 3)
        patron_comentario_linea = QRegularExpression(r"//[^\n]*")
        self.rules.append((patron_comentario_linea, self.formato_comentarios))

        # Expresiones para comentarios multilínea (estilo C)
        self.comentario_inicio = QRegularExpression(r"/\*")
        self.comentario_fin = QRegularExpression(r"\*/")
    def highlightBlock(self, text):
        # 1. Aplicar las reglas de una sola línea
        for patron, formato in self.rules:
            match_iterator = patron.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), formato)

        # 2. Aplicar lógica de estados para los comentarios multilínea (/* ... */)
        self.setCurrentBlockState(0)
        start_index = 0

        # Si el bloque anterior NO estaba dentro de un comentario, buscamos el inicio de uno (/*)
        if self.previousBlockState() != 1:
            match_inicio = self.comentario_inicio.match(text)
            start_index = match_inicio.capturedStart()
        
        # Mientras encontremos un inicio de comentario (start_index >= 0)
        while start_index >= 0:
            # Buscamos dónde termina (*/) a partir de donde inició
            match_fin = self.comentario_fin.match(text, start_index)
            end_index = match_fin.capturedStart()
            comentario_length = 0

            # Si NO encuentra el cierre, el comentario ocupa todo el resto de la línea
            if end_index == -1:
                self.setCurrentBlockState(1) # Avisamos a la siguiente línea que seguimos en comentario
                comentario_length = len(text) - start_index
            else:
                # Si SÍ encuentra el cierre, calculamos su tamaño para pintarlo
                comentario_length = end_index - start_index + match_fin.capturedLength()
            
            # setFormat SOBREESCRIBE los colores (borra el azul del identificador y pone el verde)
            self.setFormat(start_index, comentario_length, self.formato_comentarios)
            
            # Buscamos si el usuario abrió OTRO comentario más adelante en la misma línea
            match_inicio = self.comentario_inicio.match(text, start_index + comentario_length)
            start_index = match_inicio.capturedStart()
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line() # Asegura resaltado inicial
        
        fuente_codigo = self.font()
        fuente_codigo.setFamily("Consolas") # O usa "Fira Code" si la tienes instalada
        fuente_codigo.setPointSize(11)
        self.setFont(fuente_codigo)
        
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.highlighter = LexerHighlighter(self.document())

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 20 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy: 
            self.line_number_area.scroll(0, dy)
        else: 
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()): 
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2a2d2e") 
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e1e"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(), Qt.AlignCenter, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
