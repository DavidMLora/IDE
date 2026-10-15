"""Análisis semántico de la fase 3.

El AST esperado sigue el formato generado por el parser del proyecto:
{'tipo': ..., 'valor': ..., 'fila': ..., 'columna': ..., 'hijos': [...]}.

El lenguaje descrito para esta fase tiene tipos int, float y bool. La
implementación conserva una tabla de ámbito global, como el archivo original;
para soportar ámbitos anidados será necesario confirmar la gramática del parser.
"""

from copy import deepcopy
import json
from pathlib import Path


TIPOS_NUMERICOS = {"int", "float"}
OPERADORES_ARITMETICOS = {"+", "-", "*", "/", "%", "^"}
OPERADORES_RELACIONALES = {"<", "<=", ">", ">=", "==", "!=", "<>"}
OPERADORES_LOGICOS = {"&&", "||", "!", "and", "or", "not", "y", "o", "no"}


class TablaSimbolos:
    """Tabla con nombre, tipo, dirección secuencial y líneas de referencia."""

    def __init__(self):
        self.tabla = {}
        self.location = 0

    def insertar(self, nombre, linea, tipo_dato=None):
        """True si el símbolo se declaró por primera vez; False si ya existe."""
        if nombre in self.tabla:
            return False
        self.tabla[nombre] = {
            "tipo": tipo_dato,
            "memloc": self.location,
            "lineas": [linea] if linea is not None else [],
            "valor": None,  # Valor constante conocido; None = desconocido.
        }
        self.location += 1
        return True

    def registrar_uso(self, nombre, linea):
        info = self.buscar(nombre)
        if info is None:
            return False
        # Cada token ID cuenta: `y = y + 1` registra dos veces la misma línea.
        if linea is not None:
            info["lineas"].append(linea)
        return True

    def buscar(self, nombre):
        return self.tabla.get(nombre)

    def imprimir_tabla(self):
        print(f"{'Nombre':<15} | {'Tipo':<10} | {'Loc':<5} | Líneas | Valor conocido")
        print("-" * 55)
        for nombre, info in self.tabla.items():
            lineas = ", ".join(map(str, info["lineas"]))
            valor = info.get("valor")
            print(f"{nombre:<15} | {str(info['tipo']):<10} | {info['memloc']:<5} | {lineas} | {valor!r}")


class AnalizadorSemantico:
    """Construye la tabla, anota una copia del AST y verifica tipos."""

    def __init__(self, ast):
        self.ast_original = deepcopy(ast)
        self.ast = deepcopy(ast)
        self.symtab = TablaSimbolos()
        self.errores = []
        self._errores_vistos = set()

    def analizar(self, ruta_salida=None):
        # Cada ejecución parte del AST original, sin repetir anotaciones anteriores.
        self.ast = deepcopy(self.ast_original)
        self.symtab = TablaSimbolos()
        self.errores = []
        self._errores_vistos = set()
        self._build_symtab(self.ast)
        self._type_check(self.ast)

        if ruta_salida:
            destino = Path(ruta_salida)
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.suffix.lower() == ".json":
                with destino.open("w", encoding="utf-8") as f:
                    json.dump(self.ast, f, ensure_ascii=False, indent=2)
            else:
                destino.write_text(self.generar_arbol_visual(self.ast), encoding="utf-8")
        return self.symtab, self.errores

    @staticmethod
    def _hijos(nodo):
        if not isinstance(nodo, dict):
            return []
        return [hijo for hijo in nodo.get("hijos", []) if isinstance(hijo, dict)]

    def _obtener_posicion(self, nodo):
        if not isinstance(nodo, dict):
            return None, None
        linea = nodo.get("fila", nodo.get("linea"))
        columna = nodo.get("columna")
        if linea is not None:
            return linea, columna
        for hijo in self._hijos(nodo):
            fila_hijo, col_hijo = self._obtener_posicion(hijo)
            if fila_hijo is not None:
                return fila_hijo, col_hijo
        return None, None

    def _obtener_linea(self, nodo):
        fila, _ = self._obtener_posicion(nodo)
        return fila if fila is not None else "N/A"

    def _error(self, nodo, descripcion):
        linea, columna = self._obtener_posicion(nodo)
        ubicacion = f"Línea {linea if linea is not None else 'N/A'}"
        if columna is not None:
            ubicacion += f", Columna {columna}"
        mensaje = f"Error Semántico ({ubicacion}): {descripcion}"
        if mensaje not in self._errores_vistos:
            self._errores_vistos.add(mensaje)
            self.errores.append(mensaje)

    def _build_symtab(self, nodo):
        """Recorrido preorden: declara y registra usos, sin inferir aún tipos."""
        if not isinstance(nodo, dict):
            return
        tipo = nodo.get("tipo")
        hijos = self._hijos(nodo)

        if tipo == "declaracion_variable":
            tipo_dato = next(
                (h.get("valor") for h in hijos if h.get("tipo") == "tipo_dato"), None
            )
            if tipo_dato not in {"int", "float", "bool"}:
                self._error(nodo, f"Tipo de declaración desconocido: '{tipo_dato}'.")
                return
            # El tipo declarado se hereda del nodo de declaración hacia los IDs.
            nodo["dtype"] = tipo_dato
            contenedores = [h for h in hijos if h.get("tipo") == "identificadores"]
            identificadores = []
            for contenedor in contenedores:
                contenedor["dtype"] = tipo_dato
                identificadores.extend(h for h in self._hijos(contenedor) if h.get("tipo") == "id")
            if not contenedores:
                identificadores.extend(h for h in hijos if h.get("tipo") == "id")

            for id_nodo in identificadores:
                nombre = id_nodo.get("valor")
                linea, _ = self._obtener_posicion(id_nodo)
                if linea is None:
                    linea, _ = self._obtener_posicion(nodo)
                id_nodo["dtype"] = tipo_dato
                id_nodo["type"] = tipo_dato
                if not nombre:
                    continue
                if not self.symtab.insertar(nombre, linea, tipo_dato):
                    # También contabilizar la segunda aparición declarada.
                    self.symtab.registrar_uso(nombre, linea)
                    self._error(id_nodo, f"Variable '{nombre}' ya fue declarada.")
            # Los IDs declarados no deben contabilizarse como usos adicionales.
            return

        if tipo == "id":
            nombre = nodo.get("valor")
            if nombre and nombre not in {"true", "false", "then", "until"}:
                linea, _ = self._obtener_posicion(nodo)
                if not self.symtab.registrar_uso(nombre, linea):
                    self._error(nodo, f"Variable '{nombre}' no declarada.")

        for hijo in hijos:
            self._build_symtab(hijo)

    @staticmethod
    def _conversión_permitida(destino, origen):
        # Única conversión implícita propuesta: int -> float.
        return destino == origen or (destino == "float" and origen == "int")

    @staticmethod
    def _anotar_conversion(nodo, origen, destino):
        if origen != destino:
            nodo["conversion"] = {"de": origen, "a": destino}

    def _estado(self):
        """Copia de valores conocidos, útil para bifurcaciones y ciclos."""
        return {nombre: info["valor"] for nombre, info in self.symtab.tabla.items()}

    def _restaurar_estado(self, estado):
        for nombre, info in self.symtab.tabla.items():
            info["valor"] = estado.get(nombre)

    def _modificadas(self, nodo):
        """Variables que podrían cambiar en un bloque, aunque no se ejecute."""
        if not isinstance(nodo, dict):
            return set()
        tipo = nodo.get("tipo")
        hijos = self._hijos(nodo)
        modificadas = set()
        if tipo == "operador" and nodo.get("valor") in {"=", ":="} and hijos:
            if hijos[0].get("tipo") == "id":
                modificadas.add(hijos[0].get("valor"))
        elif tipo in {"incremento", "decremento"} and hijos:
            if hijos[0].get("tipo") == "id":
                modificadas.add(hijos[0].get("valor"))
        elif tipo == "sent_in":
            modificadas.update(h.get("valor") for h in hijos if h.get("tipo") == "id")
        for hijo in hijos:
            modificadas.update(self._modificadas(hijo))
        return modificadas - {None}

    def _type_check(self, nodo):
        """Recorrido en orden de ejecución para propagación CONSTANTE estática.

        No interpreta ciclos: pierde conservadoramente valores cuando no se
        puede garantizar su estado final. Esto es análisis, no ejecución real.
        """
        if not isinstance(nodo, dict):
            return
        tipo = nodo.get("tipo")
        valor = nodo.get("valor")
        hijos = self._hijos(nodo)

        if tipo == "declaracion_variable":
            return  # La construcción de la tabla ya anotó los identificadores.
        if tipo == "id":
            info = self.symtab.buscar(valor)
            if info is not None:
                nodo["type"] = info["tipo"]
                if info["valor"] is not None:
                    nodo["eval"] = info["valor"]
            return
        if tipo == "numero":
            try:
                texto = str(valor)
                if "." in texto or "e" in texto.lower():
                    nodo["type"] = "float"
                    nodo["eval"] = float(texto)
                else:
                    nodo["type"] = "int"
                    nodo["eval"] = int(texto)
            except (ValueError, TypeError, OverflowError):
                self._error(nodo, f"Literal numérico no válido: '{valor}'.")
            return
        if tipo == "booleano":
            nodo["type"] = "bool"
            nodo["eval"] = str(valor).lower() == "true"
            return

        if tipo in {"incremento", "decremento"}:
            if not hijos or hijos[0].get("tipo") != "id":
                self._error(nodo, "Se esperaba identificador en incremento/decremento.")
                return
            destino = hijos[0]
            info = self.symtab.buscar(destino.get("valor"))
            if info is None:
                return  # _build_symtab ya reportó el identificador faltante.
            destino["type"] = info["tipo"]
            if info["tipo"] not in TIPOS_NUMERICOS:
                self._error(nodo, f"El operador '{valor}' requiere una variable numérica.")
                return
            nodo["type"] = info["tipo"]
            if info["valor"] is not None:
                nuevo = info["valor"] + (1 if tipo == "incremento" else -1)
                info["valor"] = nuevo
                destino["eval"] = nuevo
                nodo["eval"] = nuevo
            else:
                info["valor"] = None
            return

        if tipo == "sent_in":
            # cin permite la entrada de cualquier valor del tipo declarado.
            # Lo que se introducirá en tiempo de ejecución es desconocido.
            for hijo in hijos:
                if hijo.get("tipo") == "id":
                    info = self.symtab.buscar(hijo.get("valor"))
                    if info is not None:
                        hijo["type"] = info["tipo"]
                        info["valor"] = None
                else:
                    self._type_check(hijo)
            return

        if tipo == "seleccion":
            condicion = next((h for h in hijos if h.get("tipo") != "else"), None)
            if condicion is None:
                return
            self._type_check(condicion)
            if condicion.get("type") not in {None, "bool"}:
                self._error(condicion, "La condición debe ser de tipo 'bool'.")
            original = self._estado()
            ramas = [h for h in hijos if h.get("tipo") == "lista_sentencias"]
            rama_else = next((h for h in hijos if h.get("tipo") == "else"), None)
            self._restaurar_estado(original)
            for rama in ramas:
                self._type_check(rama)
            estado_then = self._estado()
            self._restaurar_estado(original)
            if rama_else is not None:
                self._type_check(rama_else)
                estado_else = self._estado()
            else:
                estado_else = original
            cond_val = condicion.get("eval")
            if isinstance(cond_val, bool):
                final = estado_then if cond_val else estado_else
            else:
                # Solo se conserva un valor cuando ambas ramas coinciden.
                final = {n: estado_then.get(n) if estado_then.get(n) == estado_else.get(n)
                         else None for n in original}
            self._restaurar_estado(final)
            return

        if tipo == "iteracion":
            if not hijos:
                return
            condicion = hijos[0]
            self._type_check(condicion)
            if condicion.get("type") not in {None, "bool"}:
                self._error(condicion, "La condición debe ser de tipo 'bool'.")
            original = self._estado()
            # No evaluar una sola iteración usando constantes que puede haber
            # cambiado una iteración anterior: evita resultados ficticios.
            modificadas = set().union(*(self._modificadas(h) for h in hijos[1:]))
            cuerpo = dict(original)
            for nombre in modificadas:
                cuerpo[nombre] = None
            self._restaurar_estado(cuerpo)
            for hijo in hijos[1:]:
                self._type_check(hijo)
            salida = dict(original)
            if condicion.get("eval") is not False:
                for nombre in modificadas:
                    salida[nombre] = None
            self._restaurar_estado(salida)
            return

        if tipo == "repeticion":
            # do-until: el cuerpo se procesa al menos una vez; la condición
            # es comprobada después. No se simulan vueltas adicionales.
            original = self._estado()
            for hijo in hijos:
                self._type_check(hijo)
            if hijos:
                condicion = hijos[-1]
                if condicion.get("type") not in {None, "bool"}:
                    self._error(condicion, "La condición debe ser de tipo 'bool'.")
                # Si se sabe que termina tras la primera vuelta, conservarla.
                if condicion.get("eval") is not True:
                    modificadas = self._modificadas(nodo)
                    estado = self._estado()
                    for nombre in modificadas:
                        estado[nombre] = None
                    self._restaurar_estado(estado)
            return

        if tipo == "operador" and valor in {"=", ":="}:
            if len(hijos) >= 2:
                # Primero la expresión DERECHA: y = y + 1 debe leer el valor
                # anterior de y antes de modificar la tabla.
                self._type_check(hijos[1])
                destino = hijos[0]
                info = self.symtab.buscar(destino.get("valor")) if destino.get("tipo") == "id" else None
                if info is not None:
                    destino["type"] = info["tipo"]
                self._verificar_asignacion(nodo, hijos)
            return

        for hijo in hijos:
            self._type_check(hijo)

        # Solo los nodos intermedios de expresión transmiten valor y tipo.
        nodos_transparentes = {"sent_expresion", "expresion", "comparacion",
                               "expresion_simple", "termino", "factor", "componente"}
        if len(hijos) == 1 and tipo in nodos_transparentes:
            hijo = hijos[0]
            if hijo.get("type") is not None:
                nodo["type"] = hijo["type"]
                if "eval" in hijo:
                    nodo["eval"] = hijo["eval"]

        operador = str(valor or "").lower()
        es_operador = tipo in {"suma_op", "mult_op", "pot_op", "operador", "op_relacional", "op_logico"}
        if es_operador and operador in OPERADORES_ARITMETICOS:
            self._verificar_aritmetica(nodo, hijos, operador)
        elif es_operador and (tipo == "op_relacional" or operador in OPERADORES_RELACIONALES):
            self._verificar_relacional(nodo, hijos, operador)
        elif es_operador and (tipo == "op_logico" or operador in OPERADORES_LOGICOS):
            self._verificar_logica(nodo, hijos, operador)

    def _verificar_asignacion(self, nodo, hijos):
        if len(hijos) < 2:
            return
        izquierdo, derecho = hijos[0], hijos[1]
        if izquierdo.get("tipo") != "id":
            self._error(izquierdo, "El destino de una asignación debe ser un identificador.")
            return
        info = self.symtab.buscar(izquierdo.get("valor"))
        tipo_destino = izquierdo.get("type")
        tipo_origen = derecho.get("type")
        if not info or not tipo_destino or not tipo_origen:
            return
        if not self._conversión_permitida(tipo_destino, tipo_origen):
            self._error(
                nodo,
                f"Tipos incompatibles: no se puede asignar '{tipo_origen}' a "
                f"'{izquierdo.get('valor')}' de tipo '{tipo_destino}'.",
            )
            info["valor"] = None
            return
        self._anotar_conversion(derecho, tipo_origen, tipo_destino)
        nodo["type"] = tipo_destino
        if "eval" in derecho:
            conocido = derecho["eval"]
            convertido = float(conocido) if tipo_destino == "float" else conocido
            nodo["eval"] = convertido
            izquierdo["eval"] = convertido
            info["valor"] = convertido
        else:
            info["valor"] = None

    def _verificar_aritmetica(self, nodo, hijos, operador):
        if len(hijos) not in {1, 2}:
            return
        if len(hijos) == 1:
            if operador not in {"+", "-"}:
                return
            operando = hijos[0]
            tipo = operando.get("type")
            if tipo and tipo not in TIPOS_NUMERICOS:
                self._error(nodo, f"Operador '{operador}' no admite operando '{tipo}'.")
                nodo.pop("type", None)
                nodo.pop("eval", None)
                return
            if tipo in TIPOS_NUMERICOS:
                nodo["type"] = tipo
                if "eval" in operando:
                    nodo["eval"] = (+operando["eval"] if operador == "+" else -operando["eval"])
            return

        izquierdo, derecho = hijos
        t_izq, t_der = izquierdo.get("type"), derecho.get("type")
        if not t_izq or not t_der:
            return
        if t_izq not in TIPOS_NUMERICOS or t_der not in TIPOS_NUMERICOS:
            self._error(nodo, f"Operador '{operador}' incompatible con '{t_izq}' y '{t_der}'.")
            return
        # En esta gramática, % se restringe a enteros (no a float ni bool).
        if operador == "%" and (t_izq != "int" or t_der != "int"):
            self._error(nodo, "Operador '%' requiere operandos 'int'.")
            return
        resultado = "float" if "float" in {t_izq, t_der} else "int"
        nodo["type"] = resultado
        self._anotar_conversion(izquierdo, t_izq, resultado)
        self._anotar_conversion(derecho, t_der, resultado)
        # Incluso si el operando izquierdo es dinámico, x/0 y x%0 son inválidos.
        if operador in {"/", "%"} and derecho.get("eval") == 0:
            self._error(nodo, "División por cero detectada." if operador == "/" else "Módulo por cero detectado.")
            return
        if "eval" not in izquierdo or "eval" not in derecho:
            return
        a, b = izquierdo["eval"], derecho["eval"]
        try:
            if operador == "+":
                calculado = a + b
            elif operador == "-":
                calculado = a - b
            elif operador == "*":
                calculado = a * b
            elif operador == "/":
                # Para enteros, división con truncamiento hacia cero.
                if resultado == "float":
                    calculado = a / b
                else:
                    cociente = abs(a) // abs(b)
                    calculado = -cociente if (a < 0) != (b < 0) else cociente
            elif operador == "%":
                # Resto consistente con el cociente truncado hacia cero.
                cociente = abs(a) // abs(b)
                cociente = -cociente if (a < 0) != (b < 0) else cociente
                calculado = a - cociente * b
            else:
                calculado = a ** b
            if isinstance(calculado, complex):
                self._error(nodo, "La operación produce un valor no numérico real.")
            elif resultado == "int" and isinstance(calculado, float):
                # Potencias negativas pueden producir float aun con dos int.
                nodo["type"] = "float"
                nodo["eval"] = calculado
            else:
                nodo["eval"] = calculado
        except (ArithmeticError, OverflowError, ValueError) as e:
            self._error(nodo, f"No se pudo evaluar la expresión constante: {e}.")

    def _verificar_relacional(self, nodo, hijos, operador):
        if len(hijos) != 2:
            return
        izquierdo, derecho = hijos
        t_izq, t_der = izquierdo.get("type"), derecho.get("type")
        if not t_izq or not t_der:
            return
        igualdad = operador in {"==", "!=", "<>", "="}
        ambos_numericos = t_izq in TIPOS_NUMERICOS and t_der in TIPOS_NUMERICOS
        ambos_bool = t_izq == t_der == "bool"
        if not ambos_numericos and not (igualdad and ambos_bool):
            self._error(nodo, f"Comparación '{operador}' incompatible con '{t_izq}' y '{t_der}'.")
            return
        nodo["type"] = "bool"
        if ambos_numericos:
            self._anotar_conversion(izquierdo, t_izq, "float" if "float" in {t_izq, t_der} else "int")
            self._anotar_conversion(derecho, t_der, "float" if "float" in {t_izq, t_der} else "int")
        if "eval" in izquierdo and "eval" in derecho:
            a, b = izquierdo["eval"], derecho["eval"]
            comparaciones = {"<": lambda: a < b, "<=": lambda: a <= b,
                             ">": lambda: a > b, ">=": lambda: a >= b,
                             "==": lambda: a == b, "=": lambda: a == b,
                             "!=": lambda: a != b, "<>": lambda: a != b}
            if operador in comparaciones:
                nodo["eval"] = comparaciones[operador]()

    def _verificar_logica(self, nodo, hijos, operador):
        unary = operador in {"!", "not", "no"}
        if (unary and len(hijos) != 1) or (not unary and len(hijos) != 2):
            return
        if any(h.get("type") is None for h in hijos):
            return
        if any(h["type"] != "bool" for h in hijos):
            self._error(nodo, f"Operador lógico '{operador}' requiere operandos 'bool'.")
            return
        nodo["type"] = "bool"
        if all("eval" in h for h in hijos):
            if unary:
                nodo["eval"] = not hijos[0]["eval"]
            elif operador in {"&&", "and", "y"}:
                nodo["eval"] = hijos[0]["eval"] and hijos[1]["eval"]
            elif operador in {"||", "or", "o"}:
                nodo["eval"] = hijos[0]["eval"] or hijos[1]["eval"]

    def generar_arbol_visual(self, nodo, prefijo="", es_ultimo=True, es_raiz=True):
        if not isinstance(nodo, dict):
            return ""
        marcador = "" if es_raiz else ("└── " if es_ultimo else "├── ")
        tipo = nodo.get("tipo", "Desconocido")
        texto = f"{tipo}: {nodo['valor']}" if nodo.get("valor") is not None else tipo
        atributos = []
        for clave, etiqueta in (("dtype", "Tipo heredado"), ("type", "Tipo"),
                                ("eval", "Valor"), ("conversion", "Conversión")):
            if clave in nodo:
                atributos.append(f"{etiqueta}: {nodo[clave]}")
        if atributos:
            texto += " [" + ", ".join(atributos) + "]"
        resultado = f"{prefijo}{marcador}{texto}\n"
        hijos = self._hijos(nodo)
        siguiente = prefijo + ("" if es_raiz else ("    " if es_ultimo else "│   "))
        for i, hijo in enumerate(hijos):
            resultado += self.generar_arbol_visual(hijo, siguiente, i == len(hijos) - 1, False)
        return resultado
