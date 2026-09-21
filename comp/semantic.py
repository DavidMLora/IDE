import json

class TablaSimbolos:
    def __init__(self):
        self.tabla = {}
        self.location = 0

    def insertar(self, nombre, linea, tipo_dato=None):
        if nombre not in self.tabla:
            # Nueva declaración
            self.tabla[nombre] = {
                'tipo': tipo_dato,
                'memloc': self.location,
                'lineas': [linea]
            }
            self.location += 1
            return True
        else:
            # Evita registrar números de línea duplicados si la variable se usa varias veces en la misma fila
            if linea not in self.tabla[nombre]['lineas']:
                self.tabla[nombre]['lineas'].append(linea)
            return False

    def buscar(self, nombre):
        return self.tabla.get(nombre, None)

    def imprimir_tabla(self):
        print(f"{'Nombre':<15} | {'Tipo':<10} | {'Loc':<5} | {'Líneas'}")
        print("-" * 50)
        for nombre, info in self.tabla.items():
            lineas_str = ", ".join(map(str, info['lineas']))
            print(f"{nombre:<15} | {info['tipo']:<10} | {info['memloc']:<5} | {lineas_str}")
            
class AnalizadorSemantico:
    def __init__(self, ast):
        self.ast = ast
        self.symtab = TablaSimbolos()
        self.errores = []

    def analizar(self, ruta_salida=None):
        self._build_symtab(self.ast)
        self._type_check(self.ast)
        
        # 3. Generar la representación visual para la UI
        arbol_texto = self.generar_arbol_visual(self.ast)
        
        # Guardar en la ruta dinámica indicada por la interfaz (.compilados/)
        if ruta_salida:
            try:
                with open(ruta_salida, "w", encoding="utf-8") as f:
                    f.write("ÁRBOL SINTÁCTICO ANOTADO (Propagación de Tipos y Valores)\n")
                    f.write("="*60 + "\n")
                    f.write(arbol_texto)
            except Exception as e:
                pass

        return self.symtab, self.errores
        self._build_symtab(self.ast)
        self._type_check(self.ast)
        
        # 3. Generar la representación visual para la UI
        arbol_texto = self.generar_arbol_visual(self.ast)
        
        # Guardar en un archivo de texto para que el panel de tu IDE lo pueda cargar
        try:
            with open("arbol_anotado_visual.txt", "w", encoding="utf-8") as f:
                f.write("ÁRBOL SINTÁCTICO ANOTADO (Propagación de Tipos y Valores)\n")
                f.write("="*60 + "\n")
                f.write(arbol_texto)
        except Exception as e:
            pass

        return self.symtab, self.errores
        self._build_symtab(self.ast)
        self._type_check(self.ast)
        return self.symtab, self.errores
        
    def _obtener_linea(self, nodo):
        """Busca recursivamente el número de línea en el nodo o en sus hijos"""
        if not isinstance(nodo, dict): return 'N/A'
        
        if nodo.get('fila'): 
            return nodo.get('fila')
            
        for hijo in nodo.get('hijos', []):
            fila = self._obtener_linea(hijo)
            if fila != 'N/A': 
                return fila
                
        return 'N/A'

    # ---------------------------------------------------------
    # FASE 1: Construcción de la Tabla de Símbolos (Preorden)
    # ---------------------------------------------------------
    def _build_symtab(self, nodo):
        if not nodo or not isinstance(nodo, dict):
            return

        tipo_nodo = nodo.get('tipo')
        hijos = nodo.get('hijos', [])
        linea = self._obtener_linea(nodo)

        # 1. Declaración de variables
        if tipo_nodo == 'declaracion_variable':
            tipo_dato = None
            identificadores = []
            
            for hijo in hijos:
                if hijo.get('tipo') == 'tipo_dato':
                    tipo_dato = hijo.get('valor')
                elif hijo.get('tipo') == 'identificadores':
                    for subhijo in hijo.get('hijos', []):
                        if subhijo.get('tipo') == 'id':
                            identificadores.append(subhijo.get('valor'))
            
            for nombre in identificadores:
                if not self.symtab.insertar(nombre, linea, tipo_dato):
                    msg = f"Error Semántico (Línea {linea}): Variable '{nombre}' ya fue declarada."
                    if msg not in self.errores:
                        self.errores.append(msg)
            
            # Detenemos la recursividad aquí para no registrar la declaración como un "uso" posterior
            return

        # 2. Uso de variables (Captura todo limpiamente: asignaciones, sumas, condicionales)
        elif tipo_nodo == 'id':
            nombre = nodo.get('valor')
            
            # Filtramos palabras clave que el Lexer pudo confundir con IDs
            if nombre and nombre not in ['true', 'false', 'then', 'until']:
                if self.symtab.buscar(nombre) is None:
                    msg = f"Error Semántico (Línea {linea}): Variable '{nombre}' no declarada."
                    if msg not in self.errores:
                        self.errores.append(msg)
                else:
                    self.symtab.insertar(nombre, linea)

        # Recorrer los hijos recursivamente
        for hijo in hijos:
            self._build_symtab(hijo)

    # ---------------------------------------------------------
    # FASE 2: Inferencia y Verificación de Tipos (Postorden)
    # ---------------------------------------------------------
    def generar_arbol_visual(self, nodo, prefijo="", es_ultimo=True, es_raiz=True):
        """Genera un string con formato de árbol mostrando cómo se propagan los atributos"""
        if not isinstance(nodo, dict): return ""
            
        resultado = ""
        marcador = "" if es_raiz else ("└── " if es_ultimo else "├── ")
        
        tipo_nodo = nodo.get('tipo', 'Desconocido')
        lexema = nodo.get('valor', '')
        
        # Recopilar los atributos semánticos inyectados
        atributos = []
        if 'type' in nodo:
            atributos.append(f"Tipo: {nodo['type']}")
        if 'eval' in nodo:
            # Formatear flotantes para que no tengan demasiados decimales
            val = nodo['eval']
            str_val = f"{val:.2f}" if isinstance(val, float) else str(val)
            atributos.append(f"Valor: {str_val}")
            
        str_atributos = f" [{', '.join(atributos)}]" if atributos else ""
        nombre_mostrar = f"{tipo_nodo}: {lexema}" if lexema else tipo_nodo
        
        resultado += f"{prefijo}{marcador}{nombre_mostrar}{str_atributos}\n"
        
        hijos = nodo.get('hijos', [])
        prefijo_hijos = prefijo + ("" if es_raiz else ("    " if es_ultimo else "│   "))
        
        for i, hijo in enumerate(hijos):
            resultado += self.generar_arbol_visual(hijo, prefijo_hijos, i == len(hijos) - 1, False)
            
        return resultado

    # ---------------------------------------------------------
    # FASE 2: Inferencia de Tipos y Propagación de Valores
    # ---------------------------------------------------------
    def _type_check(self, nodo):
        if not nodo or not isinstance(nodo, dict):
            return

        hijos = nodo.get('hijos', [])
        
        # 1. Recorrido postorden: procesar hijos primero
        for hijo in hijos:
            self._type_check(hijo)

        tipo_nodo = nodo.get('tipo')
        linea = self._obtener_linea(nodo)

        # 2. Asignar tipos y valores base a las hojas
        if tipo_nodo == 'id':
            nombre = nodo.get('valor')
            info = self.symtab.buscar(nombre)
            if info:
                nodo['type'] = info['tipo'] 
                # El valor de una variable es dinámico, no se conoce en tiempo de compilación
                # a menos que hagamos un intérprete completo.
                
        elif tipo_nodo == 'numero':
            valor = nodo.get('valor', '0')
            if '.' in valor:
                nodo['type'] = 'float'
                nodo['eval'] = float(valor)
            else:
                nodo['type'] = 'int'
                nodo['eval'] = int(valor)
            
        elif tipo_nodo == 'booleano':
            nodo['type'] = 'bool'
            nodo['eval'] = True if nodo.get('valor') == 'true' else False

        # 3. Operaciones Aritméticas (Propagación ascendente)
        elif tipo_nodo in ['suma_op', 'mult_op', 'pot_op', 'operador']:
            op = nodo.get('valor')
            if op in ['+', '-', '*', '/', '^']:
                hijo_izq = hijos[0] if len(hijos) > 0 else {}
                hijo_der = hijos[1] if len(hijos) > 1 else {}
                
                t_izq = hijo_izq.get('type')
                t_der = hijo_der.get('type')
                
                if t_izq == 'float' or t_der == 'float':
                    nodo['type'] = 'float'
                else:
                    nodo['type'] = 'int'

                # Intentar calcular y propagar el valor si ambos hijos son constantes numéricas
                v_izq = hijo_izq.get('eval')
                v_der = hijo_der.get('eval')
                
                if v_izq is not None and v_der is not None:
                    try:
                        if op == '+': nodo['eval'] = v_izq + v_der
                        elif op == '-': nodo['eval'] = v_izq - v_der
                        elif op == '*': nodo['eval'] = v_izq * v_der
                        elif op == '/': 
                            nodo['eval'] = v_izq / v_der if nodo['type'] == 'float' else v_izq // v_der
                        elif op == '^': nodo['eval'] = v_izq ** v_der
                    except ZeroDivisionError:
                        self.errores.append(f"Error Semántico (Línea {linea}): División por cero detectada.")

            # 4. Asignación (operador =)
            elif op == '=':
                if len(hijos) >= 2:
                    hijo_izq_nodo = hijos[0]
                    hijo_der_nodo = hijos[1]
                    
                    if hijo_izq_nodo.get('tipo') == 'id':
                        nombre = hijo_izq_nodo.get('valor')
                        info_var = self.symtab.buscar(nombre)
                        
                        if info_var:
                            tipo_var = info_var['tipo']
                            tipo_exp = hijo_der_nodo.get('type')

                            if tipo_var and tipo_exp:
                                if tipo_var == 'int' and tipo_exp == 'float':
                                    msg = f"Error Semántico (Línea {linea}): Tipos incompatibles. No se puede asignar un valor 'float' a la variable '{nombre}' de tipo 'int'."
                                    if msg not in self.errores:
                                        self.errores.append(msg)

        # 5. Operadores Relacionales y Lógicos
        elif tipo_nodo in ['op_relacional', 'op_logico']:
            nodo['type'] = 'bool'
            
        # 6. Estructuras de control
        elif tipo_nodo in ['seleccion', 'iteracion', 'repeticion']:
            if len(hijos) > 0:
                tipo_cond = hijos[0].get('type')
                if tipo_cond and tipo_cond not in ['bool', 'int']:
                    msg = f"Error Semántico (Línea {linea}): La condición debe ser booleana o entera."
                    if msg not in self.errores:
                        self.errores.append(msg)
        if not nodo or not isinstance(nodo, dict):
            return

        hijos = nodo.get('hijos', [])
        
        # 1. Recorrido postorden: inferimos primero los tipos de los hijos
        for hijo in hijos:
            self._type_check(hijo)

        tipo_nodo = nodo.get('tipo')
        linea = self._obtener_linea(nodo)

        # 2. Asignar tipos base a las hojas
        if tipo_nodo == 'id':
            nombre = nodo.get('valor')
            info = self.symtab.buscar(nombre)
            if info:
                nodo['type'] = info['tipo'] 
                
        elif tipo_nodo == 'numero':
            valor = nodo.get('valor', '')
            nodo['type'] = 'float' if '.' in valor else 'int'
            
        elif tipo_nodo == 'booleano':
            nodo['type'] = 'bool'

        # 3. Operaciones Aritméticas
        elif tipo_nodo in ['suma_op', 'mult_op', 'pot_op', 'operador']:
            op = nodo.get('valor')
            if op in ['+', '-', '*', '/', '^']:
                hijo_izq = hijos[0].get('type') if len(hijos) > 0 else None
                hijo_der = hijos[1].get('type') if len(hijos) > 1 else None
                
                if hijo_izq == 'float' or hijo_der == 'float':
                    nodo['type'] = 'float'
                else:
                    nodo['type'] = 'int'

            # 4. Asignación (operador =)
            elif op == '=':
                if len(hijos) >= 2:
                    hijo_izq_nodo = hijos[0]
                    hijo_der_nodo = hijos[1]
                    
                    if hijo_izq_nodo.get('tipo') == 'id':
                        nombre = hijo_izq_nodo.get('valor')
                        info_var = self.symtab.buscar(nombre)
                        
                        if info_var:
                            tipo_var = info_var['tipo']
                            tipo_exp = hijo_der_nodo.get('type')

                            if tipo_var and tipo_exp:
                                if tipo_var == 'int' and tipo_exp == 'float':
                                    msg = f"Error Semántico (Línea {linea}): Tipos incompatibles. No se puede asignar un valor 'float' a la variable '{nombre}' de tipo 'int'."
                                    if msg not in self.errores:
                                        self.errores.append(msg)

        # 5. Operadores Relacionales y Lógicos
        elif tipo_nodo in ['op_relacional', 'op_logico']:
            nodo['type'] = 'bool'
            
        # 6. Estructuras de control (If, While, Do-While)
        elif tipo_nodo in ['seleccion', 'iteracion', 'repeticion']:
            if len(hijos) > 0:
                nodo_condicion = hijos[0]
                tipo_cond = nodo_condicion.get('type')
                
                if tipo_cond and tipo_cond not in ['bool', 'int']:
                    msg = f"Error Semántico (Línea {linea}): La condición de la estructura de control debe ser booleana o entera."
                    if msg not in self.errores:
                        self.errores.append(msg)