"""
cubo_semantico.py - Tabla de consideraciones semánticas (cubo semántico).

El cubo contesta una sola pregunta:

    "Si aplico el OPERADOR a un operando de tipo A y otro de tipo B,
     ¿de qué tipo es el resultado? ¿O es un error?"

Estructura elegida: diccionarios anidados  CUBO[operador][tipo_izq][tipo_der].
  * La consulta es O(1) (tres búsquedas en tablas hash).
  * Se lee casi igual que la tabla del documento, así que es fácil de revisar.
  * Una combinación inválida se guarda explícitamente como ERROR.

Decisiones de diseño de BabyDuck:
  * int (op) int   -> int      (la división entre enteros es entera, como en C)
  * si participa un float en + - * /  -> float
  * los relacionales (> < !=) regresan bool; bool solo existe como resultado
    de una comparación (no se pueden declarar variables bool)
  * asignación: a un float se le puede asignar un int (se promueve), pero a un
    int NO se le puede asignar un float (se perdería información)
"""

INT = "int"
FLOAT = "float"
BOOL = "bool"
ERROR = "error"

TIPOS = (INT, FLOAT, BOOL)

OPERADORES_ARITMETICOS = ("+", "-", "*", "/")
OPERADORES_RELACIONALES = (">", "<", "!=")


def _tabla(int_int, int_float, float_int, float_float):
    """
    Construye la tabla de un operador. Solo se dan las 4 combinaciones entre
    int y float; cualquier combinación donde participe un bool es ERROR.
    """
    tabla = {izq: {der: ERROR for der in TIPOS} for izq in TIPOS}
    tabla[INT][INT] = int_int
    tabla[INT][FLOAT] = int_float
    tabla[FLOAT][INT] = float_int
    tabla[FLOAT][FLOAT] = float_float
    return tabla


CUBO = {}

for _operador in OPERADORES_ARITMETICOS:
    CUBO[_operador] = _tabla(INT, FLOAT, FLOAT, FLOAT)

for _operador in OPERADORES_RELACIONALES:
    CUBO[_operador] = _tabla(BOOL, BOOL, BOOL, BOOL)

# Asignación: el tipo de la IZQUIERDA es el de la variable destino y el de la
# DERECHA es el de la expresión. El resultado es el tipo con el que se guarda.
CUBO["="] = _tabla(INT, ERROR, FLOAT, FLOAT)


def tipo_resultante(operador, tipo_izq, tipo_der):
    """
    Consulta el cubo. Regresa el tipo del resultado o ERROR si la operación
    no está permitida entre esos tipos.
    """
    return CUBO[operador][tipo_izq][tipo_der]


def imprimir_cubo():
    """Muestra el cubo completo como texto (una fila por combinación de tipos)."""
    operadores = list(CUBO)
    print(f"{'izquierdo':<10}{'derecho':<10}" + "".join(f"{op:<7}" for op in operadores))
    for izq in TIPOS:
        for der in TIPOS:
            celdas = "".join(f"{CUBO[op][izq][der]:<7}" for op in operadores)
            print(f"{izq:<10}{der:<10}{celdas}")


if __name__ == "__main__":
    imprimir_cubo()
