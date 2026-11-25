"""
main.py - Punto de entrada de la entrega 4 (estatutos, funciones y direcciones virtuales).

Uso:
    python main.py programas/factorial.bd            # cuádruplos y tabla de constantes
    python main.py programas/factorial.bd --tablas   # además, el directorio con direcciones
    python main.py programas/factorial.bd --traza    # además, las pilas paso a paso

Cada cuádruplo se muestra dos veces: con direcciones virtuales (lo que de
verdad genera el compilador) y, a la derecha, con nombres (para leerlo).
"""

import sys

from errores import ErrorBabyDuck
from parser import analizar


def main(argumentos):
    if not argumentos:
        print(__doc__)
        return 2

    ruta = argumentos[0]
    with open(ruta, encoding="utf-8") as archivo:
        codigo = archivo.read()

    try:
        compilacion = analizar(codigo, con_traza="--traza" in argumentos)
    except ErrorBabyDuck as error:
        print(f"{ruta}: {error}")
        return 1

    print(f"{ruta}: programa válido")

    if "--tablas" in argumentos:
        print()
        print("DIRECTORIO DE FUNCIONES Y TABLAS DE VARIABLES (con direcciones)")
        print(compilacion.directorio.como_texto())

    if "--traza" in argumentos:
        print()
        print("PILAS PASO A PASO")
        print(compilacion.generador.traza_como_texto())

    print()
    print("TABLA DE CONSTANTES")
    print(compilacion.memoria.tabla_constantes_como_texto() or "  (vacía)")
    print()
    print("FILA DE CUÁDRUPLOS (direcciones | nombres)")
    print(compilacion.generador.como_texto() or "(vacía)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
