# Documentación Técnica: Analizador Sintáctico Descendente Recursivo

## Objetivo General
Diseñar e implementar un analizador sintáctico descendente recursivo (Fase 2 del compilador) que tome como entrada los tokens validados por el analizador léxico de la Fase 1. Este componente construye un Árbol Sintáctico Abstracto (AST), valida la estructura gramatical del programa y reporta los errores sintácticos indicando la línea y columna exactas.

---

## 1. Diseño y Metodología

### Tipo de Analizador
Se implementó un **Analizador Sintáctico Descendente Recursivo**.
- **Descendente**: Construye el árbol de derivación desde la raíz (el símbolo inicial) hacia las hojas (los tokens).
- **Recursivo**: Consiste en un conjunto de procedimientos (funciones), uno por cada símbolo no terminal de la gramática. La recursión ocurre cuando las funciones se invocan entre sí.
- **Gramática LL(1)**: Para poder utilizar este enfoque, las reglas gramaticales originales (con recursividad por la izquierda) fueron factorizadas.

### Integración en el IDE
- **Flujo de Trabajo**: El IDE invoca externamente al analizador `comp/parser.py` pasándole como argumento el archivo `_tokens.txt`.
- **Generación del AST**: El parser escupe un archivo JSON estructurado con jerarquía de nodos padre-hijo.
- **Visualización Gráfica**: La interfaz (`interface.py`) lee el archivo JSON y dibuja dinámicamente un `QTreeWidget`. Se añadieron iconos representativos (por ejemplo, llaves para palabras reservadas, engranes para operadores, cubos para literales y números) haciendo la navegación visualmente atractiva y colapsable (estilo carpetas).

---

## 2. Gramática Implementada (Adaptada para Recursión)

A continuación se muestra un resumen de las funciones gramaticales principales implementadas en el código:

- `programa` → `main { lista_declaracion }`
- `lista_declaracion` → `declaracion lista_declaracion_prima`
- `declaracion` → `declaracion_variable` | `lista_sentencias`
- `declaracion_variable` → `tipo_dato identificador ;`
- `tipo_dato` → `int` | `float` | `bool`
- `lista_sentencias` → `sentencia lista_sentencias_prima`
- `sentencia` → `seleccion` | `iteracion` | `repeticion` | `sent_in` | `sent_out` | `asignacion`

*(Las expresiones aritméticas mantienen precedencia mediante los niveles `expresion` > `expresion_simple` > `termino` > `factor` > `componente`)*

---

## 3. Manejo y Recuperación de Errores

El analizador utiliza una técnica básica de sincronización basada en **"Panic Mode"**.
Cuando se detecta un token que no corresponde a la regla gramatical esperada:
1. Se registra el error en una lista de forma detallada:
   `Error Sintáctico: Se esperaba ';' pero se encontró 'int' | Fila: X | Columna: Y`
2. El puntero de lectura avanza para intentar encontrar un token de sincronización (como un `;` o el cierre de una llave `}`) para no colgarse y poder seguir detectando errores en el resto del archivo.
3. Al finalizar, la lista de errores se guarda en `_errores_sintacticos.txt` y se muestran en rojo dentro de la consola del IDE.

---

## 4. Ejemplos de Pruebas

Para validar el compilador se diseñaron varios archivos `.cmp`:

### Prueba 1: Código Válido (`prueba_valida1.cmp`)
Valida la asignación de variables, condicional `if`, precedencia de operadores matemáticos (`*` frente a `+`).

### Prueba 2: Iteraciones (`prueba_valida2.cmp`)
Demuestra que los ciclos `while` y `do-while` generan correctamente sus ramas en el AST y procesan las sentencias bloque anidadas sin problemas.

### Prueba 3: Detección de Errores (`prueba_errores.cmp`)
Diseñado intencionalmente con fallas (ausencia de `;`, llaves rotas y asignaciones incompletas). El panel de "Errores Sintácticos" muestra exactamente dónde y por qué falló el programa.

---

## Conclusión
La integración del analizador sintáctico provee retroalimentación visual instantánea al desarrollador mediante la representación colapsable del AST. Se cumple con la trazabilidad solicitada para identificar de forma precisa la ubicación de los errores sintácticos mediante fila y columna.
