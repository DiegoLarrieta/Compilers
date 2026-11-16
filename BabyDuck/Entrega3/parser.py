"""
parser.py - Parser de BabyDuck con generación de cuádruplos (entrega 3).

Misma gramática y mismos puntos semánticos de la entrega 2, más los puntos
neurálgicos que traducen expresiones y estatutos lineales a cuádruplos.

Recordatorio de cómo se pone un punto neurálgico en PLY:
  * al FINAL de una regla  -> es el código de la función `p_*` de esa regla;
  * a la MITAD de una regla -> un no terminal vacío `np_*` puesto en ese lugar
    (dentro de su función, `p[-1]` es el símbolo que quedó justo antes).

Puntos de la entrega 2 (directorio de funciones y tablas de variables):

    S1 np_crear_programa      S5 np_cerrar_funcion
    S2 p_decl                 S6 np_meter_destino (verifica la variable)
    S3 np_crear_funcion       S7 p_operando_id    (verifica la variable)
    S4 p_param                S8 np_verificar_funcion

Puntos nuevos de esta entrega (los números son los del documento):

     1 p_operando_id          mete el id y su tipo a PilaO / PTipos
     2 p_operando_cte         mete la constante y su tipo
     3 np_meter_operador      mete + - * / > < != a POper
     4 np_resolver_mult       si el tope de POper es * o /, genera el cuádruplo
     5 np_resolver_suma       si el tope de POper es + o -, genera el cuádruplo
     6 np_resolver_rel        si el tope de POper es relacional, genera el cuádruplo
     7 np_fondo_falso         al abrir paréntesis mete el fondo falso
     8 np_quitar_fondo        al cerrar paréntesis lo quita
     9 np_negar               menos unario
    10 np_meter_destino       mete la variable destino de la asignación
    11 np_meter_operador      mete el "=" a POper (es la misma acción del punto 3)
    12 np_generar_asigna      genera (=, valor, _, destino)
    13 np_print_expresion     genera (print, _, _, valor)
    14 p_item_print_letrero   genera (print, _, _, "letrero")
    15 np_verificar_condicion la condición de if / while debe ser booleana
    16 np_sacar_argumento     saca de la pila el valor de un argumento
"""

import ply.yacc as yacc

from cuadruplos import (OPERADORES_MULT, OPERADORES_REL, OPERADORES_SUMA,
                        GeneradorCuadruplos, tipo_de_constante)
from directorio import DirectorioFunciones
from errores import ErrorSintactico
from lexer import construir_lexer, tokens  # noqa: F401  (PLY necesita `tokens`)

start = "programa"

# Estado del programa que se está compilando. `analizar()` crea objetos nuevos
# en cada llamada; las acciones de la gramática los van llenando.
directorio = None   # Directorio de funciones y tablas de variables (entrega 2)
generador = None    # Pilas y fila de cuádruplos (entrega 3)


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
    # PUNTO S1: ya se leyó `program ID`. Se registra el alcance global con el
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
    # PUNTO S2: se terminó una declaración como `a, b : int;`. Hasta aquí se
    # conoce el tipo, así que ahora se dan de alta todos los ids de la lista.
    # `agregar_variable` valida que ninguno esté doblemente declarado.
    for nombre, linea in p[1]:
        directorio.agregar_variable(nombre, p[3], linea)


def p_lista_ids(p):
    """lista_ids : ID COMMA lista_ids
                 | ID"""
    # Junta los ids (con su línea) en una lista para usarla en el punto S2.
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
    # PUNTO S3: ya se leyó `void ID`. Se valida que la función no exista, se
    # crea su entrada (con su tabla de variables vacía) y pasa a ser el
    # alcance actual: parámetros y variables que sigan son locales a ella.
    directorio.crear_funcion(p[-1], linea_del_anterior(p))


def p_np_cerrar_funcion(p):
    """np_cerrar_funcion :"""
    # PUNTO S5: terminó la función; lo que siga vuelve a ser alcance global.
    directorio.cerrar_funcion()


def p_params(p):
    """params_opt   : lista_params
                    | empty
    lista_params : param COMMA lista_params
                 | param"""


def p_param(p):
    """param : ID COLON tipo"""
    # PUNTO S4: un parámetro es una variable local de la función y además se
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
    """asigna : ID np_meter_destino ASSIGN np_meter_operador expresion np_generar_asigna SEMICOLON"""


def p_np_meter_destino(p):
    """np_meter_destino :"""
    # PUNTO S6 + PUNTO 10: la variable del lado izquierdo de `=` debe estar
    # declarada. Se mete a PilaO (y su tipo a PTipos) para usarla al final.
    variable = directorio.buscar_variable(p[-1], linea_del_anterior(p))
    generador.meter_operando(variable.nombre, variable.tipo)


def p_np_meter_operador(p):
    """np_meter_operador :"""
    # PUNTO 3 (y 11): el operador que se acaba de leer queda pendiente en POper.
    # Se usa para + - * / > < != y también para el "=" de la asignación.
    generador.meter_operador(p[-1])


def p_np_generar_asigna(p):
    """np_generar_asigna :"""
    # PUNTO 12: ya se tradujo toda la expresión; su resultado está en el tope
    # de PilaO. Se valida con el cubo y se genera (=, valor, _, destino).
    generador.asignar(p.lexer.lineno)


def p_condicion(p):
    """condicion : IF LPAREN expresion RPAREN np_verificar_condicion body else_opt SEMICOLON
    else_opt  : ELSE body
              | empty"""


def p_ciclo(p):
    """ciclo : WHILE LPAREN expresion RPAREN np_verificar_condicion DO body SEMICOLON"""


def p_np_verificar_condicion(p):
    """np_verificar_condicion :"""
    # PUNTO 15: los cuádruplos de la condición ya se generaron. Se saca su
    # resultado de la pila y se valida que sea booleano. `p[-4]` es la palabra
    # `if` o `while`, que quedó 4 símbolos atrás: IF ( expresion ) <aquí>.
    # Los saltos (GOTOF / GOTO) se generan en la siguiente entrega.
    generador.verificar_condicion(p[-4], linea_del_anterior(p))


def p_llamada(p):
    """llamada    : ID np_verificar_funcion LPAREN args_opt RPAREN SEMICOLON
    args_opt   : lista_args
               | empty
    lista_args : expresion np_sacar_argumento COMMA lista_args
               | expresion np_sacar_argumento"""


def p_np_verificar_funcion(p):
    """np_verificar_funcion :"""
    # PUNTO S8: solo se puede llamar a una función que ya esté en el directorio.
    directorio.buscar_funcion(p[-1], linea_del_anterior(p))


def p_np_sacar_argumento(p):
    """np_sacar_argumento :"""
    # PUNTO 16: cada argumento es una expresión que ya generó sus cuádruplos.
    # Su resultado se saca de la pila para dejarla limpia. El paso de
    # parámetros (PARAM / GOSUB) se genera en la siguiente entrega.
    generador.descartar_argumento()


def p_imprime(p):
    """imprime     : PRINT LPAREN lista_print RPAREN SEMICOLON
    lista_print : item_print COMMA lista_print
                | item_print
    item_print  : expresion np_print_expresion"""


def p_np_print_expresion(p):
    """np_print_expresion :"""
    # PUNTO 13: se imprime el resultado de la expresión (tope de PilaO).
    generador.imprimir_expresion()


def p_item_print_letrero(p):
    """item_print : CTE_STRING"""
    # PUNTO 14: se imprime un letrero. No pasa por las pilas.
    generador.imprimir_letrero(p[1])


# ---------------------------------------------------------------------------
# Expresiones
# ---------------------------------------------------------------------------
# La precedencia sale del ORDEN en que se resuelven los operadores pendientes:
#   * al terminar un factor  se resuelven * y /   (punto 4)
#   * al terminar un término se resuelven + y -   (punto 5)
#   * al terminar la segunda exp se resuelve el relacional (punto 6)
def p_expresion(p):
    """expresion       : exp expresion_resto
    expresion_resto : op_rel np_meter_operador exp np_resolver_rel
                    | empty"""


def p_op_rel(p):
    """op_rel : GT
              | LT
              | NE"""
    # Se regresa el lexema para que np_meter_operador lo encuentre en p[-1].
    p[0] = p[1]


def p_np_resolver_rel(p):
    """np_resolver_rel :"""
    # PUNTO 6: ya están los dos lados de la comparación; se genera su cuádruplo.
    generador.resolver(OPERADORES_REL, p.lexer.lineno)


def p_exp(p):
    """exp       : termino np_resolver_suma exp_resto
    exp_resto : PLUS np_meter_operador exp
              | MINUS np_meter_operador exp
              | empty"""


def p_np_resolver_suma(p):
    """np_resolver_suma :"""
    # PUNTO 5: se terminó un término. Si hay un + o - pendiente en el tope de
    # POper, sus dos operandos ya están listos: se genera el cuádruplo.
    generador.resolver(OPERADORES_SUMA, p.lexer.lineno)


def p_termino(p):
    """termino       : factor np_resolver_mult termino_resto
    termino_resto : TIMES np_meter_operador termino
                  | DIVIDE np_meter_operador termino
                  | empty"""


def p_np_resolver_mult(p):
    """np_resolver_mult :"""
    # PUNTO 4: se terminó un factor. Si hay un * o / pendiente en el tope de
    # POper, se genera su cuádruplo.
    generador.resolver(OPERADORES_MULT, p.lexer.lineno)


def p_factor(p):
    """factor : LPAREN np_fondo_falso expresion RPAREN np_quitar_fondo
              | PLUS operando
              | MINUS operando np_negar
              | operando"""


def p_np_fondo_falso(p):
    """np_fondo_falso :"""
    # PUNTO 7: el fondo falso separa lo de adentro del paréntesis de los
    # operadores que estaban pendientes afuera.
    generador.meter_fondo_falso()


def p_np_quitar_fondo(p):
    """np_quitar_fondo :"""
    # PUNTO 8: se cerró el paréntesis; se quita el fondo falso.
    generador.quitar_fondo_falso()


def p_np_negar(p):
    """np_negar :"""
    # PUNTO 9: menos unario sobre el operando que se acaba de meter.
    generador.negar()


def p_operando_id(p):
    """operando : ID"""
    # PUNTO S7 + PUNTO 1: la variable debe estar declarada (en la función
    # actual o como global). Se mete a PilaO y su tipo a PTipos.
    variable = directorio.buscar_variable(p[1], p.lineno(1))
    generador.meter_operando(variable.nombre, variable.tipo)


def p_operando_cte(p):
    """operando : CTE_INT
                | CTE_FLOAT"""
    # PUNTO 2: una constante se mete tal cual; su tipo sale de su valor.
    generador.meter_operando(p[1], tipo_de_constante(p[1]))


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


class Compilacion:
    """Lo que produce el compilador para un programa."""

    def __init__(self, directorio, generador):
        self.directorio = directorio
        self.generador = generador
        self.cuadruplos = generador.cuadruplos


def analizar(codigo, con_traza=False):
    """
    Compila `codigo` hasta la generación de cuádruplos.

    Regresa una Compilacion con el directorio de funciones y los cuádruplos.
    Con `con_traza=True` el generador guarda además el estado de las pilas
    después de cada acción. Si el programa tiene un error lanza ErrorLexico,
    ErrorSintactico o ErrorSemantico.
    """
    global directorio, generador
    directorio = DirectorioFunciones()
    generador = GeneradorCuadruplos(con_traza)
    _parser.parse(codigo, lexer=construir_lexer())
    return Compilacion(directorio, generador)
