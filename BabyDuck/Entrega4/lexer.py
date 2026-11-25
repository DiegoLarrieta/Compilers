"""
lexer.py - Scanner (analizador léxico) de BabyDuck, hecho con PLY.

PLY arma el scanner a partir de lo que encuentra en este módulo:

  * `tokens`              -> lista con el nombre de todos los tokens.
  * variables `t_NOMBRE`  -> expresión regular de un token sencillo.
  * funciones `t_NOMBRE`  -> expresión regular (en el docstring) + una acción
                             en Python que se ejecuta al reconocer el token.

Las expresiones regulares son las que se diseñaron en la entrega 0.
"""

import sys

import ply.lex as lex

from errores import ErrorLexico

# ---------------------------------------------------------------------------
# Palabras reservadas
# ---------------------------------------------------------------------------
# Una palabra reservada tiene la misma forma que un identificador, así que no
# se le escribe una expresión regular propia: primero se reconoce un ID y luego
# se consulta este diccionario para ver si en realidad es palabra reservada.
palabras_reservadas = {
    "program": "PROGRAM",
    "main": "MAIN",
    "end": "END",
    "var": "VAR",
    "int": "INT",
    "float": "FLOAT",
    "void": "VOID",
    "print": "PRINT",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "do": "DO",
}

# ---------------------------------------------------------------------------
# Lista de tokens (PLY exige que se llame exactamente `tokens`)
# ---------------------------------------------------------------------------
tokens = [
    # Identificadores y constantes
    "ID",
    "CTE_INT",
    "CTE_FLOAT",
    "CTE_STRING",
    # Operadores aritméticos
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    # Operadores relacionales y asignación
    "GT",
    "LT",
    "NE",
    "ASSIGN",
    # Puntuación y agrupadores
    "SEMICOLON",
    "COMMA",
    "COLON",
    "LPAREN",
    "RPAREN",
    "LBRACE",
    "RBRACE",
    "LBRACKET",
    "RBRACKET",
] + list(palabras_reservadas.values())

# ---------------------------------------------------------------------------
# Tokens sencillos: solo necesitan su expresión regular
# ---------------------------------------------------------------------------
# PLY ordena estas reglas de la expresión más larga a la más corta, por eso
# "!=" se prueba antes que "=".
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_NE = r"!="
t_GT = r">"
t_LT = r"<"
t_ASSIGN = r"="
t_SEMICOLON = r";"
t_COMMA = r","
t_COLON = r":"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"

# Espacios, tabuladores y retornos de carro se ignoran (no generan token).
t_ignore = " \t\r"


# ---------------------------------------------------------------------------
# Tokens con acción: las funciones se prueban en el orden en que aparecen
# ---------------------------------------------------------------------------
def t_CTE_FLOAT(t):
    r"\d+\.\d+"
    # Va ANTES que CTE_INT: si no, "3.14" se leería como el entero 3.
    t.value = float(t.value)
    return t


def t_CTE_INT(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_CTE_STRING(t):
    r'"[^"\n]*"'
    # Letrero entre comillas dobles, en una sola línea. Se guarda sin comillas.
    t.value = t.value[1:-1]
    return t


def t_ID(t):
    r"[A-Za-z_][A-Za-z0-9_]*"
    # Si el lexema es palabra reservada se cambia el tipo del token.
    t.type = palabras_reservadas.get(t.value, "ID")
    return t


def t_newline(t):
    r"\n+"
    # No genera token; solo lleva la cuenta de líneas para los mensajes de error.
    t.lexer.lineno += len(t.value)


def t_error(t):
    """PLY llama a esta función cuando ninguna expresión regular coincide."""
    raise ErrorLexico(f"carácter no reconocido '{t.value[0]}'", t.lineno)


# ---------------------------------------------------------------------------
# Funciones de apoyo
# ---------------------------------------------------------------------------
def construir_lexer():
    """Crea un scanner nuevo (con su contador de líneas en 1)."""
    return lex.lex(module=sys.modules[__name__])


def tokenizar(codigo):
    """
    Regresa todos los tokens de `codigo` como una lista de tuplas
    (tipo, valor, línea). Sirve para probar el scanner por separado.
    """
    lexer = construir_lexer()
    lexer.input(codigo)
    return [(tok.type, tok.value, tok.lineno) for tok in lexer]
