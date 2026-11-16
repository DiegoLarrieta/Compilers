"""
parser.py - Parser (analizador sintáctico) de BabyDuck, hecho con PLY (yacc).

PLY genera un parser LALR(1) a partir de las funciones `p_*` de este módulo.
Cada función lleva en su docstring una o varias reglas gramaticales en formato
BNF:

    no_terminal : simbolo simbolo ...
                | otra alternativa

Los nombres en MAYÚSCULAS son tokens (vienen de lexer.py) y los nombres en
minúsculas son no terminales. La gramática es la de la entrega 0.

En esta entrega el parser solo VALIDA la sintaxis: las funciones no hacen nada
más (`pass`). En las siguientes entregas se les agregan acciones semánticas.
"""

import ply.yacc as yacc

from errores import ErrorSintactico
from lexer import construir_lexer, tokens  # noqa: F401  (PLY necesita `tokens`)

# Símbolo inicial de la gramática.
start = "programa"


# ---------------------------------------------------------------------------
# Programa
# ---------------------------------------------------------------------------
def p_programa(p):
    """programa : PROGRAM ID SEMICOLON vars_opt funcs MAIN body END"""


# ---------------------------------------------------------------------------
# Declaración de variables
# ---------------------------------------------------------------------------
def p_vars(p):
    """vars_opt   : VAR lista_decl
                  | empty
    lista_decl : decl lista_decl
               | decl
    decl       : lista_ids COLON tipo SEMICOLON
    lista_ids  : ID COMMA lista_ids
               | ID
    tipo       : INT
               | FLOAT"""


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------
def p_funcs(p):
    """funcs        : func funcs
                    | empty
    func         : VOID ID LPAREN params_opt RPAREN LBRACKET vars_opt body RBRACKET SEMICOLON
    params_opt   : lista_params
                 | empty
    lista_params : param COMMA lista_params
                 | param
    param        : ID COLON tipo"""


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
    """asigna : ID ASSIGN expresion SEMICOLON"""


def p_condicion(p):
    """condicion : IF LPAREN expresion RPAREN body else_opt SEMICOLON
    else_opt  : ELSE body
              | empty"""


def p_ciclo(p):
    """ciclo : WHILE LPAREN expresion RPAREN DO body SEMICOLON"""


def p_llamada(p):
    """llamada    : ID LPAREN args_opt RPAREN SEMICOLON
    args_opt   : lista_args
               | empty
    lista_args : expresion COMMA lista_args
               | expresion"""


def p_imprime(p):
    """imprime     : PRINT LPAREN lista_print RPAREN SEMICOLON
    lista_print : item_print COMMA lista_print
                | item_print
    item_print  : expresion
                | CTE_STRING"""


# ---------------------------------------------------------------------------
# Expresiones
# ---------------------------------------------------------------------------
# La precedencia de operadores queda dada por los niveles de la gramática:
#   expresion (relacionales) -> exp (+ -) -> termino (* /) -> factor
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
    """factor   : LPAREN expresion RPAREN
                | PLUS operando
                | MINUS operando
                | operando
    operando : ID
             | cte
    cte      : CTE_INT
             | CTE_FLOAT"""


# ---------------------------------------------------------------------------
# Producción vacía y manejo de errores
# ---------------------------------------------------------------------------
def p_empty(p):
    """empty :"""


def p_error(tok):
    """PLY llama a esta función cuando el token leído no encaja en la gramática."""
    if tok is None:
        raise ErrorSintactico("el programa terminó antes de lo esperado (¿falta 'end'?)")
    raise ErrorSintactico(f"no se esperaba '{tok.value}' (token {tok.type})", tok.lineno)


# El parser se construye una sola vez al importar el módulo. Con estas opciones
# PLY no deja archivos generados (parser.out / parsetab.py) en la carpeta.
_parser = yacc.yacc(debug=False, write_tables=False)


def analizar(codigo):
    """
    Revisa que `codigo` sea un programa BabyDuck bien escrito.

    Regresa True si lo es. Si no, lanza ErrorLexico o ErrorSintactico con la
    línea donde se encontró el problema.
    """
    _parser.parse(codigo, lexer=construir_lexer())
    return True
