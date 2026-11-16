"""
parser.py - Parser de BabyDuck con análisis semántico de variables (entrega 2).

Es la misma gramática de la entrega 1, ahora con PUNTOS NEURÁLGICOS: lugares de
la gramática donde, además de reconocer la sintaxis, se ejecuta una acción que
crea y llena el Directorio de Funciones y las Tablas de Variables.

En PLY hay dos formas de poner un punto neurálgico:

  1. Al FINAL de una regla: es el código de la propia función `p_*`, que PLY
     ejecuta cuando termina de reconocer la regla completa.

  2. A la MITAD de una regla: se agrega un no terminal vacío (aquí todos se
     llaman `np_*`) justo en el lugar deseado. Como no consume tokens, PLY lo
     "reconoce" de inmediato y ejecuta su función en ese momento. Dentro de esa
     función, `p[-1]` es el símbolo que quedó justo antes (p. ej. el ID).

Puntos neurálgicos de esta entrega (los números son los del documento):

    1  np_crear_programa   crea el directorio y el alcance global
    2  p_decl              agrega las variables declaradas a la tabla actual
    3  np_crear_funcion    da de alta la función y cambia de alcance
    4  p_param             agrega un parámetro a la función actual
    5  np_cerrar_funcion   regresa al alcance global
    6  np_verificar_destino   la variable a la que se asigna debe existir
    7  p_operando_id       la variable usada en una expresión debe existir
    8  np_verificar_funcion   la función llamada debe existir
"""

import ply.yacc as yacc

from directorio import DirectorioFunciones
from errores import ErrorSintactico
from lexer import construir_lexer, tokens  # noqa: F401  (PLY necesita `tokens`)

start = "programa"

# Directorio del programa que se está compilando. `analizar()` crea uno nuevo
# en cada llamada; las acciones de la gramática lo van llenando.
directorio = None


def linea_del_anterior(p):
    """
    Línea del token que está justo antes de un punto neurálgico `np_*`.
    (`p.stack` es la pila del parser; su tope es ese token.)
    """
    return getattr(p.stack[-1], "lineno", p.lexer.lineno)


# ---------------------------------------------------------------------------
# Programa
# ---------------------------------------------------------------------------
def p_programa(p):
    """programa : PROGRAM ID np_crear_programa SEMICOLON vars_opt funcs MAIN body END"""


def p_np_crear_programa(p):
    """np_crear_programa :"""
    # PUNTO 1: ya se leyó `program ID`. Se registra el alcance global con el
    # nombre del programa; las variables que sigan serán globales.
    directorio.crear_programa(p[-1])


# ---------------------------------------------------------------------------
# Declaración de variables
# ---------------------------------------------------------------------------
def p_vars(p):
    """vars_opt   : VAR lista_decl
                  | empty
    lista_decl : decl lista_decl
               | decl"""


def p_decl(p):
    """decl : lista_ids COLON tipo SEMICOLON"""
    # PUNTO 2: se terminó una declaración como `a, b : int;`. Hasta aquí se
    # conoce el tipo, así que ahora se dan de alta todos los ids de la lista.
    # `agregar_variable` valida que ninguno esté doblemente declarado.
    for nombre, linea in p[1]:
        directorio.agregar_variable(nombre, p[3], linea)


def p_lista_ids(p):
    """lista_ids : ID COMMA lista_ids
                 | ID"""
    # Junta los ids (con su línea) en una lista para usarla en el punto 2.
    resto = p[3] if len(p) == 4 else []
    p[0] = [(p[1], p.lineno(1))] + resto


def p_tipo(p):
    """tipo : INT
            | FLOAT"""
    p[0] = p[1]


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------
def p_funcs(p):
    """funcs : func funcs
             | empty"""


def p_func(p):
    """func : VOID ID np_crear_funcion LPAREN params_opt RPAREN LBRACKET vars_opt body RBRACKET np_cerrar_funcion SEMICOLON"""


def p_np_crear_funcion(p):
    """np_crear_funcion :"""
    # PUNTO 3: ya se leyó `void ID`. Se valida que la función no exista, se
    # crea su entrada (con su tabla de variables vacía) y pasa a ser el
    # alcance actual: parámetros y variables que sigan son locales a ella.
    directorio.crear_funcion(p[-1], linea_del_anterior(p))


def p_np_cerrar_funcion(p):
    """np_cerrar_funcion :"""
    # PUNTO 5: terminó la función; lo que siga vuelve a ser alcance global.
    directorio.cerrar_funcion()


def p_params(p):
    """params_opt   : lista_params
                    | empty
    lista_params : param COMMA lista_params
                 | param"""


def p_param(p):
    """param : ID COLON tipo"""
    # PUNTO 4: un parámetro es una variable local de la función y además se
    # anota su tipo en la firma (lista de parámetros) de la función.
    directorio.agregar_variable(p[1], p[3], p.lineno(1), es_parametro=True)


# ---------------------------------------------------------------------------
# Cuerpo y estatutos
# ---------------------------------------------------------------------------
def p_body(p):
    """body      : LBRACE estatutos RBRACE
    estatutos : estatuto estatutos
              | empty
    estatuto  : asigna
              | condicion
              | ciclo
              | llamada
              | imprime"""


def p_asigna(p):
    """asigna : ID np_verificar_destino ASSIGN expresion SEMICOLON"""


def p_np_verificar_destino(p):
    """np_verificar_destino :"""
    # PUNTO 6: la variable del lado izquierdo de `=` debe estar declarada.
    directorio.buscar_variable(p[-1], linea_del_anterior(p))


def p_condicion(p):
    """condicion : IF LPAREN expresion RPAREN body else_opt SEMICOLON
    else_opt  : ELSE body
              | empty"""


def p_ciclo(p):
    """ciclo : WHILE LPAREN expresion RPAREN DO body SEMICOLON"""


def p_llamada(p):
    """llamada    : ID np_verificar_funcion LPAREN args_opt RPAREN SEMICOLON
    args_opt   : lista_args
               | empty
    lista_args : expresion COMMA lista_args
               | expresion"""


def p_np_verificar_funcion(p):
    """np_verificar_funcion :"""
    # PUNTO 8: solo se puede llamar a una función que ya esté en el directorio.
    directorio.buscar_funcion(p[-1], linea_del_anterior(p))


def p_imprime(p):
    """imprime     : PRINT LPAREN lista_print RPAREN SEMICOLON
    lista_print : item_print COMMA lista_print
                | item_print
    item_print  : expresion
                | CTE_STRING"""


# ---------------------------------------------------------------------------
# Expresiones
# ---------------------------------------------------------------------------
def p_expresion(p):
    """expresion       : exp expresion_resto
    expresion_resto : op_rel exp
                    | empty
    op_rel          : GT
                    | LT
                    | NE"""


def p_exp(p):
    """exp       : termino exp_resto
    exp_resto : PLUS exp
              | MINUS exp
              | empty"""


def p_termino(p):
    """termino       : factor termino_resto
    termino_resto : TIMES termino
                  | DIVIDE termino
                  | empty"""


def p_factor(p):
    """factor : LPAREN expresion RPAREN
              | PLUS operando
              | MINUS operando
              | operando"""


def p_operando_id(p):
    """operando : ID"""
    # PUNTO 7: toda variable usada en una expresión debe estar declarada
    # (en la función actual o como global).
    directorio.buscar_variable(p[1], p.lineno(1))


def p_operando_cte(p):
    """operando : cte
    cte      : CTE_INT
             | CTE_FLOAT"""


# ---------------------------------------------------------------------------
# Producción vacía y manejo de errores
# ---------------------------------------------------------------------------
def p_empty(p):
    """empty :"""


def p_error(tok):
    if tok is None:
        raise ErrorSintactico("el programa terminó antes de lo esperado (¿falta 'end'?)")
    raise ErrorSintactico(f"no se esperaba '{tok.value}' (token {tok.type})", tok.lineno)


_parser = yacc.yacc(debug=False, write_tables=False)


def analizar(codigo):
    """
    Compila `codigo` hasta el análisis semántico de variables.

    Regresa el DirectorioFunciones ya lleno. Si el programa tiene un error
    lanza ErrorLexico, ErrorSintactico o ErrorSemantico.
    """
    global directorio
    directorio = DirectorioFunciones()
    _parser.parse(codigo, lexer=construir_lexer())
    return directorio
