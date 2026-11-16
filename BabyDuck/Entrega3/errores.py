"""
errores.py - Excepciones del compilador de BabyDuck.

Cada fase del compilador lanza su propio tipo de error. Todas guardan el número
de línea para que el mensaje le diga al programador dónde está el problema.
"""


class ErrorBabyDuck(Exception):
    """Clase base de todos los errores que reporta el compilador."""

    fase = "Error"

    def __init__(self, mensaje, linea=None):
        self.mensaje = mensaje
        self.linea = linea
        donde = f" (línea {linea})" if linea is not None else ""
        super().__init__(f"{self.fase}{donde}: {mensaje}")


class ErrorLexico(ErrorBabyDuck):
    """El scanner encontró un carácter que no pertenece al lenguaje."""

    fase = "Error léxico"


class ErrorSintactico(ErrorBabyDuck):
    """El parser encontró un token que no esperaba según la gramática."""

    fase = "Error de sintaxis"


class ErrorSemantico(ErrorBabyDuck):
    """El programa está bien escrito pero no tiene sentido (p. ej. variable repetida)."""

    fase = "Error semántico"
