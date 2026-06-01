import sys
import os
import json
import argparse

class Token:
    def __init__(self, tipo, lexema, fila, columna):
        self.tipo = tipo.strip()
        self.lexema = lexema.strip()
        self.fila = int(fila)
        self.columna = int(columna)
        
    def __repr__(self):
        return f"{self.tipo}('{self.lexema}')"

def leer_tokens(ruta_archivo):
    tokens = []
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            for linea in lineas[2:]:
                if not linea.strip(): continue
                partes = linea.split('|')
                if len(partes) == 4:
                    tipo = partes[0].split(':', 1)[1].strip()
                    lexema = partes[1].split(':', 1)[1].strip()
                    fila = partes[2].split(':', 1)[1].strip()
                    col = partes[3].split(':', 1)[1].strip()
                    
                    # Restaurar saltos de linea sanitizados
                    lexema = lexema.replace('\\n', '\n')
                    tokens.append(Token(tipo, lexema, fila, col))
    except Exception as e:
        print(f"Error leyendo tokens: {e}")
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.tipo != 'COMENTARIO'] # Ignoramos los comentarios en sintáctico
        self.pos = 0
        self.errores = []
    
    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
        
    def avanzar(self):
        self.pos += 1
        
    def match(self, tipo_esperado, lexema_esperado=None):
        tok = self.actual()
        if not tok:
            self.error(f"Se esperaba {lexema_esperado or tipo_esperado} pero se alcanzo el fin de archivo")
            return None
            
        if tok.tipo == tipo_esperado and (lexema_esperado is None or tok.lexema == lexema_esperado):
            self.avanzar()
            return tok
            
        self.error(f"Se esperaba {lexema_esperado or tipo_esperado} pero se encontro '{tok.lexema}' ({tok.tipo})", tok)
        # Sincronización simple (panic mode)
        return None

    def error(self, mensaje, tok=None):
        if tok:
            self.errores.append(f"Error Sintactico: {mensaje} | Fila: {tok.fila} | Col: {tok.columna}")
        else:
            self.errores.append(f"Error Sintactico: {mensaje}")
            
    def parse(self):
        ast = self.programa()
        return ast
        
    def programa(self):
        nodo = {"tipo": "programa", "hijos": []}
        
        main_tok = self.match("RESERVADA", "main")
        if main_tok:
            nodo["hijos"].append({"tipo": "keyword", "valor": "main"})
            
        llave_abre = self.match("SIMBOLO", "{")
        if llave_abre:
            nodo["hijos"].append({"tipo": "simbolo", "valor": "{"})
            
        lista_decl = self.lista_declaracion()
        if lista_decl:
            nodo["hijos"].append(lista_decl)
            
        llave_cierra = self.match("SIMBOLO", "}")
        if llave_cierra:
            nodo["hijos"].append({"tipo": "simbolo", "valor": "}"})
            
        return nodo

    def lista_declaracion(self):
        nodo = {"tipo": "lista_declaracion", "hijos": []}
        
        while self.actual() and self.actual().lexema != "}":
            decl = self.declaracion()
            if decl:
                nodo["hijos"].append(decl)
            else:
                tok = self.actual()
                if tok and tok.lexema != "}":
                    self.avanzar() 
        
        return nodo if len(nodo["hijos"]) > 0 else None
        
    def declaracion(self):
        tok = self.actual()
        if not tok: return None
        
        if tok.tipo == "RESERVADA" and tok.lexema in ["int", "float", "bool"]:
            return self.declaracion_variable()
        else:
            return self.lista_sentencias_wrapper()
            
    def lista_sentencias_wrapper(self):
        nodo = self.lista_sentencias()
        return nodo

    def declaracion_variable(self):
        nodo = {"tipo": "declaracion_variable", "hijos": []}
        
        tipo_nodo = self.tipo_dato()
        if tipo_nodo:
            nodo["hijos"].append(tipo_nodo)
            
        id_nodo = self.identificador()
        if id_nodo:
            nodo["hijos"].append(id_nodo)
            
        pto_coma = self.match("SIMBOLO", ";")
        if pto_coma:
            nodo["hijos"].append({"tipo": "simbolo", "valor": ";"})
            
        return nodo
        
    def identificador(self):
        nodo = {"tipo": "identificadores", "hijos": []}
        
        id_tok = self.match("ID")
        if id_tok:
            nodo["hijos"].append({"tipo": "id", "valor": id_tok.lexema})
            
        while self.actual() and self.actual().lexema == ",":
            self.match("SIMBOLO", ",")
            nodo["hijos"].append({"tipo": "simbolo", "valor": ","})
            next_id = self.match("ID")
            if next_id:
                nodo["hijos"].append({"tipo": "id", "valor": next_id.lexema})
                
        return nodo
        
    def tipo_dato(self):
        tok = self.actual()
        if tok and tok.tipo == "RESERVADA" and tok.lexema in ["int", "float", "bool"]:
            self.avanzar()
            return {"tipo": "tipo_dato", "valor": tok.lexema}
        self.error("Se esperaba int, float o bool", tok)
        return None
        
    def lista_sentencias(self):
        nodo = {"tipo": "lista_sentencias", "hijos": []}
        
        primeros_sentencia = ["if", "while", "do", "cin", "cout"]
        
        while self.actual():
            tok = self.actual()
            if tok.lexema in primeros_sentencia or tok.tipo == "ID":
                sent = self.sentencia()
                if sent:
                    nodo["hijos"].append(sent)
                else:
                    self.avanzar()
            else:
                break
                
        return nodo if len(nodo["hijos"]) > 0 else None
        
    def sentencia(self):
        tok = self.actual()
        if not tok: return None
        
        if tok.lexema == "if":
            return self.seleccion()
        elif tok.lexema == "while":
            return self.iteracion()
        elif tok.lexema == "do":
            return self.repeticion()
        elif tok.lexema == "cin":
            return self.sent_in()
        elif tok.lexema == "cout":
            return self.sent_out()
        elif tok.tipo == "ID":
            return self.asignacion()
        else:
            self.error("Se esperaba una sentencia", tok)
            return None
            
    def asignacion(self):
        nodo = {"tipo": "asignacion", "hijos": []}
        
        id_tok = self.match("ID")
        if id_tok:
            nodo["hijos"].append({"tipo": "id", "valor": id_tok.lexema})
            
        eq_tok = self.match("ASIGNACION", "=")
        if eq_tok:
            nodo["hijos"].append({"tipo": "operador", "valor": "="})
            
        sent_expr = self.sent_expresion()
        if sent_expr:
            nodo["hijos"].append(sent_expr)
            
        return nodo
        
    def sent_expresion(self):
        nodo = {"tipo": "sent_expresion", "hijos": []}
        
        if self.actual() and self.actual().lexema == ";":
            self.match("SIMBOLO", ";")
            nodo["hijos"].append({"tipo": "simbolo", "valor": ";"})
        else:
            expr = self.expresion()
            if expr:
                nodo["hijos"].append(expr)
            pto_coma = self.match("SIMBOLO", ";")
            if pto_coma:
                nodo["hijos"].append({"tipo": "simbolo", "valor": ";"})
                
        return nodo
        
    def seleccion(self):
        nodo = {"tipo": "seleccion", "hijos": []}
        
        self.match("RESERVADA", "if")
        nodo["hijos"].append({"tipo": "keyword", "valor": "if"})
        
        expr = self.expresion()
        if expr: nodo["hijos"].append(expr)
        
        # Soportamos 'then' (como ID o Reservada) o '{'
        if self.actual() and self.actual().lexema in ["then", "{"]:
            val = self.actual().lexema
            self.avanzar()
            nodo["hijos"].append({"tipo": "simbolo", "valor": val})
            
        lista1 = self.lista_sentencias()
        if lista1: nodo["hijos"].append(lista1)
        
        if self.actual() and self.actual().lexema == "else":
            self.match("RESERVADA", "else")
            nodo["hijos"].append({"tipo": "keyword", "valor": "else"})
            
            if self.actual() and self.actual().lexema == "{":
                self.avanzar()
                nodo["hijos"].append({"tipo": "simbolo", "valor": "{"})
                
            lista2 = self.lista_sentencias()
            if lista2: nodo["hijos"].append(lista2)
            
        if self.actual() and self.actual().lexema in ["end", "}"]:
            val = self.actual().lexema
            self.avanzar()
            nodo["hijos"].append({"tipo": "simbolo", "valor": val})
            
        return nodo
        
    def iteracion(self):
        nodo = {"tipo": "iteracion", "hijos": []}
        
        self.match("RESERVADA", "while")
        nodo["hijos"].append({"tipo": "keyword", "valor": "while"})
        
        expr = self.expresion()
        if expr: nodo["hijos"].append(expr)
        
        if self.actual() and self.actual().lexema == "{":
            self.avanzar()
            nodo["hijos"].append({"tipo": "simbolo", "valor": "{"})
            
        lista = self.lista_sentencias()
        if lista: nodo["hijos"].append(lista)
        
        if self.actual() and self.actual().lexema in ["end", "}"]:
            val = self.actual().lexema
            self.avanzar()
            nodo["hijos"].append({"tipo": "simbolo", "valor": val})
            
        return nodo
        
    def repeticion(self):
        nodo = {"tipo": "repeticion", "hijos": []}
        
        self.match("RESERVADA", "do")
        nodo["hijos"].append({"tipo": "keyword", "valor": "do"})
        
        if self.actual() and self.actual().lexema == "{":
            self.avanzar()
            nodo["hijos"].append({"tipo": "simbolo", "valor": "{"})
            
        lista = self.lista_sentencias()
        if lista: nodo["hijos"].append(lista)
        
        if self.actual() and self.actual().lexema == "}":
            self.avanzar()
            nodo["hijos"].append({"tipo": "simbolo", "valor": "}"})
            
        self.match("RESERVADA", "while")
        nodo["hijos"].append({"tipo": "keyword", "valor": "while"})
        
        expr = self.expresion()
        if expr: nodo["hijos"].append(expr)
        
        pto = self.match("SIMBOLO", ";")
        if pto: nodo["hijos"].append({"tipo": "simbolo", "valor": ";"})
        
        return nodo
        
    def sent_in(self):
        nodo = {"tipo": "sent_in", "hijos": []}
        
        self.match("RESERVADA", "cin")
        nodo["hijos"].append({"tipo": "keyword", "valor": "cin"})
        
        if self.actual() and self.actual().lexema == ">":
            self.avanzar()
            if self.actual() and self.actual().lexema == ">":
                self.avanzar()
                nodo["hijos"].append({"tipo": "operador", "valor": ">>"})
        
        id_tok = self.match("ID")
        if id_tok: nodo["hijos"].append({"tipo": "id", "valor": id_tok.lexema})
        
        pto = self.match("SIMBOLO", ";")
        if pto: nodo["hijos"].append({"tipo": "simbolo", "valor": ";"})
        return nodo
        
    def sent_out(self):
        nodo = {"tipo": "sent_out", "hijos": []}
        self.match("RESERVADA", "cout")
        nodo["hijos"].append({"tipo": "keyword", "valor": "cout"})
        
        if self.actual() and self.actual().lexema == "<":
            self.avanzar()
            if self.actual() and self.actual().lexema == "<":
                self.avanzar()
                nodo["hijos"].append({"tipo": "operador", "valor": "<<"})
                
        sal = self.salida()
        if sal: nodo["hijos"].append(sal)
        
        pto = self.match("SIMBOLO", ";")
        if pto: nodo["hijos"].append({"tipo": "simbolo", "valor": ";"})
        
        return nodo
        
    def salida(self):
        nodo = {"tipo": "salida", "hijos": []}
        
        tok = self.actual()
        if not tok: return None
        
        if tok.tipo == "CADENA":
            self.avanzar()
            nodo["hijos"].append({"tipo": "cadena", "valor": tok.lexema})
        else:
            expr = self.expresion()
            if expr: nodo["hijos"].append(expr)
            
        if self.actual() and self.actual().lexema == "<":
            self.avanzar()
            if self.actual() and self.actual().lexema == "<":
                self.avanzar()
                nodo["hijos"].append({"tipo": "operador", "valor": "<<"})
                
                tok2 = self.actual()
                if tok2 and tok2.tipo == "CADENA":
                    self.avanzar()
                    nodo["hijos"].append({"tipo": "cadena", "valor": tok2.lexema})
                else:
                    expr2 = self.expresion()
                    if expr2: nodo["hijos"].append(expr2)
                    
        return nodo
        
    def expresion(self):
        nodo = {"tipo": "expresion", "hijos": []}
        
        simple = self.expresion_simple()
        if simple: nodo["hijos"].append(simple)
        
        tok = self.actual()
        if tok and tok.tipo == "OP_RELACIONAL":
            self.avanzar()
            nodo["hijos"].append({"tipo": "op_relacional", "valor": tok.lexema})
            
            simple2 = self.expresion_simple()
            if simple2: nodo["hijos"].append(simple2)
            
        return nodo if len(nodo["hijos"]) > 0 else None
        
    def expresion_simple(self):
        nodo = {"tipo": "expresion_simple", "hijos": []}
        
        term = self.termino()
        if term: nodo["hijos"].append(term)
        
        while self.actual() and (self.actual().lexema in ["+", "-", "++", "--"] or self.actual().tipo == "OP_ARITMETICO" and self.actual().lexema in ["+", "-"]):
            tok = self.actual()
            self.avanzar()
            nodo["hijos"].append({"tipo": "suma_op", "valor": tok.lexema})
            
            term2 = self.termino()
            if term2: nodo["hijos"].append(term2)
            
        return nodo if len(nodo["hijos"]) > 0 else None
        
    def termino(self):
        nodo = {"tipo": "termino", "hijos": []}
        
        fac = self.factor()
        if fac: nodo["hijos"].append(fac)
        
        while self.actual() and (self.actual().lexema in ["*", "/", "%"]):
            tok = self.actual()
            self.avanzar()
            nodo["hijos"].append({"tipo": "mult_op", "valor": tok.lexema})
            
            fac2 = self.factor()
            if fac2: nodo["hijos"].append(fac2)
            
        return nodo if len(nodo["hijos"]) > 0 else None
        
    def factor(self):
        nodo = {"tipo": "factor", "hijos": []}
        
        comp = self.componente()
        if comp: nodo["hijos"].append(comp)
        
        while self.actual() and self.actual().lexema == "^":
            tok = self.actual()
            self.avanzar()
            nodo["hijos"].append({"tipo": "pot_op", "valor": tok.lexema})
            
            comp2 = self.componente()
            if comp2: nodo["hijos"].append(comp2)
            
        return nodo if len(nodo["hijos"]) > 0 else None
        
    def componente(self):
        tok = self.actual()
        if not tok: return None
        
        nodo = {"tipo": "componente", "hijos": []}
        
        if tok.lexema == "(":
            self.avanzar()
            nodo["hijos"].append({"tipo": "simbolo", "valor": "("})
            expr = self.expresion()
            if expr: nodo["hijos"].append(expr)
            cierra = self.match("SIMBOLO", ")")
            if cierra: nodo["hijos"].append({"tipo": "simbolo", "valor": ")"})
            return nodo
        elif tok.tipo in ["ENTERO", "REAL"]:
            self.avanzar()
            nodo["hijos"].append({"tipo": "numero", "valor": tok.lexema})
            return nodo
        elif tok.tipo == "ID":
            self.avanzar()
            nodo["hijos"].append({"tipo": "id", "valor": tok.lexema})
            return nodo
        elif tok.tipo == "RESERVADA" and tok.lexema in ["true", "false", "bool"]: 
            self.avanzar()
            nodo["hijos"].append({"tipo": "booleano", "valor": tok.lexema})
            return nodo
        elif tok.tipo == "OP_LOGICO":
            self.avanzar()
            nodo["hijos"].append({"tipo": "op_logico", "valor": tok.lexema})
            comp = self.componente()
            if comp: nodo["hijos"].append(comp)
            return nodo
            
        if tok.tipo in ["CADENA", "CARACTER"]:
            self.avanzar()
            nodo["hijos"].append({"tipo": "literal", "valor": tok.lexema})
            return nodo
            
        self.error("Se esperaba (, numero, identificador u operador logico", tok)
        self.avanzar()
        return None

def generar_archivos_ast(ruta_tokens, tokens):
    parser = Parser(tokens)
    ast = parser.parse()
    errores_sintacticos = parser.errores
    
    directorio = os.path.dirname(ruta_tokens)
    nombre_base = os.path.basename(ruta_tokens).replace('_tokens.txt', '')
    
    ruta_ast = os.path.join(directorio, f"{nombre_base}_ast.json")
    ruta_errores = os.path.join(directorio, f"{nombre_base}_errores_sintacticos.txt")
    
    with open(ruta_ast, 'w', encoding='utf-8') as f:
        json.dump(ast, f, indent=4)
        
    with open(ruta_errores, 'w', encoding='utf-8') as f:
        f.write("REPORTE DE ERRORES SINTACTICOS\n")
        f.write("-" * 50 + "\n")
        if not errores_sintacticos:
            f.write("0 errores encontrados. Analisis sintactico limpio.\n")
        else:
            for err in errores_sintacticos:
                f.write(err + "\n")
                
    return ruta_ast, ruta_errores

if __name__ == '__main__':
    parser_arg = argparse.ArgumentParser(description="Analizador Sintactico")
    parser_arg.add_argument('archivo_tokens', help="Ruta del archivo de tokens")
    args = parser_arg.parse_args()
    
    tokens = leer_tokens(args.archivo_tokens)
    if not tokens:
        print("No se encontraron tokens o el archivo esta vacio.", file=sys.stderr)
        sys.exit(1)
        
    ruta_ast, ruta_errores = generar_archivos_ast(args.archivo_tokens, tokens)
    
    print(f">> Archivos generados: {os.path.basename(ruta_ast)} y {os.path.basename(ruta_errores)}")
    sys.exit(0)
