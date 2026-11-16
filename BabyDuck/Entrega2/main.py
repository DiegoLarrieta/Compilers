"""
main.py - Punto de entrada de la entrega 2 (semántica de variables).

Uso:
    python main.py programas/factorial.bd     # compila y muestra el directorio
    python main.py --cubo                     # muestra el cubo semántico
"""

import sys

from cubo_semantico import imprimir_cubo
from errores import ErrorBabyDuck
from parser import analizar


def main(argumentos):
    if not argumentos:
        print(__doc__)
        return 2

    if argumentos[0] == "--cubo":
        imprimir_cubo()
        return 0

    ruta = argumentos[0]
    with open(ruta, encoding="utf-8") as archivo:
        codigo = archivo.read()

    try:
        directorio = analizar(codigo)
    except ErrorBabyDuck as error:
        print(f"{ruta}: {error}")
        return 1

    print(f"{ruta}: programa válido")
    print()
    print("DIRECTORIO DE FUNCIONES Y TABLAS DE VARIABLES")
    print(directorio.como_texto())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
