# lexer.py
import re
import sys
import argparse
import os

# Palabras reservadas requeridas
RESERVADAS = {
    "if", "else", "end", "do", "while", "switch", "case", 
    "int", "float", "main", "cin", "cout"
}

# Definición de tokens mediante expresiones regulares
# El orden es crucial: de lo más específico a lo más general.
REGLAS = [
    ('COMENTARIO_MULTI', r'/\*[\s\S]*?\*/'),        # /* comentario multilínea */
    ('COMENTARIO_LINEA', r'//[^\n]*'),              # // comentario de una línea
    ('REAL',             r'\b\d+\.\d+\b'),          # Números reales
    ('ENTERO',           r'\b\d+\b'),               # Números enteros
    ('OP_RELACIONAL',    r'<=|>=|==|!=|<|>'),       # Operadores relacionales
    ('OP_LOGICO',        r'&&|\|\||!'),             # Operadores lógicos (and, or, not)
    ('OP_ARITMETICO',    r'\+\+|--|\+|-|\*|/|%|\^'),# Operadores aritméticos
    ('ASIGNACION',       r'='),                     # Asignación
    ('CADENA',           r'"[^"\\]*(\\.[^"\\]*)*"'),# Cadenas de texto ("...")
    ('CARACTER',         r"'[^'\\]*(\\.[^'\\]*)*'"),# Caracteres ('c')
    ('SIMBOLO',          r'[(){},;]'),              # Símbolos ( ) { } , ;
    ('ID',               r'\b[a-zA-Z][a-zA-Z0-9]*\b'), # Identificadores
    ('NUEVA_LINEA',      r'\n'),                    # Saltos de línea
    ('ESPACIO',          r'[ \t]+'),                # Espacios y tabulaciones
    ('MISMATCH',         r'.'),                     # Caracteres no válidos (ERROR)
]

# Compilar todas las reglas en una sola expresión regular
tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in REGLAS)
patron_maestro = re.compile(tok_regex)

def analizar_codigo(codigo):
    linea_num = 1
    linea_inicio = 0
    tokens_encontrados = []
    errores_encontrados = []

    for mo in patron_maestro.finditer(codigo):
        tipo = mo.lastgroup
        lexema = mo.group()
        # Cálculo exacto de la columna 
        columna = mo.start() - linea_inicio + 1

        if tipo == 'NUEVA_LINEA':
            linea_inicio = mo.end()
            linea_num += 1
            continue
        elif tipo == 'ESPACIO':
            continue
        elif tipo == 'COMENTARIO_MULTI':
            # Actualizar el contador de líneas si el comentario ocupa varias
            saltos = lexema.count('\n')
            if saltos > 0:
                linea_num += saltos
                linea_inicio = mo.start() + lexema.rfind('\n') + 1
            tokens_encontrados.append(('COMENTARIO', lexema, linea_num, columna))
            continue
        elif tipo == 'COMENTARIO_LINEA':
            tokens_encontrados.append(('COMENTARIO', lexema, linea_num, columna))
            continue
        elif tipo == 'ID' and lexema in RESERVADAS:
            tipo = 'RESERVADA'
        elif tipo == 'MISMATCH':
            error_msg = f"ERROR LÉXICO: Caracter no reconocido '{lexema}' | Fila: {linea_num} | Col: {columna}"
            errores_encontrados.append(error_msg)
            continue
            
        tokens_encontrados.append((tipo, lexema, linea_num, columna))

    return tokens_encontrados, errores_encontrados

def generar_archivos(ruta_original, tokens, errores):
    directorio, archivo = os.path.split(ruta_original)
    nombre_base, _ = os.path.splitext(archivo)
    
    ruta_tokens = os.path.join(directorio, f"{nombre_base}_tokens.txt")
    ruta_errores = os.path.join(directorio, f"{nombre_base}_errores.txt")

    # 1. El compilador destruye proactivamente la caché/archivos viejos
    try:
        if os.path.exists(ruta_tokens): os.remove(ruta_tokens)
        if os.path.exists(ruta_errores): os.remove(ruta_errores)
    except OSError:
        pass # Si están bloqueados, lo ignoramos y confiamos en el modo 'w'

    # 2. Escribir archivo de tokens
    with open(ruta_tokens, 'w', encoding='utf-8') as f_tok:
        f_tok.write("REPORTE DE TOKENS\n")
        f_tok.write("-" * 50 + "\n")
        for tipo, lexema, fila, col in tokens:
            lex_limpio = lexema.replace('\n', '\\n').replace('\r', '')
            f_tok.write(f"Token: {tipo:15} | Lexema: {lex_limpio:15} | Fila: {fila:3} | Col: {col:3}\n")
        
        # 3. Magia Negra: Obligar al sistema operativo a vaciar la memoria RAM al disco duro
        f_tok.flush()
        os.fsync(f_tok.fileno())
            
    # 4. Escribir archivo de errores
    with open(ruta_errores, 'w', encoding='utf-8') as f_err:
        f_err.write("REPORTE DE ERRORES LÉXICOS\n")
        f_err.write("-" * 50 + "\n")
        if not errores:
            f_err.write("0 errores encontrados. Análisis léxico limpio.\n")
        else:
            for err in errores:
                f_err.write(err + "\n")
        
        f_err.flush()
        os.fsync(f_err.fileno())
    # Obtener el nombre del archivo sin la extensión
    directorio, archivo = os.path.split(ruta_original)
    nombre_base, _ = os.path.splitext(archivo)
    
    ruta_tokens = os.path.join(directorio, f"{nombre_base}_tokens.txt")
    ruta_errores = os.path.join(directorio, f"{nombre_base}_errores.txt")

    # Escribir archivo de tokens
    with open(ruta_tokens, 'w', encoding='utf-8') as f_tok:
        f_tok.write("REPORTE DE TOKENS\n")
        f_tok.write("-" * 50 + "\n")
        for tipo, lexema, fila, col in tokens:
            # Formateamos los saltos de línea en el lexema para que no rompan el reporte
            lex_limpio = lexema.replace('\n', '\\n').replace('\r', '')
            f_tok.write(f"Token: {tipo:15} | Lexema: {lex_limpio:15} | Fila: {fila:3} | Col: {col:3}\n")
            
    # Escribir archivo de errores
    with open(ruta_errores, 'w', encoding='utf-8') as f_err:
        f_err.write("REPORTE DE ERRORES LÉXICOS\n")
        f_err.write("-" * 50 + "\n")
        if not errores:
            f_err.write("0 errores encontrados. Análisis léxico limpio.\n")
        else:
            for err in errores:
                f_err.write(err + "\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analizador Léxico Independiente")
    parser.add_argument('archivo', help="Ruta del archivo a compilar")
    args = parser.parse_args()

    try:
        with open(args.archivo, 'r', encoding='utf-8') as f:
            codigo_fuente = f.read()
            
        tokens, errores = analizar_codigo(codigo_fuente)
        
        # Generar los archivos físicos requeridos en la misma carpeta que el código
        generar_archivos(args.archivo, tokens, errores)

        # Imprimir en consola (necesario para que el IDE capture la salida)
        print(f">> Archivos generados: _tokens.txt y _errores.txt")
        print(">> INICIANDO ANÁLISIS LÉXICO...")
        for tipo, lexema, fila, col in tokens:
            lex_limpio = lexema.replace('\n', '\\n').replace('\r', '')
            print(f"Token: {tipo:15} | Lexema: {lex_limpio:15} | Fila: {fila:3} | Col: {col:3}")
        
        if errores:
            print("\n>> SE ENCONTRARON ERRORES:", file=sys.stderr)
            for err in errores:
                print(err, file=sys.stderr)
            sys.exit(1)
        else:
            print("\n>> Análisis léxico finalizado sin errores.")
            sys.exit(0)

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{args.archivo}'", file=sys.stderr)
        sys.exit(2)