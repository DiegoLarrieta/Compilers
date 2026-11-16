"""
main.py - Punto de entrada de la entrega 1 (léxico y sintaxis).

Uso:
    python main.py programas/factorial.bd            # valida el programa
    python main.py programas/factorial.bd --tokens   # además lista los tokens
"""

import sys

from errores import ErrorBabyDuck
from lexer import tokenizar
from parser import analizar


def main(argumentos):
    if not argumentos:
        print(__doc__)
        return 2

    ruta = argumentos[0]
    with open(ruta, encoding="utf-8") as archivo:
        codigo = archivo.read()

    try:
        if "--tokens" in argumentos:
            print(f"{'LÍNEA':<6} {'TOKEN':<12} LEXEMA")
            for tipo, valor, linea in tokenizar(codigo):
                print(f"{linea:<6} {tipo:<12} {valor}")
            print()
        analizar(codigo)
    except ErrorBabyDuck as error:
        print(f"{ruta}: {error}")
        return 1

    print(f"{ruta}: programa válido (léxico y sintaxis correctos)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
