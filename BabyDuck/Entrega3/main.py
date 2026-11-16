"""
main.py - Punto de entrada de la entrega 3 (cuádruplos).

Uso:
    python main.py programas/expresiones.bd            # muestra los cuádruplos
    python main.py programas/expresiones.bd --traza    # además, las pilas paso a paso
    python main.py programas/expresiones.bd --tablas   # además, el directorio de funciones
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
        print("DIRECTORIO DE FUNCIONES Y TABLAS DE VARIABLES")
        print(compilacion.directorio.como_texto())

    if "--traza" in argumentos:
        print()
        print("PILAS PASO A PASO")
        print(compilacion.generador.traza_como_texto())

    print()
    print("FILA DE CUÁDRUPLOS")
    print(compilacion.generador.como_texto() or "(vacía)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
